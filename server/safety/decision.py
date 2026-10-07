from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"


@dataclass(frozen=True)
class Decision:
    outcome: Outcome
    category: str | None = None
    score: float | None = None
    provider: str = ""

    @property
    def allowed(self) -> bool:
        return self.outcome is Outcome.ALLOW
