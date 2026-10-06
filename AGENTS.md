# Qriously — Agent Guide

## What this is

**Qriously**, a learning platform, in two parts:

1. **Landing designs** — nine standalone homepage directions around the prompt
   "What made you Qrious today?" (static; no backend).
2. **The immersive app** (`app/`) — the product: non-linear, branching
   exploration where any phrase in an answer is a doorway. Working prototype,
   mock content, no backend.

## Repo layout

```text
qriously/
├── index.html          # chooser linking to every landing design
├── DESIGN.md           # landing design system + rationale for each direction
├── nocturne/ daylight/ playtime/ blueprint/ riso/ atelier/
├── liquidglass/ questlog/ clay/          # nine landing designs
└── app/                # the immersive learning app
    ├── INTERACTION-SPEC.md  # interaction + decisions (READ FIRST)
    ├── index.html
    ├── styles.css           # "Lumen" theme + component styles
    ├── content.js           # mock node graph + generator (the fake "AI")
    └── script.js            # app engine (state, rendering, interaction)
```

Landing folders are independent, self-contained pages. `app/` is the real
product surface. Read `app/INTERACTION-SPEC.md` before changing the app.

## Running

- Landing chooser: open the root `index.html`.
- App: open `app/index.html`, or `app/index.html?demo=1` for a pre-seeded
  session (5 actions), handy for screenshots/manual testing.
- Serve anything: `python3 -m http.server 8000` (app at `/app/`).

## The app (current model — v5)

Read `app/INTERACTION-SPEC.md` for the full spec and the decision log (the model
changed several times: margin rail → list+window → **inline action sections**).
The short version:

- **Home:** centered hero input. Submit → **Calibration lens** (familiarity,
  depth, style, goal; skippable; non-PII) → **Reader**.
- **Reader:** a reading *sheet* with the answer, plus:
  - **Inline action sections** — every action (Dive in / ELI5 / Examples /
    Define) renders as a **collapsible section below the content**, titled with
    the selected phrase, labelled by kind, and **recursively nestable** (select
    text inside a section to go deeper). Collapse via the chevron; remove via ✕.
  - **Your actions** (right panel) — a collapsible, creation-ordered index;
    `↑`/`↓` step and scroll; `⤢` expands; the active row is highlighted.
  - **Trail** — breadcrumb of the active path.
  - **Composer** — a persistent bottom "ask" box (reader-only) aligned to the
    reading sheet; submitting starts a new question using the current lens.
  - **Notebook** — saved spans + context (top bar).
- **Anchors:** nothing is highlighted until acted on. Actioned spans get a
  *subtle* dotted underline + tiny muted kind glyph. Clicking the text opens the
  action toolbar; clicking the glyph scrolls to that action's section.
- **Look:** "Lumen" — luminous dark canvas that brightens as you act
  (`--energy`), bloom-on-action, unfolding transitions, serif drop cap, motes.

### Files & where things live

- `script.js` holds all behavior and state: `state = { lens, nodes, order,
  activeId, marks, notes }`. Key functions: `startReader`, `createSection`,
  `toggleSection`, `removeSection`, `renderActions`, `renderTrail`,
  `showToolbar`/`performAction`, `registerMark`/`applyMarks`, `focusSection`.
- `content.js` is the mock "AI": `SEED_ROOT` (the "Why is the sky blue?" body),
  `LIBRARY` (curated nodes keyed by phrase), `generateNode(parent, anchor, kind,
  lens)` with a `synthesize()` fallback so *any* selection produces a plausible
  section. **To wire a real LLM, replace `generateNode` behind the same
  interface** (title, body, citations, estReadSeconds).
- `styles.css` uses CSS custom properties in `:root` + `html[data-theme=...]`.
  Kind colors are `--k-dive/-eli5/-example/-define/-note`. The energy variable
  is `--energy` (set by `setEnergy`).
- Bodies use `**phrase**` markers to seed curated anchors; rendered to
  `.anchor` spans. Nothing is pre-highlighted.

### Known limitations / next steps

- Content is mock; no LLM, persistence, or accounts. `estReadSeconds` is fake.
- Landing and app are not yet connected (landing submit is visual-only).
- Mobile: the actions panel stacks below the reading sheet; the composer stays
  docked. Not yet a native bottom-sheet.
- Deliberately deferred (see spec Decision log): retrieval/consolidation
  ("explain it back"), learner-state modeling, the spark map (cut).
- The inline-section model has a known reflow/depth risk; mitigations are
  collapse + capped indent + the actions index. The single-window model is the
  logged fallback.

## Conventions

- Plain HTML/CSS/JS. No build step, no npm, no framework. Google Fonts with
  system fallbacks; pages must work offline-ish.
- Design tokens live as CSS custom properties; no scattered literals.
- Respect `prefers-reduced-motion` for every animation (app hides motes too).
- Accessibility: real `<button>`/`<input>`, visible focus rings, keyboard
  routes (Enter/Space on anchors; Escape closes toolbar/notebook).
- No comments in code unless they earn their place.
- When the app's interaction model changes, update
  `app/INTERACTION-SPEC.md`'s Decision log in the same change.
