from django.contrib import admin

from .models import ModelPrice, RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "endpoint",
        "kind",
        "status",
        "cache_hit",
        "credits_charged",
        "vendor_cost_micros",
        "created_at",
    ]
    list_filter = ["status", "cache_hit", "screening_status", "kind"]
    search_fields = ["id", "endpoint", "idempotency_key", "user__email"]
    readonly_fields = [
        "id",
        "created_at",
        "completed_at",
        "user",
        "wallet",
        "endpoint",
        "method",
        "kind",
        "lens_bucket",
        "cache_hit",
        "lookup_layer",
        "screening_status",
        "screening_category",
        "screening_score",
        "screening_provider",
        "status",
        "error_code",
        "credits_charged",
        "vendor_cost_micros",
        "tokens_in",
        "tokens_out",
        "latency_ms",
        "price_version",
        "client_fingerprint",
        "idempotency_key",
    ]


@admin.register(ModelPrice)
class ModelPriceAdmin(admin.ModelAdmin):
    list_display = [
        "model",
        "version",
        "input_per_1k_micros",
        "output_per_1k_micros",
        "currency",
        "effective_at",
    ]
    list_filter = ["model", "currency"]
