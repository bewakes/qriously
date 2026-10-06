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

All nine directions below share this structure, copy, and interaction. Only the
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

## Direction 1 — Nocturne (`nocturne/`)

**Feel:** dark, glowing, animated. Curiosity as the only light in the room.

- **Palette:** deepest `#07070c` night; accents violet `#7c5cff`, cyan
  `#42e8e0`, amber `#ffb454`.
- **Type:** Space Grotesk display + Inter body. Hero very large, tight, with a
  gradient-filled "Qrious".
- **Decoration:** three blurred aurora blobs drifting on long cycles, plus a
  particle canvas of slow rising motes.
- **Input:** pill-shaped glass bar; on focus it blooms with a gradient border
  glow and lifts.
- **Cards:** glass panels that lift and glow on hover.
- **Idea:** the night of wondering, lit by one warm spark.

## Direction 2 — Daylight (`daylight/`)

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

## Direction 3 — Playtime (`playtime/`)

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

---

## Direction 4 — Blueprint (`blueprint/`)

**Feel:** technical drawing. Curiosity as engineering.

- **Palette:** blueprint blue `#0a2545` with a cyan grid, white ink, amber
  callouts.
- **Type:** IBM Plex Mono for labels and annotations, Space Grotesk for the
  hero.
- **Decoration:** a drafting frame with corner brackets and rulers, a dimension
  line under the hero, a title block pinned bottom-right.
- **Input:** a dashed technical field with corner tick marks, labelled
  `INPUT · QUERY_001`, and a `RUN` stamp button.
- **Cards:** dashed "SPEC 01–04" fields.
- **Idea:** every question is a schematic to be drawn.

## Direction 5 — Riso Zine (`riso/`)

**Feel:** DIY print. Human, loud, anti-corporate.

- **Palette:** off-white paper, near-black ink, fluorescent pink `#ff2e63` and
  riso blue `#1f4fff`.
- **Type:** Archivo Black headlines, Space Mono for everything else.
- **Decoration:** halftone dots, a photocopy-grain overlay, misregistered
  color offsets on the hero word.
- **Input and cards:** thick ink outlines with hard pink/blue offset shadows;
  cards tilt like pasted cut-outs.
- **Idea:** a zine about asking — raw and joyful.

## Direction 6 — Luxury Atelier (`atelier/`)

**Feel:** knowledge as treasure. Refined, quiet, expensive.

- **Palette:** near-black `#0c0b0a`, brushed gold `#c9a55a`, bone text.
- **Type:** Bodoni Moda display (italic gold "Qrious"), Jost for letterspaced
  small-caps labels.
- **Decoration:** hairline rules, a faint gold vignette, a slow shimmer across
  the gold.
- **Input:** a single understated underline rather than a box.
- **Entries:** a numbered hairline list (01–04), not cards.
- **Idea:** a curated atelier of curiosity.

## Direction 7 — Liquid Glass (`liquidglass/`)

**Feel:** premium calm-tech.

- **Palette:** deep navy base with a fluid gradient of indigo, teal, pink and
  amber.
- **Type:** Sora display + Inter.
- **Decoration:** frosted glass panels over drifting color orbs, film grain, a
  subtle pointer parallax.
- **Input:** a glass pill inside a large glass console.
- **Cards:** small glass chips.
- **Idea:** modern, tactile, trustworthy software.

## Direction 8 — Quest Log (`questlog/`)

**Feel:** learning as adventure.

- **Palette:** dark leather `#17120c`, gold `#e0ac4e`, parchment cards, emerald
  XP.
- **Type:** Cinzel for runes/labels, Spectral for the hero, Inter for UI.
- **Decoration:** a sticky HUD with a level and an XP bar; a "+25 XP" reward on
  every quest; a sparkle burst and toast on submit.
- **Input and cards:** a carved panel and parchment quest cards.
- **Idea:** progress and reward built into the first interaction.

## Direction 9 — Clay Toy (`clay/`)

**Feel:** tactile and friendly.

- **Palette:** soft lavender base gradient with lavender, mint, peach and sky
  clay colors.
- **Type:** Baloo 2 display + Nunito.
- **Decoration:** blurred clay blobs, puffy dual-shadow surfaces.
- **Input and cards:** extruded clay tubes and tiles that squish on hover with
  an overshoot spring.
- **Idea:** squish your curiosity — warm and physical, but three-dimensional
  where Playtime is flat.

---

## Closing rules that apply to all nine

1. **One focal point.** Exactly one thing competes for attention: the input.
2. **Motion with meaning.** Animate to feel alive and to reward input, never as
   decoration for its own sake.
3. **Reward the interaction.** The moment a question is submitted, the page
   visibly celebrates.
4. **Reduce, then reduce again.** Whitespace is room to think.
5. **Accessible by default.** Contrast, keyboard, focus, and reduced-motion are
   first-class, not an afterthought.
