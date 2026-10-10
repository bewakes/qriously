import asyncio
import json
from uuid import uuid4

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import AsyncClient

from content import services as content_services
from credits.models import Reason
from credits.services import get_wallet, spend
from generation import services as generation_services
from generation.llm.base import StreamChunk
from generation.llm.errors import LLMError
from generation.models import GenerationJob
from safety.decision import Decision, Outcome

User = get_user_model()

LENS = {
    "familiarity": "basics",
    "depth": "solid",
    "style": "plain",
    "goal": "curious",
}


class FakeLLM:
    model = "deepseek-flash"

    def __init__(self, chunks):
        self.chunks = chunks
        self.called = False

    async def stream(self, messages, *, model=None):
        self.called = True
        for chunk in self.chunks:
            yield chunk


class ErrorLLM:
    model = "deepseek-flash"

    async def stream(self, messages, *, model=None):
        raise LLMError("upstream_timeout", "boom", retryable=True)
        yield  # pragma: no cover


class BlockPolicy:
    name = "block"

    def check(self, text, *, context=None):
        return Decision(outcome=Outcome.BLOCK, category="unsafe", provider=self.name)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token(client):
    body = client.post("/api/v1/auth/device", content_type="application/json").json()
    return body["token"]


def start_thread(client, token, question=None):
    data = {"question": question} if question else {}
    response = client.post(
        "/api/v1/threads",
        data=json.dumps(data),
        content_type="application/json",
        headers=auth(token),
    )
    return response


def post_generate(client, token, payload, idempotency_key=None):
    headers = dict(auth(token))
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return client.post(
        "/api/v1/generate",
        data=json.dumps(payload),
        content_type="application/json",
        headers=headers,
    )


def parse_sse(text):
    events = []
    for block in text.strip().split("\n\n"):
        name = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[len("event: ") :]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: ") :])
        if name is not None:
            events.append((name, data))
    return events


def consume_stream(token, job_id):
    async def run():
        try:
            client = AsyncClient()
            response = await client.get(
                f"/api/v1/generate/{job_id}/stream", headers=auth(token)
            )
            chunks = []
            async for chunk in response.streaming_content:
                chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
            return response.status_code, "".join(chunks)
        finally:
            await sync_to_async(connections.close_all)()

    return asyncio.run(run())


def new_thread(client, token, question=None):
    response = start_thread(client, token, question)
    assert response.status_code == 201, response.content
    return response.json()["thread"]["id"]


def generate_root(client, token, question="Why is the sky blue?"):
    payload = {
        "thread_id": new_thread(client, token),
        "kind": "root",
        "question": question,
    }
    return post_generate(client, token, payload).json()


@pytest.mark.django_db(transaction=True)
def test_generate_descriptor_miss(client, token):
    question = "Why is the sky blue?"
    payload = {
        "thread_id": new_thread(client, token),
        "kind": "root",
        "question": question,
    }
    response = post_generate(client, token, payload)
    assert response.status_code == 200
    body = response.json()
    assert body["cache_hit"] is False
    assert body["lookup_layer"] == "generated"
    assert body["cost"] == 15
    assert body["balance"] == 5000
    assert body["stream_url"] == f"/api/v1/generate/{body['job_id']}/stream"


@pytest.mark.django_db(transaction=True)
def test_stream_miss_streams_tokens_and_charges(client, token, monkeypatch):
    descriptor = generate_root(client, token)
    fake = FakeLLM(
        [
            StreamChunk(text="Sky "),
            StreamChunk(text="is blue."),
            StreamChunk(tokens_in=5, tokens_out=3),
        ]
    )
    monkeypatch.setattr(generation_services, "get_client", lambda: fake)

    status, text = consume_stream(token, descriptor["job_id"])
    assert status == 200
    events = parse_sse(text)
    assert [name for name, _ in events] == [
        "meta",
        "token",
        "token",
        "done",
        "usage",
    ]
    assert "".join(d["text"] for n, d in events if n == "token") == "Sky is blue."
    usage = events[-1][1]
    assert usage["credits_charged"] == 15
    assert usage["vendor_cost_micros"] is not None
    assert usage["balance"] == 4985

    balance = client.get("/api/v1/credits/balance", headers=auth(token)).json()
    assert balance["balance"] == 4985


@pytest.mark.django_db(transaction=True)
def test_stream_hit_replays_without_calling_model(client, token, monkeypatch):
    concept = content_services.upsert_concept("Why is the sky blue?")
    content_services.create_variant(
        concept=concept,
        kind="root",
        lens=LENS,
        title="Seeded",
        body="Because of Rayleigh scattering.",
        context_key="",
    )
    descriptor = generate_root(client, token)
    assert descriptor["cache_hit"] is True
    assert descriptor["cost"] == 4

    fake = FakeLLM([])
    monkeypatch.setattr(generation_services, "get_client", lambda: fake)
    status, text = consume_stream(token, descriptor["job_id"])

    assert status == 200
    assert fake.called is False
    events = parse_sse(text)
    assert [d["text"] for n, d in events if n == "token"] == [
        "Because of Rayleigh scattering."
    ]
    usage = events[-1][1]
    assert usage["cache_hit"] is True
    assert usage["vendor_cost_micros"] is None
    assert usage["balance"] == 4996


@pytest.mark.django_db(transaction=True)
def test_stream_upstream_error_charges_nothing(client, token, monkeypatch):
    descriptor = generate_root(client, token)
    monkeypatch.setattr(generation_services, "get_client", lambda: ErrorLLM())

    status, text = consume_stream(token, descriptor["job_id"])
    assert status == 200
    events = parse_sse(text)
    assert events[-1][0] == "error"
    assert events[-1][1]["code"] == "upstream_timeout"

    balance = client.get("/api/v1/credits/balance", headers=auth(token)).json()
    assert balance["balance"] == 5000


@pytest.mark.django_db(transaction=True)
def test_idempotent_replay_returns_same_job(client, token):
    question = "Why is the sky blue?"
    payload = {
        "thread_id": new_thread(client, token),
        "kind": "root",
        "question": question,
    }
    first = post_generate(client, token, payload, idempotency_key="key-1").json()
    second = post_generate(client, token, payload, idempotency_key="key-1").json()

    assert first["job_id"] == second["job_id"]
    assert first["request_id"] == second["request_id"]
    assert GenerationJob.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_screening_block_returns_422(client, token, monkeypatch):
    monkeypatch.setattr(
        generation_services, "get_policy", lambda name=None: BlockPolicy()
    )
    response = post_generate(
        client,
        token,
        {
            "thread_id": new_thread(client, token),
            "kind": "root",
            "question": "something disallowed",
        },
    )
    assert response.status_code == 422
    assert response.json() == {"error": "content_blocked", "category": "unsafe"}
    assert GenerationJob.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_insufficient_credits_returns_402(client, token):
    user = User.objects.get()
    spend(get_wallet(user), 5000, Reason.MANUAL)
    response = post_generate(
        client,
        token,
        {
            "thread_id": new_thread(client, token),
            "kind": "root",
            "question": "Why is the sky blue?",
        },
    )
    assert response.status_code == 402
    body = response.json()
    assert body["error"] == "insufficient_credits"
    assert body["required"] == 15
    assert body["balance"] == 0


def _valid(payload):
    from generation.api import GenerateSerializer

    serializer = GenerateSerializer(data=payload)
    return serializer.is_valid(), serializer.errors


def test_followup_serializer_requires_parent_and_question():
    valid, _ = _valid({"thread_id": str(uuid4()), "kind": "followup", "question": "hi"})
    assert valid is False
    valid, _ = _valid(
        {
            "thread_id": str(uuid4()),
            "kind": "followup",
            "question": "hi",
            "span": {"text": "ignored"},
        }
    )
    assert valid is False
    valid, errors = _valid(
        {
            "thread_id": str(uuid4()),
            "kind": "followup",
            "parent_node_id": str(uuid4()),
            "question": "hi",
        }
    )
    assert valid is True, errors
