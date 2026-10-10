from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class AuthError(Exception):
    """Raised when a credential cannot be verified (framework-free)."""


@dataclass(frozen=True)
class Identity:
    email: str
    display_name: str = ""
    provider: str = ""


@runtime_checkable
class AuthProvider(Protocol):
    name: str
    requires_code: bool

    def start(self, email: str) -> str | None:
        """Begin a login. Returns a code to deliver out-of-band, or None."""

    def verify(self, email: str, credential: str) -> Identity:
        """Turn a credential into an Identity, or raise ``AuthError``."""


class InMemoryCodeStore:
    """Ephemeral one-time codes, keyed by normalized email."""

    def __init__(self, ttl_seconds: int, length: int) -> None:
        self._ttl = ttl_seconds
        self._length = length
        self._codes: dict[str, tuple[str, float]] = {}

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def issue(self, email: str) -> str:
        code = "".join(
            secrets.choice("0123456789") for _ in range(self._length)
        )
        self._codes[self._key(email)] = (code, time.monotonic() + self._ttl)
        return code

    def verify(self, email: str, code: str) -> bool:
        key = self._key(email)
        entry = self._codes.get(key)
        if entry is None:
            return False
        expected, expires = entry
        if time.monotonic() > expires:
            self._codes.pop(key, None)
            return False
        if not secrets.compare_digest(expected, code.strip()):
            return False
        self._codes.pop(key, None)
        return True


class DevCodeProvider:
    """Local/offline login: a one-time code printed to the server console."""

    name = "dev"
    requires_code = True

    def __init__(self, store: InMemoryCodeStore) -> None:
        self._store = store

    def start(self, email: str) -> str:
        if not email or "@" not in email:
            raise AuthError("invalid_email")
        return self._store.issue(email)

    def verify(self, email: str, credential: str) -> Identity:
        if not self._store.verify(email, credential):
            raise AuthError("invalid_code")
        return Identity(email=email.strip().lower(), provider=self.name)


class GoogleProvider:
    """Placeholder for Google ID-token verification (same interface)."""

    name = "google"
    requires_code = False

    def __init__(self, client_id: str = "") -> None:
        self._client_id = client_id

    def start(self, email: str) -> None:
        return None

    def verify(self, email: str, credential: str) -> Identity:
        raise AuthError("provider_not_configured")
