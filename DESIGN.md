# Qriously — Design Guidelines & Motivation

## The one idea

The homepage has one job: **convert a passive visitor into a curious one in
under three seconds.** Every decision below serves that. Curiosity is not
passive — it is an itch, a pull, a lean forward. The page should feel like it is
already leaning toward the visitor, asking them something.

The hero line — *"What made you Qrious today?"* — is not decoration. It is the
product. The rest of the page exists only to make that question impossible to
ignore and trivial to answer.

## Motivation

Most learning platforms open with a promise ("Learn anything!") or a feature
list. That is a resume, not an invitation. It makes the visitor process
information before they feel anything.

Qriously opens with a **question you already have an answer to**. Every person
arrived with something they were wondering about — even if it was just idle
curiosity. By asking first and answering later, we:

1. **Lower the activation energy.** Typing a question you already have is
   easier than deciding what to learn.
2. **Make the visitor the subject.** The platform is the guide, not the hero.
3. **Create a micro-commitment.** A typed question is an intent, and intent is
   the first step of learning.

The visual language reinforces this: the page is a dark, quiet night — the
mental state of wondering — lit by a single warm glow around the input. Your
curiosity is the only light source on the page.

## Design principles

1. **One focal point.** Exactly one thing competes for attention: the input.
   Everything else recedes.
2. **Warm light in the dark.** Curiosity is warmth against the unknown. We use
   a single violet→amber accent ramp, never a rainbow.
3. **Motion with meaning.** Animation should feel like something is *alive* —
   breathing, drifting, responding — not like decoration spinning for its own
   sake.
4. **Reward the interaction.** The moment a question is submitted, the page
   should visibly celebrate. Small delights make big impressions.
5. **Reduce, then reduce again.** Whitespace is not empty; it is room to think.

## Palette

| Token | Value | Use |
|---|---|---|
| `--bg-0` | `#07070c` | Deepest background |
| `--bg-1` | `#0d0d18` | Panel base |
| `--ink` | `#f4f2ff` | Primary text |
| `--ink-dim` | `#a9a4c9` | Secondary text |
| `--violet` | `#7c5cff` | Primary accent (curiosity) |
| `--cyan` | `#42e8e0` | Cool accent (insight) |
| `--amber` | `#ffb454` | Warm accent (the spark) |
| `--line` | `rgba(255,255,255,0.08)` | Hairlines / borders |

The gradient runs violet → cyan → amber. It reads as "a question forming into
understanding into a spark."

## Typography

- **Display / hero:** a high-contrast geometric sans, very large, tight
  tracking, with a gradient fill on the key word "Qrious."
- **Body / UI:** the same family at normal weights, generous line-height,
  muted color.
- Scale is dramatic: the hero should feel like it owns the screen, the body
  should feel whispered.

## Motion

| Effect | Purpose | Duration |
|---|---|---|
| Aurora drift | Ambient life in the background | 18–24s, infinite |
| Particle drift | Sense of thought in motion | continuous, slow |
| Input focus glow | Pull focus to the action | 300ms ease |
| Sample card lift | Invite the click | 200ms ease |
| Submit burst | Celebrate and confirm | ~900ms, one-shot |

All of the above collapse to near-zero under `prefers-reduced-motion: reduce`.

## Layout

Single centered column, max ~880px. Vertical rhythm, top to bottom:
brand mark → hero line → input → sample cards. The input sits on the optical
center of the viewport, not the mathematical center — it should feel slightly
above the middle so it catches the eye first.

## Accessibility

- Contrast: body text ≥ 4.5:1 on the dark base; accents used for large text or
  as accents only.
- All controls are native and keyboard reachable, with a visible focus ring.
- Sample cards are real buttons; Enter/Space activate them.
- Reduced-motion support is first-class, not an afterthought.
