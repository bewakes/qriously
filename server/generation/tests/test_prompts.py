from core.constants import DEFAULT_LENS
from generation.prompts import (
    ANCHOR_RULE,
    TRUST_RULE,
    build_messages,
    build_system_prompt,
)

LENS = {"familiarity": "basics", "depth": "solid", "style": "plain", "goal": "curious"}


def test_system_prompt_is_deterministic():
    assert build_system_prompt(LENS, "dive") == build_system_prompt(LENS, "dive")


def test_system_prompt_includes_anchor_and_trust_rules():
    prompt = build_system_prompt(LENS, "dive")
    assert ANCHOR_RULE in prompt
    assert TRUST_RULE in prompt


def test_each_lens_dimension_changes_the_prompt():
    base = build_system_prompt(LENS, "dive")
    alternatives = {
        "familiarity": "expert",
        "depth": "deep",
        "style": "analogy",
        "goal": "exam",
    }
    for dimension, value in alternatives.items():
        changed = {**LENS, dimension: value}
        assert build_system_prompt(changed, "dive") != base, dimension


def test_kind_changes_the_prompt():
    assert build_system_prompt(LENS, "dive") != build_system_prompt(LENS, "eli5")


def test_missing_or_invalid_lens_falls_back_to_defaults():
    default = build_system_prompt(DEFAULT_LENS, "dive")
    assert build_system_prompt({}, "dive") == default
    assert build_system_prompt({"depth": "galaxy"}, "dive") == default


def test_build_messages_shape():
    messages = build_messages(text="Rayleigh scattering", kind="dive", lens=LENS)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "Rayleigh scattering" in messages[1]["content"]
    assert messages[0]["content"] == build_system_prompt(LENS, "dive")
