from core.constants import DEFAULT_LENS, lens_bucket, normalize_lens


def test_normalize_lens_fills_defaults():
    assert normalize_lens(None) == DEFAULT_LENS
    assert normalize_lens({}) == DEFAULT_LENS


def test_normalize_lens_keeps_valid_values():
    lens = normalize_lens({"depth": "deep", "style": "technical"})
    assert lens["depth"] == "deep"
    assert lens["style"] == "technical"
    assert lens["familiarity"] == "basics"


def test_normalize_lens_ignores_invalid_values():
    lens = normalize_lens({"depth": "galaxy", "goal": "nope"})
    assert lens["depth"] == "solid"
    assert lens["goal"] == "curious"


def test_lens_bucket_is_stable_and_ordered():
    bucket = lens_bucket({"familiarity": "expert", "depth": "deep", "style": "analogy"})
    assert bucket == "expert:deep:analogy:curious"
    assert lens_bucket(None) == "basics:solid:plain:curious"
