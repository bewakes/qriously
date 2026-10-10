from content.text import (
    context_fingerprint,
    context_window,
    estimate_read_seconds,
    normalize,
)


def test_normalize_lowercases_strips_punctuation_and_collapses_space():
    assert normalize("  Why is the SKY blue?! ") == "why is the sky blue"
    assert normalize("Rayleigh\u2014scattering.") == "rayleigh scattering"


def test_normalize_handles_empty():
    assert normalize(None) == ""
    assert normalize("   ") == ""
    assert normalize("!!!") == ""


def test_context_fingerprint_is_bounded_and_deterministic():
    assert context_fingerprint("") == ""
    assert context_fingerprint(None) == ""
    first = context_fingerprint("why is the sky blue")
    assert first == context_fingerprint("why is the sky blue")
    assert len(first) == 16
    assert first != context_fingerprint("why is the sky red")


def test_estimate_read_seconds():
    assert estimate_read_seconds("") == 0
    assert estimate_read_seconds("word") == 1
    assert estimate_read_seconds(" ".join(["word"] * 220)) == 60


BODY = (
    "Fees are quoted in gwei. The base fee is **destroyed**, burned forever. "
    "The practical upshot: fees swing wildly. A quiet Sunday costs a dollar; "
    "an NFT drop pushes the same transaction to fifty."
)


def test_context_window_returns_none_for_empty_body():
    assert context_window("", "fees", 800) is None
    assert context_window(None, "fees", 800) is None


def test_context_window_keeps_the_span_and_strips_markers():
    window = context_window(BODY, "fees swing wildly", 800)
    assert window is not None
    assert "fees swing wildly" in window
    assert "**" not in window


def test_context_window_matches_across_whitespace_and_case():
    window = context_window(BODY, "FEES\n  swing   WILDLY", 800)
    assert window is not None
    assert "fees swing wildly" in window


def test_context_window_is_bounded():
    long_body = ". ".join([f"sentence number {i} here" for i in range(200)])
    window = context_window(long_body, "sentence number 100 here", 120)
    assert window is not None
    assert len(window) <= 120 + 2
    assert "sentence number 100 here" in window


def test_context_window_falls_back_when_span_is_missing():
    window = context_window(BODY, "no such phrase anywhere", 800)
    assert window is not None
    assert window.startswith("Fees are quoted in gwei.")
