"""Decode OpenAI-compatible streaming payloads (pure: no Django, no I/O)."""

from typing import TypedDict

from .base import StreamChunk

DATA_PREFIX = "data:"
DONE_SENTINEL = "[DONE]"


class Delta(TypedDict, total=False):
    content: str


class Choice(TypedDict, total=False):
    index: int
    delta: Delta
    finish_reason: str | None


class Usage(TypedDict, total=False):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChunk(TypedDict, total=False):
    """One decoded OpenAI-compatible streamed chunk."""

    id: str
    object: str
    choices: list[Choice]
    usage: Usage | None


def extract_data(line: str) -> str | None:
    """Return the payload string of an SSE ``data:`` line, else ``None``."""
    if not line or not line.startswith(DATA_PREFIX):
        return None
    return line[len(DATA_PREFIX) :].strip()


def decode_chunk(payload: ChatCompletionChunk) -> StreamChunk | None:
    """Map one parsed chat-completion payload to a ``StreamChunk`` or ``None``.

    Contract:
    - ``payload`` is a :class:`ChatCompletionChunk` (a decoded JSON object).
    - Read delta text from ``choices[0]["delta"]["content"]`` and the finish
      reason from ``choices[0]["finish_reason"]``. ``choices`` may be empty
      (e.g. the final usage-only chunk).
    - Read token usage from ``payload["usage"]`` as ``prompt_tokens`` and
      ``completion_tokens`` (present only when requested, on the final chunk).
    - Return a ``StreamChunk`` carrying whichever of ``text`` /
      ``finish_reason`` / ``tokens_in`` / ``tokens_out`` are present.
    - Return ``None`` when the payload carries nothing (no text, no finish
      reason, no usage) so callers can skip it.
    - Be tolerant of missing keys; never raise on a partial payload.
    """
    delta: Delta = {}
    finish_reason: str | None = None
    choices = payload.get("choices") or []
    if choices:
        choice = choices[0]
        delta = choice.get("delta") or {}
        finish_reason = choice.get("finish_reason")

    usage: Usage = payload.get("usage") or {}
    tokens_in = usage.get("prompt_tokens")
    tokens_out = usage.get("completion_tokens")
    text = delta.get("content") or ""

    if not text and finish_reason is None and tokens_in is None and tokens_out is None:
        return None
    return StreamChunk(
        text=text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        finish_reason=finish_reason,
    )
