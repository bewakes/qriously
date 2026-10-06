# Qriously

## What it is

A learning platform, in two parts:

1. **Landing designs** (nine standalone directions) — the first thing a visitor
   sees, and the moment that has to make them feel curious.
2. **The immersive learning app** (`app/`) — the product itself: branching,
   non-linear exploration of a topic. Spec only so far.

## The page

One screen, centered. Top to bottom:

1. A brand mark and the hero line: **"What made you Qrious today?"**
2. A large free-text input where the visitor types their question.
3. A row of sample question cards to spark ideas and lower the "blank box"
   barrier.
4. On submit: an inline response panel that echoes the question and shows a
   short "pulling the thread together" state.

## Structure

Nine design directions, each standalone in its own folder. A root `index.html`
acts as a chooser.

| Folder | Direction | Feel |
|---|---|---|
| `nocturne/` | Dark, glowing, animated | Deep night, aurora glow, drifting particles |
| `daylight/` | Light, airy, editorial | Paper white, serif display, calm and trustworthy |
| `playtime/` | Playful, colorful | Cream pop, rounded, hard shadows, confetti |
| `blueprint/` | Technical drawing | Blueprint blue, cyan grid, dimension line, title block |
| `riso/` | Two-spot zine | Fluorescent pink + blue, misregistration, grain |
| `atelier/` | Luxury editorial | Near-black, gold hairlines, high-contrast Bodoni |
| `liquidglass/` | Premium glassmorphism | Frosted panes over a fluid gradient, parallax |
| `questlog/` | RPG adventure HUD | Parchment cards, XP bar that fills, sparkles |
| `clay/` | Claymorphism | Puffy pastel shapes, soft dual shadows, squish |

The last six were proposed and selected as a wider exploration; the user's
feedback was that `daylight/` felt too conventional.

## Immersive learning app (`app/`)

The product vision: learning is a graph, not a line. A chat answer is linear,
so following a tangent means losing your place. The app makes **every span a
doorway** and fans branches out **without losing the parent context**.

Core loop: **Ask → Calibrate → Read → Branch → Nest → Save**.

- **Calibration lens** — one-tap, skippable personalization (familiarity,
  depth, style, goal); non-PII, local, editable mid-session.
- **Reader** — a reading column plus a **margin rail** where dive-ins stack as
  nested, collapsible cards; the parent never reflows.
- **Selection toolbar** — select any span → Dive in / ELI5 / Examples / Save as
  note / Define.
- **Trail** — clickable ancestry that doubles as a study outline.
- **Notebook** — saved spans + context + generated text.

Full interaction spec: **`app/INTERACTION-SPEC.md`**. Data model is a single
node graph (one model powers reading, branching, trail, notes, and a future map
view). Visual direction is a new reading-first theme, working name **Lumen**.

## Current state

**Landing designs:** static prototypes. Submitting a question runs a visual-only
animation and echoes the query — no search, no backend, no accounts. This is
deliberate: nail the feel of the first interaction before wiring anything up.

**Immersive app (`app/`):** spec only (`INTERACTION-SPEC.md`). No code yet.
Decisions locked: margin-rail branching, mock content graph for the prototype,
and a new reading-first theme ("Lumen").

## Constraints

- Plain HTML/CSS/JS, no build step, per design.
- Each design must feel premium on first paint, offline, on any modern browser.
- All three share one question, one input, and sample cards, so they can be
  compared like for like.

## Decisions

- One folder per design (chosen with the user) rather than one page with a
  theme switcher, so each direction stays self-contained.
- Submit: visual only for now.
- Rationale and tokens per direction are documented in `DESIGN.md`.

## Next

- **App:** build the MVP prototype from `app/INTERACTION-SPEC.md`
  (mock content graph, Lumen theme, margin rail, notes), then wire a real LLM.
- **Landing:** pick a direction, then route the input into the app.
- Mobile polish pass and copy review.
