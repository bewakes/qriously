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
from generation.services import (
    _action_log,
    _context_key,
    _MetaSplitter,
    _parse_output,
    _trajectory,
    prepare_generation,
    stream_generation,
)
from learning.models import NodeStatus
from learning.services import create_node, create_thread

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


def test_context_key_includes_the_span_only_for_ask():
    assert _context_key(None, None, "ask", "Abc") != _context_key(
        None, None, "ask", "Xyz"
    )
    assert _context_key(None, None, "ask", "Abc") == _context_key(
        None, None, "ask", "abc"
    )
    assert _context_key(None, None, "dive", "Abc") == _context_key(
        None, None, "dive", "Xyz"
    )
    assert _context_key(None, None, "ask", None) == ""


class _ThreadId:
    def __init__(self, id):
        self.id = id


def test_context_key_followup_is_per_thread():
    thread_a, thread_b = _ThreadId("a"), _ThreadId("b")
    assert _context_key(thread_a, None, "followup", None) != _context_key(
        thread_b, None, "followup", None
    )


def test_meta_splitter_forwards_body_and_withholds_meta():
    splitter = _MetaSplitter()
    emitted = splitter.feed("The target adjusts. <<<QRIOUSLY\n")
    assert emitted == "The target adjusts. "
    assert splitter.stopped is True
    assert splitter.feed("gist: x\n>>>") == ""


def test_meta_splitter_does_not_leak_a_split_sentinel():
    splitter = _MetaSplitter()
    first = splitter.feed("body text <<<QRI")
    assert "<<<QRI" not in first
    splitter.feed("OUSLY\ngist: y\n>>>")
    assert splitter.stopped is True


def test_meta_splitter_finish_returns_withheld_tail():
    splitter = _MetaSplitter()
    emitted = splitter.feed("plain answer")
    assert emitted + splitter.finish() == "plain answer"


def test_parse_output_splits_gist_and_summary():
    raw = "Here is the answer.\n<<<QRIOUSLY\ngist: one line\nsummary: hi\n>>>"
    body, gist, summary = _parse_output("followup", raw)
    assert body == "Here is the answer."
    assert gist == "one line"
    assert summary == "hi"


def test_parse_output_passthrough_for_non_followup():
    assert _parse_output("dive", "just text") == ("just text", None, None)


@pytest.mark.django_db(transaction=True)
def test_action_log_and_trajectory_derive_from_the_thread(context):
    user, wallet, thread = context
    create_node(thread, "dive", title="base fee", anchor_text="base fee",
                status=NodeStatus.DONE)
    create_node(thread, "eli5", title="target", anchor_text="target",
                status=NodeStatus.DONE)
    create_node(thread, "followup", title="pending", status=NodeStatus.QUEUED)

    actions = _action_log(thread)
    assert 'dived into "base fee"' in actions
    assert 'asked for a simpler version of "target"' in actions
    assert len(actions) == 2

    trajectory = _trajectory(thread)
    assert "Root question: Why is the sky blue?" in trajectory
    assert "Actions so far:" in trajectory
