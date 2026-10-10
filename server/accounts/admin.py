from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Session, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created_at"]
    list_display = ["id", "email", "is_anonymous_device", "is_active", "created_at"]
    list_filter = ["is_anonymous_device", "is_active", "is_staff"]
    search_fields = ["email", "display_name"]
    fieldsets = [
        (None, {"fields": ["email", "display_name", "password"]}),
        (
            "Flags",
            {
                "fields": [
                    "is_anonymous_device",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ]
            },
        ),
        ("Timestamps", {"fields": ["created_at", "updated_at", "last_login"]}),
    ]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    ]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "label", "created_at", "revoked_at"]
    list_filter = ["revoked_at"]
    search_fields = ["user__email", "label"]
    readonly_fields = ["token_hash", "created_at", "last_seen_at"]
