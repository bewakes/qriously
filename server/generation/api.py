from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import DeviceTokenAuthentication
from credits.errors import InsufficientCredits
from learning.models import Node, Thread

from .errors import ContentBlocked
from .models import GenerationJob
from .services import job_descriptor, prepare_generation, stream_generation

if TYPE_CHECKING:
    from accounts.models import User

GENERATE_KINDS = ["root", "dive", "eli5", "example", "define", "ask"]


class GenerateSerializer(serializers.Serializer):
    thread_id = serializers.UUIDField()
    parent_node_id = serializers.UUIDField(required=False, allow_null=True)
    kind = serializers.ChoiceField(choices=GENERATE_KINDS)
    span = serializers.DictField(required=False)
    question = serializers.CharField(required=False, allow_blank=True)
    lens = serializers.DictField(required=False)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        kind = attrs["kind"]
        span_text = (attrs.get("span") or {}).get("text", "").strip()
        question = (attrs.get("question") or "").strip()
        has_parent = bool(attrs.get("parent_node_id"))
        if kind == "root":
            if not question:
                raise serializers.ValidationError({"question": "required for root"})
        elif kind == "ask":
            if not (has_parent and span_text and question):
                raise serializers.ValidationError(
                    {"span": "parent_node_id, span.text and question are required"}
                )
        elif not (has_parent and span_text):
            raise serializers.ValidationError(
                {"span": "parent_node_id and span.text are required"}
            )
        return attrs


def prepare_response(
    *,
    user: User,
    thread: Thread,
    kind: str,
    parent: Node | None = None,
    span_text: str | None = None,
    question: str | None = None,
    lens: dict[str, str] | None = None,
    idempotency_key: str | None = None,
) -> Response:
    """Run ``prepare_generation`` and map policy outcomes to HTTP responses."""
    try:
        job = prepare_generation(
            user=user,
            thread=thread,
            kind=kind,
            parent=parent,
            span_text=span_text,
            question=question,
            lens=lens,
            idempotency_key=idempotency_key,
        )
    except ContentBlocked as exc:
        return Response(
            {"error": "content_blocked", "category": exc.category}, status=422
        )
    except InsufficientCredits as exc:
        return Response(
            {
                "error": "insufficient_credits",
                "required": exc.required,
                "balance": exc.balance,
                "top_up_url": None,
            },
            status=402,
        )
    return Response(job_descriptor(job))


class GenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = GenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        thread = get_object_or_404(
            Thread, id=data["thread_id"], user=request.user
        )
        parent = None
        if data.get("parent_node_id"):
            parent = get_object_or_404(
                Node, id=data["parent_node_id"], thread=thread
            )
        return prepare_response(
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


def _load_job(user: User, job_id: str) -> GenerationJob | None:
    return (
        GenerationJob.objects.filter(id=job_id, thread__user=user)
        .select_related("wallet", "concept", "node", "request", "thread")
        .first()
    )


def _format_sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def generate_stream_view(request: Any, job_id: str) -> HttpResponse:
    """SSE stream for a prepared job (docs/API.md §4).

    Uses a plain async view (not DRF) so the response can stream an async
    generator; auth is done explicitly with the device-token authenticator.
    """
    try:
        result = await sync_to_async(DeviceTokenAuthentication().authenticate)(
            request
        )
    except AuthenticationFailed:
        return HttpResponse(status=401)
    if result is None:
        return HttpResponse(status=401)

    user, _session = result
    job = await sync_to_async(_load_job)(user, job_id)
    if job is None:
        return HttpResponse(status=404)

    async def events() -> AsyncIterator[str]:
        async for name, data in stream_generation(job):
            yield _format_sse(name, data)

    response = StreamingHttpResponse(
        events(), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
