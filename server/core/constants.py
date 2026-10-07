DEFAULT_MODEL = "deepseek-flash"

PROMPT_VERSION = "v1"

MODEL_PRICE = {
    "deepseek-flash": {
        "input_per_1k_micros": 140,
        "output_per_1k_micros": 280,
    },
}

SIGNUP_GRANT = 5000

CACHE_HIT_RATIO = 0.25

DEPTH_MULTIPLIER = {
    "quick": 0.7,
    "solid": 1.0,
    "deep": 1.6,
}

BASE_COST = {
    "root": 15,
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


def normalize_lens(lens):
    merged = dict(DEFAULT_LENS)
    for key, allowed in LENS_DIMENSIONS.items():
        value = (lens or {}).get(key)
        if value in allowed:
            merged[key] = value
    return merged


def lens_bucket(lens):
    lens = normalize_lens(lens)
    return ":".join(lens[dim] for dim in ("familiarity", "depth", "style", "goal"))
