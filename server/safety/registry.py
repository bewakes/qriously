from core.constants import SCREENING_POLICY

from .policies import AllowAllPolicy, ScreeningPolicy

_POLICIES: dict[str, type[ScreeningPolicy]] = {
    AllowAllPolicy.name: AllowAllPolicy,
}


def get_policy(name: str | None = None) -> ScreeningPolicy:
    key = name or SCREENING_POLICY
    try:
        return _POLICIES[key]()
    except KeyError as exc:
        raise ValueError(f"unknown screening policy: {key}") from exc
