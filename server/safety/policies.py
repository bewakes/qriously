from typing import Protocol

from .decision import Decision, Outcome


class ScreeningPolicy(Protocol):
    name: str

    def check(self, text: str, *, context: dict | None = None) -> Decision: ...


class AllowAllPolicy:
    name = "allow_all"

    def check(self, text: str, *, context: dict | None = None) -> Decision:
        return Decision(outcome=Outcome.ALLOW, provider=self.name)
