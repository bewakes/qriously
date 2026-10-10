"""Build model messages from a lens and kind (pure: no Django, no I/O)."""

from collections.abc import Mapping

from core.constants import normalize_lens

SPAN_KINDS = frozenset({"dive", "eli5", "define", "example"})
FOLLOWUP_KINDS = frozenset({"followup"})

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

EXAMPLE_ANCHOR_RULE = (
    "Wrap only the one or two terms that genuinely merit their own explanation "
    "in double asterisks; most examples need no markers."
)

EXAMPLE_LENGTH_RULE = (
    "Answer with a markdown list of between 2 and 4 concrete examples, one per "
    "line, each starting with '- '. Keep every example to a single short "
    "sentence. Do this regardless of the reader's depth preference or how long "
    "the surrounding answer is — examples are a short list, never a paragraph."
)

ELI5_ANCHOR_RULE = (
    "Wrap only the one or two terms that genuinely merit their own explanation "
    "in double asterisks; the simplest version must not be crowded with markers."
)

ELI5_LENGTH_RULE = (
    "Give the simplest true version in three to five short sentences, using one "
    "everyday analogy. Do not introduce a term the passage has not already used, "
    "and end on the single most useful takeaway."
)

SCOPE_RULE = (
    "You are explaining one phrase the reader selected from a passage they "
    "already have in front of them. Explain only that phrase: do not restate, "
    "summarise, or re-explain the surrounding passage, and do not re-teach the "
    "topic from the beginning."
)

REFERENCE_RULE = (
    "The selected phrase may depend on the passage for its meaning — a pronoun "
    "(this, it, that) or a framing phrase such as 'the practical upshot'. "
    "Resolve what it refers to from the passage before explaining; if it stays "
    "ambiguous, say which reading you are taking. When the phrase names no "
    "subject of its own, treat it as a reference into the passage, not a "
    "standalone topic."
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
    "followup": "Answer the reader's follow-up question about this session.",
    "dive": (
        "Explain the highlighted phrase in its own right, in context — go deeper "
        "on the phrase, not on the surrounding answer."
    ),
    "eli5": "Explain the highlighted phrase as you would to a bright five-year-old.",
    "example": "Illustrate with a short list of concrete examples.",
    "define": "Give a short, precise definition with no preamble.",
    "ask": "Answer the reader's follow-up question about the passage.",
}

GROUNDING_RULE = (
    "This is a follow-up in an ongoing session. Use the session context below to "
    "interpret the question: if it refers to something the reader has already "
    "explored, answer about that. If the question is a genuinely new topic, "
    "answer it fresh — do not force a connection that is not there."
)

META_OPEN = "<<<QRIOUSLY"
META_CLOSE = ">>>"
META_RULE = (
    "After the answer, append exactly one metadata block on its own lines:\n"
    f"{META_OPEN}\n"
    "gist: one sentence summarising your answer\n"
    "summary: one or two sentences summarising the whole session so far, "
    "including this answer\n"
    f"{META_CLOSE}\n"
    "Do not refer to this block in the answer itself."
)

ACTION_VERBS = {
    "root": "opened with the question",
    "followup": "asked",
    "dive": "dived into",
    "eli5": "asked for a simpler version of",
    "example": "asked for examples of",
    "define": "asked to define",
    "ask": "asked",
}

FRAME_PHRASES = {
    "root": "the answer to",
    "dive": "a deeper dive on",
    "eli5": "the simple explanation of",
    "define": "the definition of",
    "example": "the examples of",
    "ask": "the answer to",
}


def frame_line(kind: str, title: str | None) -> str | None:
    """Describe the container a selection came from, e.g. 'the definition of: "gas"'."""
    phrase = FRAME_PHRASES.get(kind)
    title = (title or "").strip()
    if not phrase or not title:
        return None
    return f'{phrase}: "{title}"'


def build_system_prompt(lens: Mapping[str, str] | None, kind: str) -> str:
    """Return the lens- and kind-aware system prompt for a generation request."""
    normalized = normalize_lens(lens)
    length_rule, anchor_rule = _kind_rules(kind, normalized["depth"])
    sections = [
        "You are Qriously, an explanation engine inside a learning reader.",
        KIND_GUIDANCE.get(kind, KIND_GUIDANCE["root"]),
    ]
    if kind in SPAN_KINDS:
        sections += [SCOPE_RULE, REFERENCE_RULE]
    if kind in FOLLOWUP_KINDS:
        sections += [GROUNDING_RULE]
    sections += [
        FAMILIARITY_GUIDANCE[normalized["familiarity"]],
        length_rule,
        STYLE_GUIDANCE[normalized["style"]],
        GOAL_GUIDANCE[normalized["goal"]],
        anchor_rule,
        TRUST_RULE,
    ]
    if kind in FOLLOWUP_KINDS:
        sections.append(META_RULE)
    return "\n".join(sections)


def _kind_rules(kind: str, depth: str) -> tuple[str, str]:
    """Pick the length and anchor rules for a kind, overriding depth where the
    kind has a fixed shape (a definition or a short list of examples)."""
    if kind == "define":
        return DEFINE_LENGTH_RULE, DEFINE_ANCHOR_RULE
    if kind == "example":
        return EXAMPLE_LENGTH_RULE, EXAMPLE_ANCHOR_RULE
    if kind == "eli5":
        return ELI5_LENGTH_RULE, ELI5_ANCHOR_RULE
    return DEPTH_GUIDANCE[depth], ANCHOR_RULE


def build_user_prompt(
    *,
    text: str,
    kind: str,
    context: str | None = None,
    span_text: str | None = None,
    frame: str | None = None,
    trajectory: str | None = None,
) -> str:
    lines = []
    if frame:
        lines.append(f"This selection comes from {frame}.")
    if kind == "followup":
        lines.append("Session so far:")
        lines.append((trajectory or "").strip() or "(no earlier activity)")
        lines.append(f"Follow-up question: {text}")
        lines.append("Answer the follow-up question in the context of this session.")
        return "\n".join(lines)
    if kind == "ask" and span_text:
        lines.append(f"Passage: {span_text}")
        lines.append(f"Question about the passage: {text}")
        return "\n".join(lines)
    if kind in SPAN_KINDS and span_text:
        if context:
            lines.append(f"Passage:\n{context}")
        lines.append(f"Selected phrase: {span_text}")
        lines.append(
            "Explain the selected phrase only — do not re-explain the passage above."
        )
        return "\n".join(lines)
    lines.append(f"Explain: {text}")
    if context:
        lines.append(f"Context this came from: {context}")
    return "\n".join(lines)


def build_messages(
    *,
    text: str,
    kind: str,
    lens: Mapping[str, str] | None,
    context: str | None = None,
    span_text: str | None = None,
    frame: str | None = None,
    trajectory: str | None = None,
) -> list[dict[str, str]]:
    user = build_user_prompt(
        text=text,
        kind=kind,
        context=context,
        span_text=span_text,
        frame=frame,
        trajectory=trajectory,
    )
    return [
        {"role": "system", "content": build_system_prompt(lens, kind)},
        {"role": "user", "content": user},
    ]
