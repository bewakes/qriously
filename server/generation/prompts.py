"""Build model messages from a lens and kind (pure: no Django, no I/O)."""

from collections.abc import Mapping

from core.constants import normalize_lens

ANCHOR_RULE = (
    "Wrap between 3 and 6 short, self-contained concepts in the answer with "
    "double asterisks, like **Rayleigh scattering**. These markers are "
    "branch points a reader can open on their own, so mark noun phrases and "
    "terms worth a separate explanation, never whole sentences."
)

DEFINE_ANCHOR_RULE = (
    "If a term genuinely merits its own explanation, wrap it in double "
    "asterisks; a short definition may contain no markers at all."
)

DEFINE_LENGTH_RULE = (
    "Keep the definition short: one or two sentences that state what the term "
    "is. This holds regardless of the reader's depth preference or how long the "
    "surrounding answer is — a definition is never an essay about the term."
)

TRUST_RULE = (
    "Do not invent citations and do not claim that any source has been "
    "checked. When you are unsure, say so plainly rather than fabricating a "
    "reference."
)

FAMILIARITY_GUIDANCE = {
    "new": "Assume no prior knowledge; avoid jargon and define any term you use.",
    "basics": (
        "Assume a curious beginner; use everyday language and explain jargon "
        "the first time it appears."
    ),
    "expert": (
        "Assume an expert reader; use precise terminology and skip basic definitions."
    ),
}

DEPTH_GUIDANCE = {
    "quick": "Be brief: two or three sentences covering one idea.",
    "solid": "Give a solid, self-contained answer of a few short paragraphs.",
    "deep": "Go deep: cover mechanism, nuance and edge cases in detail.",
}

STYLE_GUIDANCE = {
    "plain": "Write in plain, direct prose.",
    "analogy": "Lead with one concrete analogy and tie the explanation back to it.",
    "technical": "Write precisely and technically, using exact terms.",
}

GOAL_GUIDANCE = {
    "curious": "Satisfy curiosity: make the why vivid and interesting.",
    "project": "Be practical: emphasise what to do and how to apply it.",
    "exam": "Be exam-focused: surface definitions and points likely to be tested.",
}

KIND_GUIDANCE = {
    "root": "Answer the reader's opening question.",
    "dive": "Explain the highlighted phrase in its own right, in context.",
    "eli5": "Explain it as you would to a bright five-year-old.",
    "example": "Explain mainly through concrete examples.",
    "define": "Give a short, precise definition with no preamble.",
    "ask": "Answer the reader's follow-up question about the passage.",
}


def build_system_prompt(lens: Mapping[str, str] | None, kind: str) -> str:
    """Return the lens- and kind-aware system prompt for a generation request."""
    normalized = normalize_lens(lens)
    is_define = kind == "define"
    sections = [
        "You are Qriously, an explanation engine inside a learning reader.",
        KIND_GUIDANCE.get(kind, KIND_GUIDANCE["root"]),
        FAMILIARITY_GUIDANCE[normalized["familiarity"]],
        DEFINE_LENGTH_RULE if is_define else DEPTH_GUIDANCE[normalized["depth"]],
        STYLE_GUIDANCE[normalized["style"]],
        GOAL_GUIDANCE[normalized["goal"]],
        DEFINE_ANCHOR_RULE if is_define else ANCHOR_RULE,
        TRUST_RULE,
    ]
    return "\n".join(sections)


def build_user_prompt(*, text: str, kind: str, context: str | None = None) -> str:
    lines = [f"Explain: {text}"]
    if context:
        lines.append(f"Context this came from: {context}")
    return "\n".join(lines)


def build_messages(
    *,
    text: str,
    kind: str,
    lens: Mapping[str, str] | None,
    context: str | None = None,
) -> list[dict[str, str]]:
    user = build_user_prompt(text=text, kind=kind, context=context)
    return [
        {"role": "system", "content": build_system_prompt(lens, kind)},
        {"role": "user", "content": user},
    ]
