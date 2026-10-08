from django.contrib import admin

from .models import CreditEntry, UsageEvent, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "balance", "lifetime_granted", "lifetime_spent"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CreditEntry)
class CreditEntryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "wallet",
        "entry_type",
        "reason",
        "delta",
        "balance_after",
        "created_at",
    ]
    list_filter = ["entry_type", "reason"]
    search_fields = ["wallet__user__email", "idempotency_key"]
    readonly_fields = [
        "id",
        "wallet",
        "delta",
        "balance_after",
        "entry_type",
        "reason",
        "idempotency_key",
        "metadata",
        "created_at",
    ]


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "kind",
        "cache_hit",
        "lookup_layer",
        "cost",
        "vendor_cost_micros",
        "model",
        "created_at",
    ]
    list_filter = ["cache_hit", "lookup_layer", "kind", "model"]
    search_fields = ["id", "wallet__user__email"]
    readonly_fields = ["id", "created_at"]
