from core.constants import DEFAULT_LENS
from generation.prompts import (
    ANCHOR_RULE,
    ELI5_LENGTH_RULE,
    REFERENCE_RULE,
    SCOPE_RULE,
    SPAN_KINDS,
    TRUST_RULE,
    build_messages,
    build_system_prompt,
    frame_line,
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


def test_ask_prompt_includes_the_passage_and_the_question():
    messages = build_messages(
        text="What is this?",
        kind="ask",
        lens=LENS,
        span_text="Rayleigh scattering",
        frame='the answer to: "Why is the sky blue?"',
    )
    user = messages[1]["content"]
    assert "Rayleigh scattering" in user
    assert "What is this?" in user
    assert user.index("Rayleigh scattering") < user.index("What is this?")
    assert 'the answer to: "Why is the sky blue?"' in user


def test_span_kind_prompt_carries_frame_passage_and_phrase():
    messages = build_messages(
        text="The practical upshot: fees swing wildly",
        kind="eli5",
        lens=LENS,
        context="A quiet Sunday might cost a dollar to send a token.",
        span_text="The practical upshot: fees swing wildly",
        frame='the answer to: "Why do Ethereum fees swing so much?"',
    )
    user = messages[1]["content"]
    assert 'This selection comes from the answer to: "Why do Ethereum fees' in user
    assert "Passage:" in user
    assert "A quiet Sunday might cost a dollar" in user
    assert "Selected phrase: The practical upshot: fees swing wildly" in user
    assert "do not re-explain the passage above" in user


def test_span_kind_prompt_without_context_still_names_the_phrase():
    messages = build_messages(
        text="gas", kind="define", lens=LENS, span_text="gas"
    )
    user = messages[1]["content"]
    assert "Selected phrase: gas" in user
    assert "Passage:" not in user


def test_scope_and_reference_rules_apply_to_span_kinds_only():
    for kind in SPAN_KINDS:
        prompt = build_system_prompt(LENS, kind)
        assert SCOPE_RULE in prompt, kind
        assert REFERENCE_RULE in prompt, kind
    for kind in ("root", "ask"):
        prompt = build_system_prompt(LENS, kind)
        assert SCOPE_RULE not in prompt, kind
        assert REFERENCE_RULE not in prompt, kind


def test_eli5_has_its_own_short_length_rule():
    assert ELI5_LENGTH_RULE in build_system_prompt(LENS, "eli5")


def test_frame_line_names_the_container_or_is_omitted():
    assert frame_line("define", "gas") == 'the definition of: "gas"'
    assert frame_line("eli5", "fees swing wildly") == (
        'the simple explanation of: "fees swing wildly"'
    )
    assert frame_line("root", "Why is the sky blue?") == (
        'the answer to: "Why is the sky blue?"'
    )
    assert frame_line("define", "") is None
    assert frame_line("unknown", "gas") is None


def test_ask_prompt_without_a_passage_falls_back_to_explain():
    messages = build_messages(text="What is this?", kind="ask", lens=LENS)
    assert messages[1]["content"] == "Explain: What is this?"
