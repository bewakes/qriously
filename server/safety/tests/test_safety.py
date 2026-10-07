import pytest

from safety.decision import Decision, Outcome
from safety.policies import AllowAllPolicy
from safety.registry import get_policy


def test_allow_all_allows_everything():
    decision = AllowAllPolicy().check("how do I bake bread?")
    assert isinstance(decision, Decision)
    assert decision.allowed is True
    assert decision.outcome is Outcome.ALLOW


def test_registry_defaults_to_configured_policy():
    assert get_policy().name == "allow_all"


def test_registry_rejects_unknown_policy():
    with pytest.raises(ValueError):
        get_policy("does_not_exist")
