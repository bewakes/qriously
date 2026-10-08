import asyncio
import json
from collections.abc import AsyncIterator

import httpx

from core.constants import (
    DEFAULT_MODEL,
    LLM_MAX_RETRIES,
    LLM_RETRY_BACKOFF_SECONDS,
    LLM_TIMEOUT_SECONDS,
)

from .base import StreamChunk
from .errors import LLMError
from .sse import DONE_SENTINEL, ChatCompletionChunk, decode_chunk, extract_data

DEFAULT_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient:
    """OpenAI-compatible streaming client for DeepSeek, behind ``LLMClient``."""

    def __init__(
        self,
        api_key,
        *,
        base_url=DEFAULT_BASE_URL,
        model=DEFAULT_MODEL,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=LLM_MAX_RETRIES,
        backoff=LLM_RETRY_BACKOFF_SECONDS,
        http_client=None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self._http_client = http_client

    @property
    def endpoint(self):
        return f"{self.base_url}/chat/completions"

    async def stream(
        self, messages, *, model: str | None = None
    ) -> AsyncIterator[StreamChunk]:
        model = model or self.model
        attempt = 0
        while True:
            emitted = False
            try:
                async for chunk in self._stream_once(messages, model):
                    emitted = True
                    yield chunk
                return
            except LLMError as exc:
                if emitted or not exc.retryable or attempt >= self.max_retries:
                    raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if emitted or attempt >= self.max_retries:
                    raise LLMError(
                        "upstream_unreachable", str(exc), retryable=True
                    ) from exc
            attempt += 1
            await asyncio.sleep(self.backoff * attempt)

    async def _stream_once(self, messages, model):
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        client = self._http_client or httpx.AsyncClient(timeout=self.timeout)
        owns_client = self._http_client is None
        try:
            async with client.stream(
                "POST", self.endpoint, json=payload, headers=headers
            ) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise self._error_for(response.status_code)
                async for line in response.aiter_lines():
                    data = extract_data(line)
                    if data is None:
                        continue
                    if data == DONE_SENTINEL:
                        break
                    payload: ChatCompletionChunk = json.loads(data)
                    chunk = decode_chunk(payload)
                    if chunk is not None:
                        yield chunk
        except httpx.TimeoutException as exc:
            raise LLMError("upstream_timeout", str(exc), retryable=True) from exc
        except httpx.TransportError as exc:
            raise LLMError("upstream_unreachable", str(exc), retryable=True) from exc
        finally:
            if owns_client:
                await client.aclose()

    @staticmethod
    def _error_for(status):
        if status == 429:
            return LLMError(
                "upstream_rate_limited", "DeepSeek rate limit", retryable=True
            )
        if status >= 500:
            return LLMError(
                "upstream_error", f"DeepSeek returned {status}", retryable=True
            )
        return LLMError(
            "upstream_rejected", f"DeepSeek returned {status}", retryable=False
        )
