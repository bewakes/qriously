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
    ├── styles.css           # theme tokens + component styles
    ├── content.js           # mock node graph + generator (the fake "AI")
    └── script.js            # app engine (state, rendering, interaction)
```

Landing folders are independent, self-contained pages. `app/` is the real
product surface. Read `app/INTERACTION-SPEC.md` before changing the app.

## Running

- Landing chooser: open the root `index.html`.
- App: open `app/index.html`, or `app/index.html?demo=1` for a pre-seeded
  session (questions, dives and asides), handy for screenshots/manual testing.
- Serve anything: `python3 -m http.server 8000` (app at `/app/`).

## The app (current model — v8)

Read `app/INTERACTION-SPEC.md` for the full spec and the decision log (the model
changed several times: margin rail → list+window → inline action sections →
**dives inline, asides on the side**). The short version:

- **Home:** centered hero input. Submit → **Calibration lens** (familiarity,
  depth, style, goal; skippable; non-PII) → **Reader**.
- **Reader:** a reading *sheet* with the answer, plus:
  - **Dive sections** — only **Dive in** renders as a collapsible section
    **below the content**, titled with the selected phrase; dives nest
    recursively. Collapse via the toggle; remove via ✕. No `L#` depth labels.
  - **Wider angles** (right rail) — **ELI5 / Examples / Define** render as
    collapsible **cards** on the side. Selecting inside any card and choosing a
    kind routes by kind: dives go below, asides stay in the rail.
  - **Trail** — breadcrumb of the active path; the leading crumb is the base
    question.
  - **Composer** — a persistent bottom "ask" box (reader-only); submitting
    **appends a new question section below** (does not replace the session),
    using the current lens.
  - **Notebook** — saved spans + context (top bar).
- **Anchors:** nothing is highlighted until acted on. Actioned spans get a
  *subtle* dotted underline + a tiny direction marker (`↓` below, `→` side,
  `★` note; both shown when a phrase has both). Clicking the text opens a
  **results menu** — existing results (click to jump + expand) plus the action
  buttons; clicking the marker jumps when there is one result, opens the menu
  when there are several.
- **Look:** calm near-flat dark canvas. A single accent; no ambient blobs, motes
  or gradient/glow effects (the earlier "Lumen" energy model was removed).
  Bloom-on-action, unfolding transitions and the serif drop cap remain.

### Files & where things live

- `script.js` holds all behavior and state: `state = { lens, nodes, order,
  activeId, marks, notes }`. Key functions: `startReader`, `addQuestion`,
  `createSection` (routes dives via `diveHost`, asides to `#sideList`),
  `toggleSection`, `removeSection`/`descendantIds`, `renderSide`,
  `renderTrail`/`rootOf`, `showToolbar`/`renderToolbarResults`/`performAction`,
  `registerMark`/`applyMarks`, `focusSection`.
- `content.js` is the mock "AI": `SEED_ROOT` (the "Why is the sky blue?" body),
  `LIBRARY` (curated nodes keyed by phrase), `generateNode(parent, anchor, kind,
  lens)` and `generateRoot(question, lens)`, both with a `synthesize()` fallback
  so *any* selection/question produces plausible text. **To wire a real LLM,
  replace these behind the same interfaces** (title, body, citations,
  estReadSeconds).
- `styles.css` uses CSS custom properties in `:root` + `html[data-theme=...]`.
  Kind colors are `--k-dive/-eli5/-example/-define/-note`. Side cards
  (`.side-card`), question sections (`.question-section`) and the results menu
  (`.toolbar-results`) are the newer component styles.
- Bodies use `**phrase**` markers to seed curated anchors; rendered to
  `.anchor` spans. Nothing is pre-highlighted.

### Known limitations / next steps

- Content is mock; no LLM, persistence, or accounts. `estReadSeconds` is fake.
- Landing and app are not yet connected (landing submit is visual-only).
- Mobile: the actions rail stacks below the reading sheet; the composer stays
  docked. Not yet a native bottom-sheet.
- Deliberately deferred (see spec Decision log): retrieval/consolidation
  ("explain it back"), learner-state modeling, the spark map (cut).
- Questions accumulate down the sheet; there is no per-question collapse-all or
  reordering yet. The inline-dive model still carries a reflow/depth risk;
  mitigations are collapse + capped indent + the trail. The single-window model
  remains the logged fallback.

## Conventions

- Plain HTML/CSS/JS. No build step, no npm, no framework. Google Fonts with
  system fallbacks; pages must work offline-ish.
- Design tokens live as CSS custom properties; no scattered literals.
- Respect `prefers-reduced-motion` for every animation.
- Accessibility: real `<button>`/`<input>`, visible focus rings, keyboard
  routes (Enter/Space on anchors; Escape closes toolbar/notebook).
- No comments in code unless they earn their place.
- When the app's interaction model changes, update
  `app/INTERACTION-SPEC.md`'s Decision log in the same change.
