from django.conf import settings
from django.db import models

from core.models import UUIDModel


class RequestStatus(models.TextChoices):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RequestLog(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="requests"
    )
    wallet = models.ForeignKey(
        "credits.Wallet", on_delete=models.CASCADE, related_name="requests"
    )
    endpoint = models.CharField(max_length=64)
    kind = models.CharField(max_length=32, blank=True)
    lens_bucket = models.CharField(max_length=64, blank=True)

    status = models.CharField(
        max_length=16, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    error_code = models.CharField(max_length=64, null=True, blank=True)

    credits_charged = models.BigIntegerField(default=0)
    vendor_cost_micros = models.BigIntegerField(null=True, blank=True)
    tokens_in = models.IntegerField(null=True, blank=True)
    tokens_out = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)

    idempotency_key = models.CharField(
        max_length=255, null=True, blank=True, unique=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "telemetry_request_log"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.endpoint} {self.status} ({self.id})"
