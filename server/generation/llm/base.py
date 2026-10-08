from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, TypeAlias

Message: TypeAlias = dict[str, str]


@dataclass(frozen=True)
class StreamChunk:
    text: str = ""
    tokens_in: int | None = None
    tokens_out: int | None = None
    finish_reason: str | None = None


class LLMClient(Protocol):
    model: str

    def stream(
        self, messages: list[Message], *, model: str | None = None
    ) -> AsyncIterator[StreamChunk]: ...
