import asyncio

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connections

from content import services as content_services
from credits.errors import InsufficientCredits
from credits.models import Reason
from credits.services import get_wallet, spend
from generation.llm.base import StreamChunk
from generation.llm.errors import LLMError
from generation.models import JobStatus
from generation.services import prepare_generation, stream_generation
from learning.models import NodeStatus
from learning.services import create_thread

User = get_user_model()

LENS = {"familiarity": "basics", "depth": "solid", "style": "plain", "goal": "curious"}


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


def collect(job, llm):
    async def run():
        try:
            return [event async for event in stream_generation(job, llm=llm)]
        finally:
            await sync_to_async(connections.close_all)()

    return asyncio.run(run())


@pytest.fixture
def context(db):
    user = User.objects.create_user()
    wallet = get_wallet(user)
    thread = create_thread(user, title="Why is the sky blue?")
    return user, wallet, thread


@pytest.mark.django_db(transaction=True)
def test_miss_streams_tokens_and_persists_variant(context):
    user, wallet, thread = context
    job = prepare_generation(
        user=user, thread=thread, kind="root", question="Why is the sky blue?"
    )
    assert job.cache_hit is False

    llm = FakeLLM(
        [
            StreamChunk(text="Sky "),
            StreamChunk(text="is blue."),
            StreamChunk(tokens_in=5, tokens_out=3),
        ]
    )
    events = collect(job, llm)

    assert [name for name, _ in events] == [
        "meta",
        "token",
        "token",
        "done",
        "usage",
    ]
    text = "".join(d["text"] for name, d in events if name == "token")
    assert text == "Sky is blue."

    job.refresh_from_db()
    job.node.refresh_from_db()
    assert job.status == JobStatus.DONE
    assert job.node.status == NodeStatus.DONE
    assert job.node.reused is False
    assert job.node.content_variant is not None

    wallet.refresh_from_db()
    assert wallet.balance == 5000 - 15
    usage = events[-1][1]
    assert usage["cache_hit"] is False
    assert usage["vendor_cost_micros"] is not None
    assert usage["tokens_in"] == 5


@pytest.mark.django_db(transaction=True)
def test_hit_replays_without_calling_the_model(context):
    user, wallet, thread = context
    concept = content_services.upsert_concept("Why is the sky blue?")
    content_services.create_variant(
        concept=concept,
        kind="root",
        lens=LENS,
        title="Seeded",
        body="Because of Rayleigh scattering.",
        context_key="",
    )

    job = prepare_generation(
        user=user, thread=thread, kind="root", question="Why is the sky blue?"
    )
    assert job.cache_hit is True

    llm = FakeLLM([])
    events = collect(job, llm)

    assert llm.called is False
    assert [d["text"] for name, d in events if name == "token"] == [
        "Because of Rayleigh scattering."
    ]
    job.node.refresh_from_db()
    assert job.node.reused is True
    wallet.refresh_from_db()
    assert wallet.balance == 5000 - 4
    usage = events[-1][1]
    assert usage["cache_hit"] is True
    assert usage["vendor_cost_micros"] is None


@pytest.mark.django_db(transaction=True)
def test_prepare_rejects_when_credits_are_short(context):
    user, wallet, thread = context
    spend(wallet, 5000, Reason.MANUAL)

    with pytest.raises(InsufficientCredits):
        prepare_generation(user=user, thread=thread, kind="root", question="hi")


@pytest.mark.django_db(transaction=True)
def test_upstream_error_marks_job_and_node_failed(context):
    user, wallet, thread = context
    job = prepare_generation(
        user=user, thread=thread, kind="root", question="Why is the sky blue?"
    )

    events = collect(job, ErrorLLM())

    assert events[-1][0] == "error"
    assert events[-1][1]["code"] == "upstream_timeout"
    job.refresh_from_db()
    job.node.refresh_from_db()
    assert job.status == JobStatus.ERROR
    assert job.node.status == NodeStatus.ERROR
    wallet.refresh_from_db()
    assert wallet.balance == 5000
