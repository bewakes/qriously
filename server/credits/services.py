from django.db import transaction

from .errors import InsufficientCredits
from .models import CreditEntry, EntryType, Reason, Wallet

UPDATE_FIELDS = [
    "balance",
    "lifetime_granted",
    "lifetime_spent",
    "version",
    "updated_at",
]


def provision_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def get_wallet(user):
    return Wallet.objects.get(user=user)


def _existing(idempotency_key):
    if not idempotency_key:
        return None
    return CreditEntry.objects.filter(idempotency_key=idempotency_key).first()


@transaction.atomic
def grant(wallet, amount, reason, idempotency_key=None, metadata=None, request=None):
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
def spend(wallet, amount, reason, idempotency_key=None, metadata=None, request=None):
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
    wallet,
    amount,
    reason=Reason.FAILED_GENERATION,
    idempotency_key=None,
    metadata=None,
    request=None,
):
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
