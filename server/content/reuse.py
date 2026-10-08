from dataclasses import dataclass

from core.constants import PROMPT_VERSION

from .models import ContentVariant, LookupLayer


@dataclass(frozen=True)
class LookupResult:
    variant: ContentVariant | None
    layer: str

    @property
    def hit(self):
        return self.variant is not None


def find_variant(
    *,
    concept,
    kind,
    lens_bucket,
    context_fingerprint="",
    prompt_version=PROMPT_VERSION,
):
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
