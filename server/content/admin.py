from django.contrib import admin

from .models import Concept, ConceptLink, ContentVariant


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "kind_hint", "created_at"]
    search_fields = ["key", "text"]
    readonly_fields = ["id", "key", "created_at"]


@admin.register(ContentVariant)
class ContentVariantAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "kind",
        "title",
        "concept",
        "lens_bucket",
        "prompt_version",
        "model",
        "created_at",
    ]
    list_filter = ["kind", "prompt_version", "model"]
    search_fields = ["title", "concept__key", "concept__text"]
    readonly_fields = [
        "id",
        "concept",
        "kind",
        "lens_bucket",
        "lens_vector",
        "context_fingerprint",
        "prompt_version",
        "title",
        "body",
        "citations",
        "est_read_seconds",
        "model",
        "created_at",
    ]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConceptLink)
class ConceptLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "parent", "child", "kind", "weight", "updated_at"]
    list_filter = ["kind"]
    search_fields = ["parent__key", "child__key"]
    readonly_fields = ["id", "created_at", "updated_at"]
