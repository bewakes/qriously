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

The three directions below share this structure, copy, and interaction. Only the
visual mood changes, so they can be compared like for like.

## Shared structure

Single centered column, max ~880–900px. Top to bottom: brand → hero line →
input → sample cards → (on submit) response panel. The input sits on the optical
center, slightly above the middle, so it catches the eye first.

Shared behaviour:

- Sample cards fill the input and submit on click; they are real buttons and
  keyboard-operable.
- Submitting pulses/animates and reveals a response panel that echoes the query,
  then cycles a short "connecting the dots…" status.
- Focus rings are always visible; reduced-motion is honored everywhere.

---

## Direction 1 — Daylight (`daylight/`)

**Feel:** light, airy, editorial. Calm, trustworthy.

- **Palette:** warm paper `#f7f6f2`, ink `#191a1e`, dusty-blue accent `#2f5d8a`,
  terracotta `#bf6b45`, faint pastel washes of blue and sage.
- **Type:** Fraunces serif for the hero and key labels; Inter for UI. "Qrious"
  is italic in the accent color.
- **Decoration:** no motion in the background — just soft pastel radial washes
  and generous whitespace. A hairline masthead rule gives it a magazine feel.
- **Input:** a clean white card with a soft shadow; the button is solid ink,
  slightly rounded (not a pill), so it reads as print, not app.
- **Cards:** white, hairline borders, a "Read →" affordance that fades in on
  hover.
- **Idea:** a calm, well-set page you trust — like the front page of a good
  journal.

## Direction 2 — Playtime (`playtime/`)

**Feel:** playful, colorful. Rounded, energetic, friendly.

- **Palette:** cream `#fff7e8` base with bright candy accents — coral `#ff6b5c`,
  sunny `#ffc93c`, sky `#4cc3ff`, grape `#9b6bff`, mint `#43d9a3`.
- **Type:** Fredoka display + Nunito body. "Qrious" cycles through a rainbow
  gradient.
- **Decoration:** floating ✦ ● ✳ shapes bobbing in the corners; a confetti burst
  on submit.
- **Input and cards:** thick ink outlines with hard offset shadows (sticker /
  pop style). Cards are tinted per slot, tilted slightly, and jump on hover.
- **Idea:** learning as play — ask silly questions, get rewarded for asking.

## Direction 3 — Luxury Atelier (`atelier/`)

**Feel:** knowledge as treasure. Refined, quiet, expensive.

- **Palette:** near-black `#0c0b0a`, brushed gold `#c9a55a`, bone text.
- **Type:** Bodoni Moda display (italic gold "Qrious"), Jost for letterspaced
  small-caps labels.
- **Decoration:** hairline rules, a faint gold vignette, a slow shimmer across
  the gold.
- **Input:** a single understated underline rather than a box.
- **Entries:** a numbered hairline list (01–04), not cards.
- **Idea:** a curated atelier of curiosity.

---

## Closing rules that apply to all three

1. **One focal point.** Exactly one thing competes for attention: the input.
2. **Motion with meaning.** Animate to feel alive and to reward input, never as
   decoration for its own sake.
3. **Reward the interaction.** The moment a question is submitted, the page
   visibly celebrates.
4. **Reduce, then reduce again.** Whitespace is room to think.
5. **Accessible by default.** Contrast, keyboard, focus, and reduced-motion are
   first-class, not an afterthought.
