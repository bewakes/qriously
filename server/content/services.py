from __future__ import annotations

from collections.abc import Mapping

from django.db import IntegrityError, transaction

from core.constants import DEFAULT_MODEL, PROMPT_VERSION
from core.constants import lens_bucket as make_lens_bucket
from core.constants import lens_vector as make_lens_vector

from .models import Concept, ConceptLink, ContentVariant
from .reuse import LookupResult, find_variant
from .text import context_fingerprint, estimate_read_seconds, normalize


@transaction.atomic
def upsert_concept(text: str, kind_hint: str | None = None) -> Concept:
    key = normalize(text)
    if not key:
        raise ValueError("cannot upsert a concept from empty text")
    concept, _ = Concept.objects.get_or_create(
        key=key,
        defaults={"text": (text or "").strip(), "kind_hint": kind_hint},
    )
    return concept


def _lookup_fields(
    *,
    concept: Concept,
    kind: str,
    lens: Mapping[str, str] | None,
    context_key: str,
    prompt_version: str,
) -> dict[str, object]:
    return {
        "concept": concept,
        "kind": kind,
        "lens_bucket": make_lens_bucket(lens),
        "context_fingerprint": context_fingerprint(context_key),
        "prompt_version": prompt_version,
    }


@transaction.atomic
def create_variant(
    *,
    concept: Concept,
    kind: str,
    lens: Mapping[str, str] | None,
    title: str,
    body: str,
    context_key: str = "",
    prompt_version: str = PROMPT_VERSION,
    model: str = DEFAULT_MODEL,
    citations: list[dict] | None = None,
) -> ContentVariant:
    return ContentVariant.objects.create(
        **_lookup_fields(
            concept=concept,
            kind=kind,
            lens=lens,
            context_key=context_key,
            prompt_version=prompt_version,
        ),
        lens_vector=make_lens_vector(lens),
        title=title,
        body=body,
        citations=citations or [],
        est_read_seconds=estimate_read_seconds(body),
        model=model,
    )


@transaction.atomic
def get_or_create_variant(
    *,
    concept: Concept,
    kind: str,
    lens: Mapping[str, str] | None,
    title: str,
    body: str,
    context_key: str = "",
    prompt_version: str = PROMPT_VERSION,
    model: str = DEFAULT_MODEL,
    citations: list[dict] | None = None,
) -> tuple[ContentVariant, bool]:
    lookup = _lookup_fields(
        concept=concept,
        kind=kind,
        lens=lens,
        context_key=context_key,
        prompt_version=prompt_version,
    )
    existing = ContentVariant.objects.filter(**lookup).first()
    if existing is not None:
        return existing, False
    try:
        with transaction.atomic():
            variant = ContentVariant.objects.create(
                **lookup,
                lens_vector=make_lens_vector(lens),
                title=title,
                body=body,
                citations=citations or [],
                est_read_seconds=estimate_read_seconds(body),
                model=model,
            )
    except IntegrityError:
        return ContentVariant.objects.get(**lookup), False
    return variant, True


@transaction.atomic
def record_concept_link(
    parent: Concept, child: Concept, kind: str
) -> ConceptLink:
    link, created = ConceptLink.objects.get_or_create(
        parent=parent, child=child, kind=kind
    )
    if not created:
        link.weight += 1
        link.save(update_fields=["weight", "updated_at"])
    return link


@transaction.atomic
def resolve_variant(
    *,
    text: str,
    kind: str,
    lens: Mapping[str, str] | None,
    context_key: str = "",
    prompt_version: str = PROMPT_VERSION,
    kind_hint: str | None = None,
) -> tuple[Concept, LookupResult]:
    concept = upsert_concept(text, kind_hint=kind_hint)
    result = find_variant(
        concept=concept,
        kind=kind,
        lens_bucket=make_lens_bucket(lens),
        context_fingerprint=context_fingerprint(context_key),
        prompt_version=prompt_version,
    )
    return concept, result
