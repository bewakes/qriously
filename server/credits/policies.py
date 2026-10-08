import math

from core.constants import BASE_COST, CACHE_HIT_RATIO, DEFAULT_COST, DEPTH_MULTIPLIER


def price(kind: str, depth: str = "solid", cache_hit: bool = False) -> int:
    base = BASE_COST.get(kind, DEFAULT_COST)
    multiplier = DEPTH_MULTIPLIER.get(depth, 1.0)
    ratio = CACHE_HIT_RATIO if cache_hit else 1.0
    return math.ceil(base * multiplier * ratio)
