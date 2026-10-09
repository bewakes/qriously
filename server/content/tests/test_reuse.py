import pytest

from content.models import Kind, LookupLayer
from content.reuse import find_variant
from content.services import create_variant, upsert_concept
from content.text import context_fingerprint
from core.constants import PROMPT_VERSION

LENS = {"familiarity": "basics", "depth": "solid", "style": "plain", "goal": "curious"}
BUCKET = "basics:solid:plain:curious"


@pytest.fixture
def concept(db):
    return upsert_concept("Rayleigh scattering")


def make_variant(
    concept, *, context_key="", kind=Kind.DIVE, lens=None, version=PROMPT_VERSION
):
    return create_variant(
        concept=concept,
        kind=kind,
        lens=lens or LENS,
        title="title",
        body="body",
        context_key=context_key,
        prompt_version=version,
    )


def lookup(concept, **overrides):
    params = {
        "concept": concept,
        "kind": Kind.DIVE,
        "lens_bucket": BUCKET,
        "context_fingerprint": "",
    }
    params.update(overrides)
    return find_variant(**params)


@pytest.mark.django_db
def test_exact_hit_matches_context(concept):
    variant = make_variant(concept, context_key="why is the sky blue")
    result = lookup(
        concept,
        context_fingerprint=context_fingerprint("why is the sky blue"),
    )
    assert result.hit
    assert result.variant == variant
    assert result.layer == LookupLayer.EXACT


@pytest.mark.django_db
def test_broadened_hit_drops_context(concept):
    variant = make_variant(concept, context_key="why is the sky blue")
    result = lookup(concept, context_fingerprint=context_fingerprint("sunset colors"))
    assert result.hit
    assert result.variant == variant
    assert result.layer == LookupLayer.BROADENED


@pytest.mark.django_db
def test_miss_returns_generated_layer(concept):
    result = lookup(concept)
    assert not result.hit
    assert result.variant is None
    assert result.layer == LookupLayer.GENERATED


@pytest.mark.django_db
def test_prompt_version_is_part_of_the_key(concept):
    make_variant(concept, version="v1")
    assert not lookup(concept, prompt_version="v2").hit


@pytest.mark.django_db
def test_lens_bucket_is_part_of_the_key(concept):
    make_variant(concept)
    assert not lookup(concept, lens_bucket="new:quick:plain:curious").hit


@pytest.mark.django_db
def test_kind_is_part_of_the_key(concept):
    make_variant(concept, kind=Kind.DIVE)
    assert not lookup(concept, kind=Kind.ELI5).hit


@pytest.mark.django_db
def test_concept_is_part_of_the_key(concept):
    other = upsert_concept("The photoelectric effect")
    make_variant(concept)
    assert not lookup(other).hit
