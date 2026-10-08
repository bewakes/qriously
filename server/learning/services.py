from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import connection, transaction

from content.models import ContentVariant
from core.constants import lens_bucket as make_lens_bucket
from core.constants import normalize_lens

from .models import Node, NodeStatus, Span, Thread

if TYPE_CHECKING:
    from accounts.models import User


@transaction.atomic
def create_thread(
    user: User, title: str = "", lens: Mapping[str, str] | None = None
) -> Thread:
    normalized = normalize_lens(lens)
    return Thread.objects.create(
        user=user,
        title=title,
        lens=normalized,
        lens_bucket=make_lens_bucket(normalized),
    )


@transaction.atomic
def create_node(
    thread: Thread,
    kind: str,
    *,
    parent: Node | None = None,
    span: Span | None = None,
    content_variant: ContentVariant | None = None,
    status: str = NodeStatus.QUEUED,
    title: str = "",
    anchor_text: str = "",
    lens: Mapping[str, str] | None = None,
    order: int = 0,
    reused: bool = False,
) -> Node:
    effective_lens = normalize_lens(lens if lens is not None else thread.lens)
    node = Node.objects.create(
        thread=thread,
        parent=parent,
        root=parent.root if parent else None,
        kind=kind,
        status=status,
        span=span,
        content_variant=content_variant,
        anchor_text=anchor_text,
        title=title,
        lens=effective_lens,
        lens_bucket=make_lens_bucket(effective_lens),
        order=order,
        depth=parent.depth + 1 if parent else 0,
        reused=reused,
    )
    if parent is None:
        node.root = node
        node.save(update_fields=["root"])
    return node


def descendant_ids(node: Node) -> list[UUID]:
    """Return the ids of ``node`` and every node beneath it (recursive CTE)."""
    table = Node._meta.db_table
    sql = f"""
        WITH RECURSIVE subtree AS (
            SELECT id FROM {table} WHERE id = %s
            UNION ALL
            SELECT child.id
            FROM {table} AS child
            JOIN subtree ON child.parent_id = subtree.id
        )
        SELECT id FROM subtree
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [node.id])
        return [row[0] for row in cursor.fetchall()]


@transaction.atomic
def remove_subtree(node: Node) -> int:
    ids = descendant_ids(node)
    deleted, _ = Node.objects.filter(id__in=ids).delete()
    return deleted


def thread_snapshot(thread: Thread) -> dict[str, object]:
    return {
        "thread": thread,
        "nodes": list(thread.nodes.select_related("content_variant").all()),
        "spans": list(thread.spans.all()),
        "notes": list(thread.notes.all()),
    }
