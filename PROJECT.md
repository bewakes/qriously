# Qriously

## What it is

A learning platform, in two parts:

1. **Landing designs** (nine standalone directions) — the first thing a visitor
   sees, and the moment that has to make them feel curious.
2. **The immersive learning app** (`app/`) — the product itself: branching,
   non-linear exploration of a topic. Prototype built (mock content).

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

Core loop: **Ask → Calibrate → Read → Act → Nest → Save**.

- **Calibration lens** — one-tap, skippable personalization (familiarity,
  depth, style, goal); non-PII, local, editable mid-session.
- **Reader** — a reading *sheet*. **Dive in** renders as a **collapsible section
  below the content**, titled with the selection and recursively nestable.
- **Wider angles** — **ELI5 / Examples / Define** render as collapsible **cards
  in the side rail** (asides stay beside the text; only dives grow the sheet).
- **Selection toolbar** — select any span → Dive in / ELI5 / Examples / Define /
  Save as note, or type a free-text **Ask**. An already-actioned phrase opens a
  **results menu** listing its existing results plus the actions.
- **Trail** — clickable ancestry; **Composer** — persistent bottom ask box that
  **appends a new question section below**; **Notebook** — saved spans + context.

Full interaction spec: **`app/INTERACTION-SPEC.md`** (see its Decision log for
how the model evolved). Data model is a single node graph (one model powers
reading, actions, trail, and notes). Visual direction is a calm, near-flat dark
reading theme.

## Current state

**Landing designs:** static prototypes. Submitting a question runs a visual-only
animation and echoes the query — no search, no backend, no accounts. This is
deliberate: nail the feel of the first interaction before wiring anything up.

**Immersive app (`app/`):** MVP prototype built — calm reading-first theme,
calibration lens, **dives inline below the content** (collapsible, titled with
the selection, recursively nestable), a **"Wider angles"** side rail for
ELI5 / Examples / Define cards, a **results menu** on already-actioned phrases,
subtle direction markers (dotted underline + tiny `↓`/`→` arrow, no
pre-highlighting), a trail breadcrumb, an appending composer, and a notebook.
Content is a mock node graph for "Why is the sky blue?" (`?demo=1` pre-seeds a
session).

The visual system is deliberately **quiet**: a near-flat dark canvas with a
single accent; the earlier luminous ambient/energy effects were removed.
Bloom-on-action, unfolding transitions and a serif drop cap remain. The home
screen keeps its centered hero input; the reading view has a **persistent bottom
composer** that adds a new question below the current one. Retention/retrieval
mechanics are deliberately deferred; see the spec's Decision log. Spec:
`app/INTERACTION-SPEC.md`.

## Constraints

- Plain HTML/CSS/JS, no build step, per design.
- Each design must feel premium on first paint, offline, on any modern browser.
- The landing designs share one question, one input, and sample cards, so they
  can be compared like for like.

## Decisions

- One folder per design (chosen with the user) rather than one page with a
  theme switcher, so each direction stays self-contained.
- Submit: visual only for now.
- Rationale and tokens per direction are documented in `DESIGN.md`.

## Next

- **App:** wire a real LLM behind `generateNode` / `generateRoot` in
  `app/content.js` (streaming, citations, caching); then persistence and a
  lightweight learner profile.
- **App (deferred):** retrieval/"explain it back"; learner-state modeling.
- **Landing:** pick a direction, then route its input into the app.
- Mobile polish pass and copy review.
