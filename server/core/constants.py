from collections.abc import Mapping

DEFAULT_MODEL = "deepseek-flash"

PROMPT_VERSION = "v4"

LLM_TIMEOUT_SECONDS = 60
LLM_MAX_RETRIES = 2
LLM_RETRY_BACKOFF_SECONDS = 0.5

MODEL_PRICE = {
    "deepseek-flash": {
        "input_per_1k_micros": 140,
        "output_per_1k_micros": 280,
    },
}

SIGNUP_GRANT = 5000

CACHE_HIT_RATIO = 0.25

BRANCH_CONTEXT_MAX_CHARS = 800

DEPTH_MULTIPLIER = {
    "quick": 0.7,
    "solid": 1.0,
    "deep": 1.6,
}

BASE_COST = {
    "root": 15,
    "followup": 15,
    "dive": 12,
    "ask": 10,
    "eli5": 6,
    "example": 6,
    "define": 5,
}

DEFAULT_COST = 10

SCREENING_POLICY = "allow_all"

DEFAULT_LENS = {
    "familiarity": "basics",
    "depth": "solid",
    "style": "plain",
    "goal": "curious",
}

LENS_DIMENSIONS = {
    "familiarity": ["new", "basics", "expert"],
    "depth": ["quick", "solid", "deep"],
    "style": ["plain", "analogy", "technical"],
    "goal": ["curious", "project", "exam"],
}


def normalize_lens(lens: Mapping[str, str] | None) -> dict[str, str]:
    merged = dict(DEFAULT_LENS)
    for key, allowed in LENS_DIMENSIONS.items():
        value = (lens or {}).get(key)
        if value in allowed:
            merged[key] = value
    return merged


def lens_bucket(lens: Mapping[str, str] | None) -> str:
    normalized = normalize_lens(lens)
    return ":".join(
        normalized[dim] for dim in ("familiarity", "depth", "style", "goal")
    )


def lens_vector(lens: Mapping[str, str] | None) -> list[float]:
    normalized = normalize_lens(lens)
    vector = []
    for dim in ("familiarity", "depth", "style", "goal"):
        values = LENS_DIMENSIONS[dim]
        index = values.index(normalized[dim])
        last = len(values) - 1
        vector.append(0.0 if last == 0 else round(2 * index / last - 1, 6))
    return vector
