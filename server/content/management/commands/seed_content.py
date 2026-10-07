from django.core.management.base import BaseCommand

from content import services
from content.seeds import SEED_VARIANTS
from core.constants import DEFAULT_MODEL, PROMPT_VERSION


class Command(BaseCommand):
    help = "Seed a few reusable content variants so cache hits are demonstrable."

    def handle(self, *args, **options):
        created = 0
        for seed in SEED_VARIANTS:
            concept = services.upsert_concept(
                seed["text"], kind_hint=seed.get("kind_hint")
            )
            _, was_created = services.get_or_create_variant(
                concept=concept,
                kind=seed["kind"],
                lens=seed["lens"],
                context_key=seed.get("context_key", ""),
                prompt_version=seed.get("prompt_version", PROMPT_VERSION),
                title=seed["title"],
                body=seed["body"],
                model=seed.get("model", DEFAULT_MODEL),
                citations=seed.get("citations"),
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"seeded {created} new variant(s); {len(SEED_VARIANTS)} in the set"
            )
        )
