"""Decode OpenAI-compatible streaming payloads.

Pure module: no Django, no I/O. The HTTP/SSE framing lives in
``deepseek.py``; this module only knows the JSON shape of a chat-completion
chunk, which is what makes it easy to unit test.
"""

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

    TODO(you): implement.

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

    See ``generation/tests/test_sse.py``; ``pytest generation`` goes green once
    this and the client tests pass.
    """
    raise NotImplementedError("decode_chunk is yours to implement")
