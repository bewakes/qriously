from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from content.models import LookupLayer
from core.constants import DEFAULT_MODEL
from telemetry.services import resolve_vendor_cost

from .errors import InsufficientCredits
from .models import CreditEntry, EntryType, Reason, UsageEvent, Wallet
from .policies import price as compute_price

if TYPE_CHECKING:
    from accounts.models import User
    from content.models import ContentVariant
    from learning.models import Node, Thread
    from telemetry.models import RequestLog

UPDATE_FIELDS = [
    "balance",
    "lifetime_granted",
    "lifetime_spent",
    "version",
    "updated_at",
]


def provision_wallet(user: User) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def get_wallet(user: User) -> Wallet:
    return Wallet.objects.get(user=user)


def _existing(idempotency_key: str | None) -> CreditEntry | None:
    if not idempotency_key:
        return None
    return CreditEntry.objects.filter(idempotency_key=idempotency_key).first()


@transaction.atomic
def grant(
    wallet: Wallet,
    amount: int,
    reason: str,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
    request: RequestLog | None = None,
) -> CreditEntry:
    if amount <= 0:
        raise ValueError("grant amount must be positive")
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
    existing = _existing(idempotency_key)
    if existing:
        return existing
    wallet.apply_grant(amount)
    wallet.save(update_fields=UPDATE_FIELDS)
    return CreditEntry.objects.create(
        wallet=wallet,
        delta=amount,
        balance_after=wallet.balance,
        entry_type=EntryType.GRANT,
        reason=reason,
        idempotency_key=idempotency_key,
        request=request,
        metadata=metadata or {},
    )


@transaction.atomic
def spend(
    wallet: Wallet,
    amount: int,
    reason: str,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
    request: RequestLog | None = None,
) -> CreditEntry:
    if amount < 0:
        raise ValueError("spend amount must not be negative")
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
    existing = _existing(idempotency_key)
    if existing:
        return existing
    if wallet.balance < amount:
        raise InsufficientCredits(required=amount, balance=wallet.balance)
    wallet.apply_debit(amount)
    wallet.save(update_fields=UPDATE_FIELDS)
    return CreditEntry.objects.create(
        wallet=wallet,
        delta=-amount,
        balance_after=wallet.balance,
        entry_type=EntryType.DEBIT,
        reason=reason,
        idempotency_key=idempotency_key,
        request=request,
        metadata=metadata or {},
    )


@transaction.atomic
def refund(
    wallet: Wallet,
    amount: int,
    reason: str = Reason.FAILED_GENERATION,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
    request: RequestLog | None = None,
) -> CreditEntry:
    if amount <= 0:
        raise ValueError("refund amount must be positive")
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
    existing = _existing(idempotency_key)
    if existing:
        return existing
    wallet.apply_refund(amount)
    wallet.save(update_fields=UPDATE_FIELDS)
    return CreditEntry.objects.create(
        wallet=wallet,
        delta=amount,
        balance_after=wallet.balance,
        entry_type=EntryType.REFUND,
        reason=reason,
        idempotency_key=idempotency_key,
        request=request,
        metadata=metadata or {},
    )


@transaction.atomic
def record_generation(
    *,
    wallet: Wallet,
    request: RequestLog,
    kind: str,
    depth: str,
    cache_hit: bool,
    thread: Thread | None = None,
    node: Node | None = None,
    content_variant: ContentVariant | None = None,
    lens_bucket: str = "",
    lookup_layer: str = LookupLayer.GENERATED,
    model: str = DEFAULT_MODEL,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    latency_ms: int | None = None,
) -> UsageEvent:
    """Price a generation, debit the wallet and record the usage event.

    Charges ``price(kind, depth, cache_hit)`` — a cache hit is a fraction, never
    free — and records the vendor cost separately (``None`` on a cache hit,
    when no LLM call happens). Returns the created UsageEvent.
    """
    cost = compute_price(kind, depth, cache_hit)
    reason = Reason.CACHE_REUSE if cache_hit else Reason.GENERATION
    spend(
        wallet,
        cost,
        reason,
        idempotency_key=f"generation:{request.id}",
        request=request,
        metadata={"kind": kind, "depth": depth, "cache_hit": cache_hit},
    )
    if cache_hit:
        tokens_in = None
        tokens_out = None
        vendor_cost = None
    else:
        vendor_cost = resolve_vendor_cost(model, tokens_in, tokens_out)
    return UsageEvent.objects.create(
        wallet=wallet,
        request=request,
        thread=thread,
        node=node,
        content_variant=content_variant,
        kind=kind,
        lens_bucket=lens_bucket,
        cache_hit=cache_hit,
        lookup_layer=lookup_layer,
        cost=cost,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        vendor_cost_micros=vendor_cost,
        latency_ms=latency_ms,
        model=model,
    )
