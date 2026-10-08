"""Prompt construction for generation.

Pure module: no Django, no I/O, no vendor SDK. It only turns
(lens, kind, text) into the messages a model receives, so it is fully
unit-testable and the same on every request.
"""

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


def build_system_prompt(lens, kind):
    """Return the system prompt for a generation request.

    TODO(you): compose and return the system prompt string.

    Contract:
    - Normalize ``lens`` with ``core.constants.normalize_lens`` and turn each
      of the four dimensions into guidance:
        * familiarity -> how much prior knowledge to assume
          (``new`` | ``basics`` | ``expert``)
        * depth       -> how long and detailed the answer should be
          (``quick`` | ``solid`` | ``deep``)
        * style       -> the voice to use
          (``plain`` | ``analogy`` | ``technical``)
        * goal        -> how to frame the answer
          (``curious`` | ``project`` | ``exam``)
    - Tailor the framing to ``kind``
      (``root`` | ``dive`` | ``eli5`` | ``example`` | ``define`` | ``ask``).
    - Include ``ANCHOR_RULE`` and ``TRUST_RULE`` verbatim.
    - Be deterministic: same ``(lens, kind)`` -> same string.

    See ``generation/tests/test_prompts.py`` for the exact behaviors expected;
    ``pytest generation`` should go green when this is implemented.
    """
    raise NotImplementedError("build_system_prompt is yours to implement")


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
