import pytest
from django.contrib.auth import get_user_model

from credits.models import Reason
from credits.services import get_wallet, spend
from telemetry.models import RequestStatus, ScreeningStatus
from telemetry.services import (
    finish_request,
    record_screening,
    resolve_vendor_cost,
    start_request,
)

User = get_user_model()


def make_user():
    return User.objects.create_user()


@pytest.mark.django_db
def test_request_lifecycle():
    user = make_user()
    wallet = get_wallet(user)

    request = start_request(
        user=user, wallet=wallet, endpoint="nodes.create", kind="dive"
    )
    assert request.status == RequestStatus.PENDING

    record_screening(request, status=ScreeningStatus.ALLOW, provider="allow_all")
    request.refresh_from_db()
    assert request.screening_status == ScreeningStatus.ALLOW

    finish_request(
        request,
        status=RequestStatus.SUCCEEDED,
        credits_charged=120,
        tokens_in=812,
        tokens_out=337,
        vendor_cost_micros_value=1840,
        price_version="v1",
        latency_ms=2410,
        cache_hit=False,
        lookup_layer="generated",
    )
    request.refresh_from_db()
    assert request.status == RequestStatus.SUCCEEDED
    assert request.credits_charged == 120
    assert request.completed_at is not None


@pytest.mark.django_db
def test_resolve_vendor_cost_uses_seeded_price():
    cost, version = resolve_vendor_cost("deepseek-flash", 1000, 1000)
    assert (cost, version) == (420, "v1")


@pytest.mark.django_db
def test_resolve_vendor_cost_unknown_model():
    assert resolve_vendor_cost("nope", 1000, 1000) == (None, None)


@pytest.mark.django_db
def test_credit_entry_links_to_request():
    user = make_user()
    wallet = get_wallet(user)
    request = start_request(user=user, wallet=wallet, endpoint="nodes.create")

    entry = spend(wallet, 100, Reason.GENERATION, request=request)

    assert entry.request_id == request.id
    assert list(request.credit_entries.all()) == [entry]
