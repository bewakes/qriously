import hashlib
import re

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
_WORDS = re.compile(r"[A-Za-z0-9]+")
_MARKERS = re.compile(r"\*\*")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
_ELLIPSIS = "\u2026"

DEFAULT_READING_WPM = 220
FINGERPRINT_LENGTH = 16


def normalize(text: str | None) -> str:
    cleaned = (text or "").strip().lower()
    cleaned = _PUNCTUATION.sub(" ", cleaned)
    return _WHITESPACE.sub(" ", cleaned).strip()


def context_fingerprint(parent_key: str | None) -> str:
    if not parent_key:
        return ""
    digest = hashlib.sha256(parent_key.encode("utf-8")).hexdigest()
    return digest[:FINGERPRINT_LENGTH]


def estimate_read_seconds(body: str | None, wpm: int = DEFAULT_READING_WPM) -> int:
    words = len(_WORDS.findall(body or ""))
    if words == 0:
        return 0
    return max(1, round(words / wpm * 60))


def context_window(body: str | None, span: str | None, budget: int) -> str | None:
    """Return a bounded slice of ``body`` around ``span`` for prompt context.

    Anchor ``**`` markers are stripped and the selected phrase is located with
    whitespace-tolerant, case-insensitive matching. The surrounding text is
    snapped to sentence boundaries and capped near ``budget`` characters, so a
    branch carries the passage it needs rather than the whole parent body.
    Returns a leading slice when the span cannot be located, and ``None`` when
    the body is empty.
    """
    text = _MARKERS.sub("", body or "")
    if not text.strip():
        return None

    match = _locate(text, span)
    if match is None:
        trimmed = text.strip()
        clipped = len(trimmed) > budget
        return trimmed[:budget].rstrip() + (_ELLIPSIS if clipped else "")

    start, end = match.span()
    room = max(0, budget - (end - start))
    before, after = room // 3, room - room // 3
    lo, hi = max(0, start - before), min(len(text), end + after)
    window = text[_snap_start(text, lo) : _snap_end(text, hi)].strip()
    if len(window) > budget:
        window = text[lo:hi].strip()
    return window


def _locate(text: str, span: str | None) -> re.Match | None:
    parts = (span or "").split()
    if not parts:
        return None
    pattern = r"\s+".join(re.escape(part) for part in parts)
    return re.search(pattern, text, re.IGNORECASE)


def _snap_start(text: str, index: int) -> int:
    boundary = 0
    for found in _SENTENCE_BREAK.finditer(text[:index]):
        boundary = found.end()
    paragraph = text.rfind("\n\n", 0, index)
    return max(boundary, paragraph + 2 if paragraph != -1 else 0)


def _snap_end(text: str, index: int) -> int:
    found = _SENTENCE_BREAK.search(text, index)
    if found is not None:
        return found.end()
    paragraph = text.find("\n\n", index)
    return paragraph + 2 if paragraph != -1 else len(text)
