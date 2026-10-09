from __future__ import annotations

from typing import Any

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import lens_bucket as make_lens_bucket
from core.constants import normalize_lens
from generation.api import GenerateSerializer, prepare_response

from .models import Node, NodeStatus, Note, Span, Thread
from .services import (
    create_thread,
    get_or_create_span,
    remove_subtree,
    render_outline,
    thread_snapshot,
)


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ["id", "title", "lens", "lens_bucket", "created_at", "updated_at"]
        read_only_fields = fields


class NodeSerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(read_only=True)
    root_id = serializers.UUIDField(read_only=True)
    content_variant_id = serializers.UUIDField(read_only=True)
    body = serializers.SerializerMethodField()
    citations = serializers.SerializerMethodField()
    est_read_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = [
            "id",
            "parent_id",
            "root_id",
            "kind",
            "anchor_text",
            "title",
            "lens",
            "lens_bucket",
            "status",
            "order",
            "depth",
            "collapsed",
            "reused",
            "content_variant_id",
            "body",
            "citations",
            "est_read_seconds",
        ]

    def _variant(self, obj: Node) -> Any:
        if obj.status == NodeStatus.DONE and obj.content_variant_id:
            return obj.content_variant
        return None

    def get_body(self, obj: Node) -> str | None:
        variant = self._variant(obj)
        return variant.body if variant else None

    def get_citations(self, obj: Node) -> list:
        variant = self._variant(obj)
        return variant.citations if variant else []

    def get_est_read_seconds(self, obj: Node) -> int | None:
        variant = self._variant(obj)
        return variant.est_read_seconds if variant else None


class SpanSerializer(serializers.ModelSerializer):
    source_node_id = serializers.UUIDField(read_only=True)
    concept_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Span
        fields = ["id", "source_node_id", "text", "concept_id", "created_at"]
        read_only_fields = fields


class NoteSerializer(serializers.ModelSerializer):
    span_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Note
        fields = ["id", "span_id", "text", "context", "tags", "created_at"]
        read_only_fields = ["id", "created_at"]


def _thread_or_404(user: Any, thread_id: str) -> Thread:
    return get_object_or_404(Thread, id=thread_id, user=user)


def _node_or_404(user: Any, node_id: str) -> Node:
    return get_object_or_404(Node, id=node_id, thread__user=user)


class ThreadPagination(CursorPagination):
    page_size = 50
    ordering = "-updated_at"


class ThreadListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ThreadPagination

    def get(self, request: Request) -> Response:
        queryset = request.user.threads.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ThreadSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        question = (request.data.get("question") or "").strip()
        title = (request.data.get("title") or "").strip() or question[:200]
        lens = request.data.get("lens")
        thread = create_thread(request.user, title=title, lens=lens)
        payload: dict[str, Any] = {"thread": ThreadSerializer(thread).data}
        if question:
            response = prepare_response(
                user=request.user,
                thread=thread,
                kind="root",
                question=question,
                lens=lens,
                idempotency_key=request.headers.get("Idempotency-Key"),
            )
            if response.status_code >= 400:
                return response
            payload.update(response.data)
        return Response(payload, status=201)


class ThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, thread_id: str) -> Response:
        thread = _thread_or_404(request.user, thread_id)
        snapshot = thread_snapshot(thread)
        return Response(
            {
                "thread": ThreadSerializer(thread).data,
                "nodes": NodeSerializer(snapshot["nodes"], many=True).data,
                "spans": SpanSerializer(snapshot["spans"], many=True).data,
                "notes": NoteSerializer(snapshot["notes"], many=True).data,
            }
        )

    def patch(self, request: Request, thread_id: str) -> Response:
        thread = _thread_or_404(request.user, thread_id)
        fields: list[str] = []
        if "title" in request.data:
            thread.title = request.data["title"]
            fields.append("title")
        if "lens" in request.data:
            lens = normalize_lens(request.data["lens"])
            thread.lens = lens
            thread.lens_bucket = make_lens_bucket(lens)
            fields += ["lens", "lens_bucket"]
        if fields:
            thread.save(update_fields=[*fields, "updated_at"])
        return Response(ThreadSerializer(thread).data)

    def delete(self, request: Request, thread_id: str) -> Response:
        _thread_or_404(request.user, thread_id).delete()
        return Response(status=204)


class NodeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, thread_id: str) -> Response:
        thread = _thread_or_404(request.user, thread_id)
        serializer = GenerateSerializer(
            data={**request.data, "thread_id": str(thread.id)}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        parent = None
        if data.get("parent_node_id"):
            parent = get_object_or_404(
                Node, id=data["parent_node_id"], thread=thread
            )
        response = prepare_response(
            user=request.user,
            thread=thread,
            kind=data["kind"],
            parent=parent,
            span_text=(data.get("span") or {}).get("text"),
            question=data.get("question"),
            lens=data.get("lens"),
            idempotency_key=(
                data.get("idempotency_key") or request.headers.get("Idempotency-Key")
            ),
        )
        if response.status_code < 400:
            response.status_code = 202
        return response


class NodeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, node_id: str) -> Response:
        node = _node_or_404(request.user, node_id)
        fields: list[str] = []
        if "collapsed" in request.data:
            node.collapsed = bool(request.data["collapsed"])
            fields.append("collapsed")
        if "title" in request.data:
            node.title = request.data["title"]
            fields.append("title")
        if fields:
            node.save(update_fields=[*fields, "updated_at"])
        return Response(NodeSerializer(node).data)

    def delete(self, request: Request, node_id: str) -> Response:
        node = _node_or_404(request.user, node_id)
        remove_subtree(node)
        return Response(status=204)


class NotePagination(CursorPagination):
    page_size = 50
    ordering = "-created_at"


class NoteListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotePagination

    def get(self, request: Request, thread_id: str) -> Response:
        thread = _thread_or_404(request.user, thread_id)
        queryset = thread.notes.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NoteSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request, thread_id: str) -> Response:
        thread = _thread_or_404(request.user, thread_id)
        span = self._resolve_span(request, thread)
        if span is None:
            return Response(
                {"error": "span_id or source_node_id+text is required"},
                status=400,
            )
        text = (request.data.get("text") or "").strip() or span.text
        context = (request.data.get("context") or "").strip() or span.source_node.title
        tags = request.data.get("tags") or []
        note = Note.objects.create(
            thread=thread, span=span, text=text, context=context, tags=tags
        )
        return Response(NoteSerializer(note).data, status=201)

    @staticmethod
    def _resolve_span(request: Request, thread: Thread) -> Span | None:
        span_id = request.data.get("span_id")
        if span_id:
            return get_object_or_404(Span, id=span_id, thread=thread)
        source_node_id = request.data.get("source_node_id")
        text = (request.data.get("text") or "").strip()
        if not source_node_id or not text:
            return None
        source_node = get_object_or_404(Node, id=source_node_id, thread=thread)
        return get_or_create_span(thread, source_node, text)


class NoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, note_id: str) -> Response:
        note = get_object_or_404(
            Note, id=note_id, thread__user=request.user
        )
        fields: list[str] = []
        if "text" in request.data:
            note.text = request.data["text"]
            fields.append("text")
        if "context" in request.data:
            note.context = request.data["context"]
            fields.append("context")
        if "tags" in request.data:
            note.tags = request.data["tags"]
            fields.append("tags")
        if fields:
            note.save(update_fields=[*fields, "updated_at"])
        return Response(NoteSerializer(note).data)

    def delete(self, request: Request, note_id: str) -> Response:
        get_object_or_404(Note, id=note_id, thread__user=request.user).delete()
        return Response(status=204)


class OutlineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, thread_id: str) -> HttpResponse:
        thread = _thread_or_404(request.user, thread_id)
        return HttpResponse(
            render_outline(thread), content_type="text/markdown; charset=utf-8"
        )
