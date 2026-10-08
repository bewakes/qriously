from django.conf import settings
from django.db import models

from content.models import LookupLayer
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

    def __str__(self) -> str:
        return f"wallet({self.user}) = {self.balance}"

    def apply_grant(self, amount: int) -> None:
        self.balance += amount
        self.lifetime_granted += amount
        self.version += 1

    def apply_debit(self, amount: int) -> None:
        self.balance -= amount
        self.lifetime_spent += amount
        self.version += 1

    def apply_refund(self, amount: int) -> None:
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

    def __str__(self) -> str:
        return f"{self.entry_type} {self.delta:+d} -> {self.balance_after}"


class UsageEvent(UUIDModel):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="usage_events"
    )
    request = models.ForeignKey(
        "telemetry.RequestLog",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usage_events",
    )
    thread = models.ForeignKey(
        "learning.Thread",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usage_events",
    )
    node = models.ForeignKey(
        "learning.Node",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usage_events",
    )
    content_variant = models.ForeignKey(
        "content.ContentVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usage_events",
    )
    kind = models.CharField(max_length=16, blank=True)
    lens_bucket = models.CharField(max_length=64, blank=True)
    cache_hit = models.BooleanField(default=False)
    lookup_layer = models.CharField(
        max_length=16, choices=LookupLayer.choices, default=LookupLayer.GENERATED
    )
    cost = models.BigIntegerField(default=0)
    tokens_in = models.IntegerField(null=True, blank=True)
    tokens_out = models.IntegerField(null=True, blank=True)
    vendor_cost_micros = models.BigIntegerField(null=True, blank=True)
    price_version = models.CharField(max_length=32, null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    model = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credits_usage_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
            models.Index(fields=["cache_hit", "kind"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} cost={self.cost} cache_hit={self.cache_hit}"
