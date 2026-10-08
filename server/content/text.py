import hashlib
import re

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
_WORDS = re.compile(r"[A-Za-z0-9]+")

DEFAULT_READING_WPM = 220
FINGERPRINT_LENGTH = 16


def normalize(text):
    text = (text or "").strip().lower()
    text = _PUNCTUATION.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def context_fingerprint(parent_key):
    if not parent_key:
        return ""
    digest = hashlib.sha256(parent_key.encode("utf-8")).hexdigest()
    return digest[:FINGERPRINT_LENGTH]


def estimate_read_seconds(body, wpm=DEFAULT_READING_WPM):
    words = len(_WORDS.findall(body or ""))
    if words == 0:
        return 0
    return max(1, round(words / wpm * 60))
