from content.text import context_fingerprint, estimate_read_seconds, normalize


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
