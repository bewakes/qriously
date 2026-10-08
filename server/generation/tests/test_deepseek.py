import asyncio
import json

import httpx
import pytest

from generation.llm.deepseek import DeepSeekClient
from generation.llm.errors import LLMError


def sse(*payloads):
    body = "".join(f"data: {json.dumps(p)}\n\n" for p in payloads)
    return (body + "data: [DONE]\n\n").encode()


def make_client(handler, **kwargs):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return DeepSeekClient("test-key", http_client=http, backoff=0, **kwargs)


def collect(client, messages=None):
    messages = messages or [{"role": "user", "content": "hi"}]

    async def run():
        return [chunk async for chunk in client.stream(messages)]

    return asyncio.run(run())


def test_streams_text_and_reads_usage():
    def handler(request):
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            content=sse(
                {"choices": [{"delta": {"content": "Hello "}}]},
                {"choices": [{"delta": {"content": "world"}, "finish_reason": "stop"}]},
                {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 2}},
            ),
            headers={"content-type": "text/event-stream"},
        )

    chunks = collect(make_client(handler))
    assert "".join(chunk.text for chunk in chunks) == "Hello world"
    assert chunks[-1].tokens_in == 10
    assert chunks[-1].tokens_out == 2


def test_retries_retryable_status_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, content=b"{}")
        body = sse({"choices": [{"delta": {"content": "ok"}}]})
        return httpx.Response(200, content=body)

    chunks = collect(make_client(handler, max_retries=2))
    assert "".join(chunk.text for chunk in chunks) == "ok"
    assert calls["n"] == 2


def test_non_retryable_status_raises():
    def handler(request):
        return httpx.Response(400, content=b'{"error": "bad"}')

    with pytest.raises(LLMError) as excinfo:
        collect(make_client(handler))
    assert excinfo.value.retryable is False
    assert excinfo.value.code == "upstream_rejected"


def test_retryable_status_exhausts_and_raises():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500, content=b"{}")

    with pytest.raises(LLMError) as excinfo:
        collect(make_client(handler, max_retries=2))
    assert excinfo.value.retryable is True
    assert calls["n"] == 3
