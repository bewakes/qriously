import pytest

from content.models import Concept, ContentVariant, Kind, LookupLayer
from content.services import (
    create_variant,
    get_or_create_variant,
    record_concept_link,
    resolve_variant,
    upsert_concept,
)
from core.constants import PROMPT_VERSION

LENS = {"familiarity": "basics", "depth": "solid", "style": "plain", "goal": "curious"}


def make_variant(
    concept, *, kind=Kind.DIVE, context_key="", version=PROMPT_VERSION, body="body"
):
    return create_variant(
        concept=concept,
        kind=kind,
        lens=LENS,
        title="title",
        body=body,
        context_key=context_key,
        prompt_version=version,
    )


@pytest.mark.django_db
def test_upsert_concept_normalizes_and_dedupes():
    first = upsert_concept("Why is the sky blue?")
    second = upsert_concept("  why is the SKY blue  ")
    assert first.pk == second.pk
    assert Concept.objects.count() == 1
    assert first.text == "Why is the sky blue?"


@pytest.mark.django_db
def test_upsert_concept_rejects_empty():
    with pytest.raises(ValueError):
        upsert_concept("!!!")


@pytest.mark.django_db
def test_create_variant_derives_bucket_vector_and_read_time():
    concept = upsert_concept("Rayleigh scattering")
    variant = make_variant(concept, body=" ".join(["word"] * 220))
    assert variant.lens_bucket == "basics:solid:plain:curious"
    assert variant.lens_vector == [0.0, 0.0, -1.0, -1.0]
    assert variant.est_read_seconds == 60
    assert variant.prompt_version == PROMPT_VERSION


@pytest.mark.django_db
def test_get_or_create_variant_is_idempotent():
    concept = upsert_concept("Rayleigh scattering")
    first, created_first = get_or_create_variant(
        concept=concept, kind=Kind.DIVE, lens=LENS, title="t", body="b"
    )
    second, created_second = get_or_create_variant(
        concept=concept, kind=Kind.DIVE, lens=LENS, title="t", body="b"
    )
    assert created_first is True
    assert created_second is False
    assert first.pk == second.pk
    assert ContentVariant.objects.count() == 1


@pytest.mark.django_db
def test_new_prompt_version_does_not_mutate_old_variant():
    concept = upsert_concept("Rayleigh scattering")
    old = make_variant(concept, version="v1")
    new = make_variant(concept, version="v2", body="different")
    assert old.pk != new.pk
    old.refresh_from_db()
    assert old.body == "body"
    assert ContentVariant.objects.count() == 2


@pytest.mark.django_db
def test_variants_are_immutable():
    concept = upsert_concept("Rayleigh scattering")
    variant = make_variant(concept)
    variant.title = "changed"
    with pytest.raises(ValueError):
        variant.save()


@pytest.mark.django_db
def test_record_concept_link_increments_weight():
    parent = upsert_concept("Why is the sky blue?")
    child = upsert_concept("Rayleigh scattering")
    first = record_concept_link(parent, child, Kind.DIVE)
    second = record_concept_link(parent, child, Kind.DIVE)
    assert first.pk == second.pk
    second.refresh_from_db()
    assert second.weight == 2


@pytest.mark.django_db
def test_resolve_variant_miss_then_hit():
    _, miss = resolve_variant(text="Rayleigh scattering", kind=Kind.DIVE, lens=LENS)
    assert miss.layer == LookupLayer.GENERATED

    concept = upsert_concept("Rayleigh scattering")
    make_variant(concept)

    _, hit = resolve_variant(text="Rayleigh scattering", kind=Kind.DIVE, lens=LENS)
    assert hit.layer == LookupLayer.EXACT
    assert hit.variant is not None
