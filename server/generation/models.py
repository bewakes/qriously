from django.db import models

from core.models import UUIDModel


class JobStatus(models.TextChoices):
    PENDING = "pending"
    STREAMING = "streaming"
    DONE = "done"
    ERROR = "error"


class GenerationJob(UUIDModel):
    request = models.ForeignKey(
        "telemetry.RequestLog",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs",
    )
    wallet = models.ForeignKey(
        "credits.Wallet", on_delete=models.CASCADE, related_name="generation_jobs"
    )
    thread = models.ForeignKey(
        "learning.Thread", on_delete=models.CASCADE, related_name="generation_jobs"
    )
    node = models.ForeignKey(
        "learning.Node",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs",
    )
    concept = models.ForeignKey(
        "content.Concept",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs",
    )
    kind = models.CharField(max_length=16, blank=True)
    lens_bucket = models.CharField(max_length=64, blank=True)
    context_fingerprint = models.CharField(max_length=64, blank=True)
    prompt_version = models.CharField(max_length=32)
    model = models.CharField(max_length=64)
    idempotency_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=16, choices=JobStatus.choices, default=JobStatus.PENDING
    )
    error_code = models.CharField(max_length=64, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "generation_generation_job"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind} {self.status} ({self.id})"
