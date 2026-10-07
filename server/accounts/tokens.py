import hashlib
import secrets


def generate_token():
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
