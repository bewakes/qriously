import pytest
from django.core.management import call_command

from content.models import Concept, ContentVariant
from content.seeds import SEED_VARIANTS


@pytest.mark.django_db
def test_seed_content_is_idempotent():
    call_command("seed_content")
    call_command("seed_content")
    assert ContentVariant.objects.count() == len(SEED_VARIANTS)
    assert Concept.objects.count() == 2
