import os

from .base import LLMClient, StreamChunk
from .deepseek import DEFAULT_BASE_URL, DeepSeekClient
from .errors import LLMError

__all__ = [
    "DEFAULT_BASE_URL",
    "DeepSeekClient",
    "LLMClient",
    "LLMError",
    "StreamChunk",
    "get_client",
]


def get_client() -> LLMClient:
    return DeepSeekClient(
        os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url=os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL,
    )
