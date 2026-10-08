from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from content.models import Kind
from core.models import TimeStampedModel, UUIDModel


class NodeStatus(models.TextChoices):
    QUEUED = "queued"
    STREAMING = "streaming"
    DONE = "done"
    ERROR = "error"


class Thread(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads"
    )
    title = models.TextField(blank=True)
    lens = models.JSONField(default=dict, blank=True)
    lens_bucket = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "learning_thread"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or str(self.id)


class Node(UUIDModel, TimeStampedModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="nodes"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    root = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rooted_nodes",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(
        max_length=16, choices=NodeStatus.choices, default=NodeStatus.QUEUED
    )
    span = models.ForeignKey(
        "learning.Span",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="nodes",
    )
    content_variant = models.ForeignKey(
        "content.ContentVariant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="nodes",
    )
    anchor_text = models.TextField(blank=True)
    title = models.TextField(blank=True)
    lens = models.JSONField(default=dict, blank=True)
    lens_bucket = models.CharField(max_length=64, blank=True)
    order = models.IntegerField(default=0)
    depth = models.IntegerField(default=0)
    collapsed = models.BooleanField(default=False)
    reused = models.BooleanField(default=False)

    class Meta:
        db_table = "learning_node"
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["thread", "parent"])]

    def __str__(self) -> str:
        return self.title or self.anchor_text or str(self.id)


class Span(UUIDModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="spans"
    )
    source_node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="sourced_spans"
    )
    text = models.TextField()
    concept = models.ForeignKey(
        "content.Concept",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spans",
    )
    start_offset = models.IntegerField(null=True, blank=True)
    end_offset = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "learning_span"

    def __str__(self) -> str:
        return self.text


class Note(UUIDModel, TimeStampedModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="notes"
    )
    span = models.ForeignKey(
        Span, on_delete=models.CASCADE, related_name="notes"
    )
    text = models.TextField()
    context = models.TextField(blank=True)
    tags = ArrayField(
        models.CharField(max_length=64), default=list, blank=True
    )

    class Meta:
        db_table = "learning_note"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.text
