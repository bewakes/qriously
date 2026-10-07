from django.conf import settings
from django.db import models

from core.models import TimeStampedModel, UUIDModel


class EntryType(models.TextChoices):
    GRANT = "grant"
    DEBIT = "debit"
    REFUND = "refund"
    ADJUST = "adjust"
    EXPIRE = "expire"


class Reason(models.TextChoices):
    SIGNUP_GRANT = "signup_grant"
    GENERATION = "generation"
    CACHE_REUSE = "cache_reuse"
    FAILED_GENERATION = "failed_generation"
    PLAN_REFILL = "plan_refill"
    PURCHASE = "purchase"
    MANUAL = "manual"


class Wallet(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.BigIntegerField(default=0)
    lifetime_granted = models.BigIntegerField(default=0)
    lifetime_spent = models.BigIntegerField(default=0)
    version = models.IntegerField(default=0)

    class Meta:
        db_table = "credits_wallet"

    def __str__(self):
        return f"wallet({self.user}) = {self.balance}"

    def apply_grant(self, amount):
        self.balance += amount
        self.lifetime_granted += amount
        self.version += 1

    def apply_debit(self, amount):
        self.balance -= amount
        self.lifetime_spent += amount
        self.version += 1

    def apply_refund(self, amount):
        self.balance += amount
        self.lifetime_spent = max(0, self.lifetime_spent - amount)
        self.version += 1


class CreditEntry(UUIDModel):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="entries"
    )
    delta = models.BigIntegerField()
    balance_after = models.BigIntegerField()
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    reason = models.CharField(max_length=32, choices=Reason.choices)
    idempotency_key = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )
    request = models.ForeignKey(
        "telemetry.RequestLog",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="credit_entries",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credits_credit_entry"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["wallet", "-created_at"])]

    def __str__(self):
        return f"{self.entry_type} {self.delta:+d} -> {self.balance_after}"
