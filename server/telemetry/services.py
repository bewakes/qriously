from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from core.constants import MODEL_PRICE

from .models import RequestLog
from .policies import vendor_cost_micros

if TYPE_CHECKING:
    from accounts.models import User
    from credits.models import Wallet


def start_request(
    *,
    user: User,
    wallet: Wallet,
    endpoint: str,
    kind: str = "",
    lens_bucket: str = "",
    idempotency_key: str | None = None,
) -> RequestLog:
    return RequestLog.objects.create(
        user=user,
        wallet=wallet,
        endpoint=endpoint,
        kind=kind,
        lens_bucket=lens_bucket,
        idempotency_key=idempotency_key,
    )


def resolve_vendor_cost(
    model: str, tokens_in: int | None, tokens_out: int | None
) -> int | None:
    price = MODEL_PRICE.get(model)
    if price is None:
        return None
    return vendor_cost_micros(
        tokens_in,
        tokens_out,
        price["input_per_1k_micros"],
        price["output_per_1k_micros"],
    )


def finish_request(
    request_log: RequestLog,
    *,
    status: str,
    credits_charged: int = 0,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    vendor_cost_micros_value: int | None = None,
    latency_ms: int | None = None,
    error_code: str | None = None,
) -> RequestLog:
    request_log.status = status
    request_log.credits_charged = credits_charged
    request_log.tokens_in = tokens_in
    request_log.tokens_out = tokens_out
    request_log.vendor_cost_micros = vendor_cost_micros_value
    request_log.latency_ms = latency_ms
    request_log.error_code = error_code
    request_log.completed_at = timezone.now()
    request_log.save()
    return request_log
