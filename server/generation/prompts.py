"""Prompt construction for generation.

Pure module: no Django, no I/O, no vendor SDK. It only turns
(lens, kind, text) into the messages a model receives, so it is fully
unit-testable and the same on every request.
"""

from core.constants import normalize_lens

ANCHOR_RULE = (
    "Wrap between 3 and 6 short, self-contained concepts in the answer with "
    "double asterisks, like **Rayleigh scattering**. These markers are "
    "branch points a reader can open on their own, so mark noun phrases and "
    "terms worth a separate explanation, never whole sentences."
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
        "Assume an expert reader; use precise terminology and skip basic "
        "definitions."
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
    "define": "Give a short, precise definition.",
    "ask": "Answer the reader's follow-up question about the passage.",
}


def build_system_prompt(lens, kind):
    """Return the lens- and kind-aware system prompt for a generation request."""
    lens = normalize_lens(lens)
    sections = [
        "You are Qriously, an explanation engine inside a branching "
        "learning reader.",
        KIND_GUIDANCE.get(kind, KIND_GUIDANCE["root"]),
        FAMILIARITY_GUIDANCE[lens["familiarity"]],
        DEPTH_GUIDANCE[lens["depth"]],
        STYLE_GUIDANCE[lens["style"]],
        GOAL_GUIDANCE[lens["goal"]],
        ANCHOR_RULE,
        TRUST_RULE,
    ]
    return "\n".join(sections)


def build_user_prompt(*, text, kind, context=None):
    lines = [f"Explain: {text}"]
    if context:
        lines.append(f"Context this came from: {context}")
    return "\n".join(lines)


def build_messages(*, text, kind, lens, context=None):
    user = build_user_prompt(text=text, kind=kind, context=context)
    return [
        {"role": "system", "content": build_system_prompt(lens, kind)},
        {"role": "user", "content": user},
    ]
