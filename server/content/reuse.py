from dataclasses import dataclass

from core.constants import PROMPT_VERSION

from .models import Concept, ContentVariant, LookupLayer


@dataclass(frozen=True)
class LookupResult:
    variant: ContentVariant | None
    layer: str

    @property
    def hit(self) -> bool:
        return self.variant is not None


def find_variant(
    *,
    concept: Concept,
    kind: str,
    lens_bucket: str,
    context_fingerprint: str = "",
    prompt_version: str = PROMPT_VERSION,
) -> LookupResult:
    candidates = ContentVariant.objects.filter(
        concept=concept,
        kind=kind,
        lens_bucket=lens_bucket,
        prompt_version=prompt_version,
    )
    exact = candidates.filter(context_fingerprint=context_fingerprint).first()
    if exact is not None:
        return LookupResult(variant=exact, layer=LookupLayer.EXACT)
    broadened = candidates.first()
    if broadened is not None:
        return LookupResult(variant=broadened, layer=LookupLayer.BROADENED)
    return LookupResult(variant=None, layer=LookupLayer.GENERATED)
