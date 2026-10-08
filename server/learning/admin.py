from django.contrib import admin

from .models import Node, Note, Span, Thread


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "user", "lens_bucket", "created_at"]
    list_filter = ["lens_bucket"]
    search_fields = ["id", "title", "user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "kind",
        "status",
        "thread",
        "parent",
        "depth",
        "order",
        "reused",
    ]
    list_filter = ["kind", "status", "reused"]
    search_fields = ["id", "title", "anchor_text"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Span)
class SpanAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "thread", "source_node", "concept", "created_at"]
    search_fields = ["id", "text"]
    readonly_fields = ["id", "created_at"]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["id", "thread", "span", "text", "created_at"]
    search_fields = ["id", "text"]
    readonly_fields = ["id", "created_at", "updated_at"]
