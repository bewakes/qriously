from credits.policies import price


def test_price_uses_base_and_depth():
    assert price("dive", "solid") == 12
    assert price("dive", "quick") == 9
    assert price("dive", "deep") == 20


def test_price_unknown_kind_uses_default():
    assert price("mystery", "solid") == 10


def test_cache_hit_is_a_fraction_and_never_free():
    assert price("dive", "solid", cache_hit=True) == 3
    assert price("define", "solid", cache_hit=True) == 2
    assert price("define", "solid", cache_hit=True) > 0


def test_price_rounds_up():
    assert price("define", "quick", cache_hit=True) == 1
