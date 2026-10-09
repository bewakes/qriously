from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import connection, transaction

from content.models import ContentVariant
from content.services import upsert_concept
from core.constants import lens_bucket as make_lens_bucket
from core.constants import normalize_lens

from .models import Node, NodeStatus, Note, Span, Thread

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


@transaction.atomic
def get_or_create_span(thread: Thread, source_node: Node, text: str) -> Span:
    """Return the span for a phrase saved from ``source_node``, creating it once.

    A saved note is span-anchored: the phrase becomes a ``Span`` (reused if the
    same phrase was already saved from the same node) so notes and branches share
    one anchor.
    """
    clean = " ".join(text.split())
    if not clean:
        raise ValueError("span text cannot be empty")
    existing = Span.objects.filter(
        thread=thread, source_node=source_node, text=clean
    ).first()
    if existing is not None:
        return existing
    return Span.objects.create(
        thread=thread,
        source_node=source_node,
        text=clean,
        concept=upsert_concept(clean),
    )


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


def render_outline(thread: Thread) -> str:
    """Render the trail (node headings) and saved notes as markdown."""
    nodes = list(thread.nodes.order_by("depth", "order", "created_at"))
    children: dict[UUID | None, list[Node]] = {}
    for node in nodes:
        children.setdefault(node.parent_id, []).append(node)

    notes_by_node: dict[UUID, list[Note]] = {}
    for note in thread.notes.select_related("span"):
        notes_by_node.setdefault(note.span.source_node_id, []).append(note)

    lines: list[str] = [f"# {thread.title or 'Untitled thread'}", ""]

    def walk(node: Node, level: int) -> None:
        heading = node.title or node.anchor_text or node.kind
        lines.append(f"{'#' * min(level, 6)} {heading}")
        for note in notes_by_node.get(node.id, []):
            lines.append(f"- {note.text}")
        lines.append("")
        for child in children.get(node.id, []):
            walk(child, level + 1)

    for root in children.get(None, []):
        walk(root, 2)
    return "\n".join(lines).rstrip() + "\n"
