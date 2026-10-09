from __future__ import annotations

import time
from collections.abc import AsyncIterator, Mapping
from typing import TYPE_CHECKING
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from content.models import ContentVariant
from content.reuse import find_variant
from content.services import get_or_create_variant, upsert_concept
from content.text import context_fingerprint
from core.constants import DEFAULT_MODEL, PROMPT_VERSION, normalize_lens
from core.constants import lens_bucket as make_lens_bucket
from credits.errors import InsufficientCredits
from credits.policies import price
from credits.services import get_wallet, record_generation
from learning.models import Node, NodeStatus, Span, Thread
from learning.services import create_node
from safety.registry import get_policy
from telemetry.services import finish_request, start_request

from .errors import ContentBlocked
from .llm import LLMClient, LLMError, get_client
from .models import GenerationJob, JobStatus
from .prompts import build_messages

if TYPE_CHECKING:
    from accounts.models import User

StreamEvent = tuple[str, dict]


@transaction.atomic
def prepare_generation(
    *,
    user: User,
    thread: Thread,
    kind: str,
    parent: Node | None = None,
    span_text: str | None = None,
    question: str | None = None,
    lens: Mapping[str, str] | None = None,
    idempotency_key: str | None = None,
) -> GenerationJob:
    """Open a request, resolve the concept, look the cache up and price the job.

    Returns a queued GenerationJob. Raises ContentBlocked before any spend if
    screening denies the query, and InsufficientCredits if the wallet cannot
    cover the price. Replaying the same idempotency key returns the original job
    without opening a second request or spend.
    """
    if idempotency_key:
        existing = GenerationJob.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing is not None:
            return existing

    wallet = get_wallet(user)
    effective_lens = normalize_lens(lens if lens is not None else thread.lens)
    text = (question or span_text or "").strip()

    decision = get_policy().check(text)
    if not decision.allowed:
        raise ContentBlocked(decision.category or "unsafe")

    concept = upsert_concept(text)
    parent_concept_key = _parent_concept_key(parent)
    fingerprint = context_fingerprint(parent_concept_key)
    bucket = make_lens_bucket(effective_lens)

    result = find_variant(
        concept=concept,
        kind=kind,
        lens_bucket=bucket,
        context_fingerprint=fingerprint,
        prompt_version=PROMPT_VERSION,
    )
    cache_hit = result.hit
    cost = price(kind, effective_lens["depth"], cache_hit)
    if wallet.balance < cost:
        raise InsufficientCredits(required=cost, balance=wallet.balance)

    request_log = start_request(
        user=user,
        wallet=wallet,
        endpoint="generate",
        kind=kind,
        lens_bucket=bucket,
        idempotency_key=idempotency_key,
    )
    span = None
    if parent is not None and span_text:
        span = Span.objects.create(
            thread=thread, source_node=parent, text=span_text, concept=concept
        )
    node = create_node(
        thread,
        kind,
        parent=parent,
        span=span,
        anchor_text=span_text or "",
        title=concept.text,
        lens=effective_lens,
        status=NodeStatus.QUEUED,
    )
    messages = build_messages(
        text=text,
        kind=kind,
        lens=effective_lens,
        context=parent.title if parent is not None else None,
    )
    return GenerationJob.objects.create(
        request=request_log,
        wallet=wallet,
        thread=thread,
        node=node,
        concept=concept,
        kind=kind,
        lens_bucket=bucket,
        context_fingerprint=fingerprint,
        prompt_version=PROMPT_VERSION,
        model=DEFAULT_MODEL,
        idempotency_key=idempotency_key or uuid4().hex,
        messages=messages,
        lens=dict(effective_lens),
        cost=cost,
        cache_hit=cache_hit,
        lookup_layer=result.layer,
    )


async def stream_generation(
    job: GenerationJob, *, llm: LLMClient | None = None
) -> AsyncIterator[StreamEvent]:
    """Run a prepared job, yielding meta/token/done/usage (or error) events."""
    client = llm or get_client()
    started = time.monotonic()
    yield (
        "meta",
        {
            "request_id": str(job.request_id),
            "node_id": str(job.node_id),
            "concept": {"id": str(job.concept_id), "text": job.concept.text},
            "kind": job.kind,
            "lens_bucket": job.lens_bucket,
            "cache_hit": job.cache_hit,
            "cost": job.cost,
            "balance": job.wallet.balance,
        },
    )

    if job.cache_hit:
        variant = await sync_to_async(_load_hit_variant)(job)
        yield ("token", {"text": variant.body})
        payload = await sync_to_async(_finalize)(
            job,
            body=variant.body,
            variant=variant,
            cache_hit=True,
            tokens_in=None,
            tokens_out=None,
            latency_ms=_elapsed_ms(started),
        )
        yield ("done", payload["done"])
        yield ("usage", payload["usage"])
        return

    text = ""
    tokens_in: int | None = None
    tokens_out: int | None = None
    try:
        async for chunk in client.stream(job.messages, model=job.model):
            if chunk.text:
                text += chunk.text
                yield ("token", {"text": chunk.text})
            if chunk.tokens_in is not None:
                tokens_in = chunk.tokens_in
            if chunk.tokens_out is not None:
                tokens_out = chunk.tokens_out
    except LLMError as exc:
        await sync_to_async(_fail)(job, code=exc.code, message=exc.message)
        yield (
            "error",
            {"code": exc.code, "message": exc.message, "retryable": exc.retryable},
        )
        return

    payload = await sync_to_async(_finalize)(
        job,
        body=text,
        variant=None,
        cache_hit=False,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=_elapsed_ms(started),
    )
    yield ("done", payload["done"])
    yield ("usage", payload["usage"])


def job_descriptor(job: GenerationJob) -> dict[str, object]:
    """The JSON shape returned by ``POST /generate`` (see docs/API.md §4)."""
    return {
        "request_id": str(job.request_id),
        "job_id": str(job.id),
        "node_id": str(job.node_id),
        "cache_hit": job.cache_hit,
        "lookup_layer": job.lookup_layer,
        "cost": job.cost,
        "balance": job.wallet.balance,
        "stream_url": f"/api/v1/generate/{job.id}/stream",
    }


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _parent_concept_key(parent: Node | None) -> str:
    if parent is not None and parent.content_variant_id:
        return parent.content_variant.concept.key
    return ""


def _load_hit_variant(job: GenerationJob) -> ContentVariant | None:
    return ContentVariant.objects.filter(
        concept=job.concept,
        kind=job.kind,
        lens_bucket=job.lens_bucket,
        context_fingerprint=job.context_fingerprint,
        prompt_version=job.prompt_version,
    ).first()


def _finalize(
    job: GenerationJob,
    *,
    body: str,
    variant: ContentVariant | None,
    cache_hit: bool,
    tokens_in: int | None,
    tokens_out: int | None,
    latency_ms: int,
) -> dict:
    node = job.node
    if variant is None:
        variant, _ = get_or_create_variant(
            concept=job.concept,
            kind=job.kind,
            lens=job.lens,
            title=job.concept.text,
            body=body,
            context_key=_parent_concept_key(node.parent),
            prompt_version=job.prompt_version,
            model=job.model,
        )
    node.content_variant = variant
    node.status = NodeStatus.DONE
    node.reused = cache_hit
    node.title = variant.title or node.title
    node.save(
        update_fields=[
            "content_variant",
            "status",
            "reused",
            "title",
            "updated_at",
        ]
    )

    event = record_generation(
        wallet=job.wallet,
        request=job.request,
        kind=job.kind,
        depth=job.lens.get("depth", "solid"),
        cache_hit=cache_hit,
        thread=job.thread,
        node=node,
        content_variant=variant,
        lens_bucket=job.lens_bucket,
        lookup_layer=job.lookup_layer,
        model=job.model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
    )
    finish_request(
        job.request,
        status="succeeded",
        credits_charged=event.cost,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        vendor_cost_micros_value=event.vendor_cost_micros,
        latency_ms=latency_ms,
    )
    job.status = JobStatus.DONE
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])

    job.wallet.refresh_from_db()
    done = {
        "node_id": str(node.id),
        "content_variant_id": str(variant.id),
        "title": variant.title,
        "est_read_seconds": variant.est_read_seconds,
    }
    usage = {
        "request_id": str(job.request_id),
        "credits_charged": event.cost,
        "balance": job.wallet.balance,
        "cache_hit": cache_hit,
        "lookup_layer": job.lookup_layer,
        "tokens_in": event.tokens_in,
        "tokens_out": event.tokens_out,
        "vendor_cost_micros": event.vendor_cost_micros,
        "latency_ms": latency_ms,
    }
    return {"done": done, "usage": usage}


def _fail(job: GenerationJob, *, code: str, message: str) -> None:
    if job.node is not None:
        job.node.status = NodeStatus.ERROR
        job.node.save(update_fields=["status", "updated_at"])
    job.status = JobStatus.ERROR
    job.error_code = code
    job.error_message = message
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "error_code", "error_message", "completed_at"])
    finish_request(job.request, status="failed", error_code=code)
