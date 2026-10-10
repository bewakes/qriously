from core.constants import (
    DEFAULT_LENS,
    MAX_OUTPUT_TOKENS,
    lens_bucket,
    lens_vector,
    max_output_tokens,
    normalize_lens,
)


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


def test_lens_vector_is_normalized_and_ordered():
    assert lens_vector(None) == [0.0, 0.0, -1.0, -1.0]
    lens = {"familiarity": "new", "depth": "deep", "style": "technical"}
    assert lens_vector(lens) == [-1.0, 1.0, 1.0, -1.0]


def test_lens_vector_ignores_invalid_values():
    assert lens_vector({"depth": "galaxy"}) == lens_vector(None)


def test_fixed_shape_kinds_ignore_depth():
    assert max_output_tokens("define", "deep") == MAX_OUTPUT_TOKENS["define"]
    assert max_output_tokens("eli5", "quick") == MAX_OUTPUT_TOKENS["eli5"]


def test_open_ended_kinds_scale_with_depth():
    assert max_output_tokens("root", "solid") == MAX_OUTPUT_TOKENS["root"]
    assert max_output_tokens("dive", "deep") > max_output_tokens("dive", "quick")


def test_unknown_kind_uses_default():
    assert max_output_tokens("mystery", "solid") == 700
