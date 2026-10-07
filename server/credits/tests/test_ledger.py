import pytest
from django.contrib.auth import get_user_model

from credits.errors import InsufficientCredits
from credits.models import EntryType, Reason
from credits.services import get_wallet, grant, refund, spend

User = get_user_model()


def make_wallet():
    return get_wallet(User.objects.create_user())


@pytest.mark.django_db
def test_signup_grants_wallet():
    wallet = make_wallet()
    assert wallet.balance == 5000
    assert wallet.lifetime_granted == 5000
    entry = wallet.entries.get()
    assert entry.entry_type == EntryType.GRANT
    assert entry.reason == Reason.SIGNUP_GRANT


@pytest.mark.django_db
def test_spend_deducts_and_records():
    wallet = make_wallet()
    entry = spend(wallet, 120, Reason.GENERATION)
    assert entry.delta == -120
    assert entry.balance_after == 4880
    wallet.refresh_from_db()
    assert wallet.balance == 4880
    assert wallet.lifetime_spent == 120


@pytest.mark.django_db
def test_spend_insufficient_raises_and_writes_nothing():
    wallet = make_wallet()
    with pytest.raises(InsufficientCredits):
        spend(wallet, 999999, Reason.GENERATION)
    wallet.refresh_from_db()
    assert wallet.balance == 5000
    assert wallet.entries.count() == 1


@pytest.mark.django_db
def test_idempotent_spend_not_double_charged():
    wallet = make_wallet()
    first = spend(wallet, 100, Reason.GENERATION, idempotency_key="k1")
    second = spend(wallet, 100, Reason.GENERATION, idempotency_key="k1")
    assert first.id == second.id
    wallet.refresh_from_db()
    assert wallet.balance == 4900


@pytest.mark.django_db
def test_refund_restores_balance():
    wallet = make_wallet()
    spend(wallet, 100, Reason.GENERATION)
    refund(wallet, 100)
    wallet.refresh_from_db()
    assert wallet.balance == 5000
    assert wallet.lifetime_spent == 0


@pytest.mark.django_db
def test_grant_idempotent():
    wallet = make_wallet()
    grant(wallet, 1000, Reason.PURCHASE, idempotency_key="p1")
    grant(wallet, 1000, Reason.PURCHASE, idempotency_key="p1")
    wallet.refresh_from_db()
    assert wallet.balance == 6000
