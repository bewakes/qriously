from django.contrib import admin

from .models import GenerationJob


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "kind",
        "status",
        "model",
        "thread",
        "created_at",
        "completed_at",
    ]
    list_filter = ["status", "kind", "model"]
    search_fields = ["id", "idempotency_key", "thread__title"]
    readonly_fields = ["id", "created_at", "completed_at"]
