from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import TimeStampedModel, UUIDModel


class Kind(models.TextChoices):
    ROOT = "root"
    DIVE = "dive"
    ELI5 = "eli5"
    EXAMPLE = "example"
    DEFINE = "define"
    ASK = "ask"
    VISUAL = "visual"
    RELEVANCE = "relevance"


class ConceptKindHint(models.TextChoices):
    QUESTION = "question"
    ENTITY = "entity"
    PHRASE = "phrase"
    TERM = "term"


class LookupLayer(models.TextChoices):
    EXACT = "exact"
    BROADENED = "broadened"
    SEMANTIC = "semantic"
    GENERATED = "generated"


class Concept(UUIDModel):
    key = models.TextField(unique=True)
    text = models.TextField()
    kind_hint = models.CharField(
        max_length=16, choices=ConceptKindHint.choices, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_concept"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.text


class ContentVariant(UUIDModel):
    concept = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="variants"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    lens_bucket = models.CharField(max_length=64)
    lens_vector = ArrayField(models.FloatField(), default=list, blank=True)
    context_fingerprint = models.CharField(max_length=64, blank=True, default="")
    prompt_version = models.CharField(max_length=32)
    title = models.TextField()
    body = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    est_read_seconds = models.IntegerField(default=0)
    model = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_content_variant"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "concept",
                    "kind",
                    "lens_bucket",
                    "context_fingerprint",
                    "prompt_version",
                ],
                name="content_variant_unique_lens_context",
            )
        ]
        indexes = [models.Index(fields=["concept", "kind", "lens_bucket"])]

    def __str__(self) -> str:
        return f"{self.kind}:{self.title} ({self.lens_bucket})"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValueError(
                "ContentVariant rows are immutable; create a new prompt_version."
            )
        super().save(*args, **kwargs)


class ConceptLink(UUIDModel, TimeStampedModel):
    parent = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="outgoing_links"
    )
    child = models.ForeignKey(
        Concept, on_delete=models.CASCADE, related_name="incoming_links"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    weight = models.IntegerField(default=1)

    class Meta:
        db_table = "content_concept_link"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "child", "kind"],
                name="content_concept_link_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.parent.key} -[{self.kind}]-> {self.child.key}"
