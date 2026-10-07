from django.utils import timezone

from .models import ModelPrice, RequestLog, RequestStatus
from .policies import vendor_cost_micros


def start_request(
    *,
    user,
    wallet,
    endpoint,
    method="POST",
    kind="",
    lens_bucket="",
    idempotency_key=None,
    client_fingerprint=None,
):
    return RequestLog.objects.create(
        user=user,
        wallet=wallet,
        endpoint=endpoint,
        method=method,
        kind=kind,
        lens_bucket=lens_bucket,
        idempotency_key=idempotency_key,
        client_fingerprint=client_fingerprint,
    )


def record_screening(
    request_log,
    *,
    status,
    category=None,
    score=None,
    provider=None,
):
    request_log.screening_status = status
    request_log.screening_category = category
    request_log.screening_score = score
    request_log.screening_provider = provider
    request_log.save(
        update_fields=[
            "screening_status",
            "screening_category",
            "screening_score",
            "screening_provider",
        ]
    )
    return request_log


def price_for(model, version=None):
    queryset = ModelPrice.objects.filter(model=model)
    if version:
        queryset = queryset.filter(version=version)
    return queryset.order_by("-effective_at").first()


def resolve_vendor_cost(model, tokens_in, tokens_out, version=None):
    price = price_for(model, version)
    if price is None:
        return None, None
    cost = vendor_cost_micros(
        tokens_in,
        tokens_out,
        price.input_per_1k_micros,
        price.output_per_1k_micros,
    )
    return cost, price.version


def finish_request(
    request_log,
    *,
    status,
    credits_charged=0,
    tokens_in=None,
    tokens_out=None,
    vendor_cost_micros_value=None,
    price_version=None,
    latency_ms=None,
    cache_hit=None,
    lookup_layer=None,
    error_code=None,
):
    request_log.status = status
    request_log.credits_charged = credits_charged
    request_log.tokens_in = tokens_in
    request_log.tokens_out = tokens_out
    request_log.vendor_cost_micros = vendor_cost_micros_value
    request_log.price_version = price_version
    request_log.latency_ms = latency_ms
    if cache_hit is not None:
        request_log.cache_hit = cache_hit
    if lookup_layer is not None:
        request_log.lookup_layer = lookup_layer
    request_log.error_code = error_code
    request_log.completed_at = timezone.now()
    request_log.save()
    return request_log


def mark_denied(request_log, error_code="insufficient_credits"):
    return finish_request(
        request_log, status=RequestStatus.DENIED, error_code=error_code
    )


def mark_blocked(request_log, error_code="content_blocked"):
    return finish_request(
        request_log, status=RequestStatus.BLOCKED, error_code=error_code
    )
