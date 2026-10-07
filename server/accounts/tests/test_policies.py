from accounts.policies import generate_token, hash_token


def test_hash_is_deterministic_and_not_identity():
    raw = "abc"
    assert hash_token(raw) == hash_token(raw)
    assert hash_token(raw) != raw
    assert len(hash_token(raw)) == 64


def test_generate_token_returns_raw_and_matching_hash():
    raw, hashed = generate_token()
    assert raw != hashed
    assert hashed == hash_token(raw)


def test_generate_token_is_unique():
    assert generate_token()[0] != generate_token()[0]
