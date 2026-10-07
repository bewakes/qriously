from django.contrib import admin

from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "endpoint",
        "kind",
        "status",
        "credits_charged",
        "vendor_cost_micros",
        "created_at",
    ]
    list_filter = ["status", "kind"]
    search_fields = ["id", "endpoint", "idempotency_key", "user__email"]
    readonly_fields = [
        "id",
        "created_at",
        "completed_at",
        "user",
        "wallet",
        "endpoint",
        "kind",
        "lens_bucket",
        "status",
        "error_code",
        "credits_charged",
        "vendor_cost_micros",
        "tokens_in",
        "tokens_out",
        "latency_ms",
        "idempotency_key",
    ]
