import pytest
from django.contrib.auth import get_user_model

from content.models import LookupLayer
from credits.models import Reason
from credits.services import get_wallet, record_generation
from telemetry.services import start_request

User = get_user_model()


@pytest.fixture
def context(db):
    user = User.objects.create_user()
    wallet = get_wallet(user)
    request = start_request(
        user=user, wallet=wallet, endpoint="generate", kind="dive"
    )
    return wallet, request


def test_cache_miss_charges_full_price_and_records_vendor_cost(context):
    wallet, request = context

    event = record_generation(
        wallet=wallet,
        request=request,
        kind="dive",
        depth="solid",
        cache_hit=False,
        model="deepseek-flash",
        tokens_in=1000,
        tokens_out=1000,
        lookup_layer=LookupLayer.GENERATED,
    )

    assert event.cost == 12
    assert event.cache_hit is False
    assert event.vendor_cost_micros == 420
    assert event.tokens_in == 1000
    wallet.refresh_from_db()
    assert wallet.balance == 5000 - 12
    entry = wallet.entries.get()
    assert entry.reason == Reason.GENERATION
    assert entry.delta == -12


def test_cache_hit_charges_a_fraction_and_has_no_vendor_cost(context):
    wallet, request = context

    event = record_generation(
        wallet=wallet,
        request=request,
        kind="dive",
        depth="solid",
        cache_hit=True,
        lookup_layer=LookupLayer.EXACT,
    )

    assert event.cost == 3
    assert event.cache_hit is True
    assert event.vendor_cost_micros is None
    assert event.tokens_in is None
    wallet.refresh_from_db()
    assert wallet.balance == 5000 - 3
    assert wallet.entries.get().reason == Reason.CACHE_REUSE
