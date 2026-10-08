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
├── docs/               # end-to-end architecture (READ docs/ARCHITECTURE.md)
│   ├── ARCHITECTURE.md  # thesis, stack, flows, decisions (proposed)
│   ├── DATA-MODEL.md    # content layer + thread layer schema
│   ├── API.md           # REST + SSE contract (v1)
│   └── PLAN.md          # phased build plan
├── app/                # the immersive learning app (frontend)
│   ├── INTERACTION-SPEC.md  # interaction + decisions (READ FIRST)
│   ├── index.html
│   ├── styles.css           # theme tokens + component styles
│   ├── content.js           # mock node graph + generator (demo/offline "AI")
│   └── script.js            # app engine (state, rendering, interaction)
└── server/             # Django + DRF backend: core, accounts, credits,
                        # telemetry, content, learning, generation, safety
```

Landing folders are independent, self-contained pages. `app/` is the product
frontend. Read `app/INTERACTION-SPEC.md` before changing the app, and
`docs/` before touching the backend.

## Running

- Landing chooser: open the root `index.html`.
- App: open `app/index.html`, or `app/index.html?demo=1` for a pre-seeded
  session (questions, dives and asides), handy for screenshots/manual testing.
  `?demo=1` uses the offline mock and needs no server.
- Serve anything: `python3 -m http.server 8000` (app at `/app/`).
- Backend: `cd server && docker compose up -d db`, then
  `python manage.py migrate && python manage.py seed_content`, then
  `python manage.py runserver` (or `uvicorn config.asgi:application`) — see
  `docs/PLAN.md`. Checks: `ruff check .` and `pytest` (needs the Postgres
  container). `DEEPSEEK_API_KEY` in `server/.env` enables real generation.

## The app (current model — v8)

Read `app/INTERACTION-SPEC.md` for the full spec and the decision log (the model
changed several times: margin rail → list+window → inline action sections →
**dives inline, asides on the side**). The short version:

- **Home:** centered hero input. Submit → **Calibration lens** (familiarity,
  depth, style, goal; skippable; non-PII) → **Reader**.
- **Reader:** a reading *sheet* with the answer, plus:
  - **Dive sections** — only **Dive in** renders as a collapsible section
    **below the content**, titled with the selected phrase; dives nest
    recursively. Collapse via the toggle **or the title**; `↩` jumps to the
    source phrase; remove via ✕. No `L#` depth labels.
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
  when there are several. The toolbar also has a small free-text **Ask** field
  that turns a question about the span into one inline `ask` section
  (single-shot; no chat/thread state).
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
  lens)`, `generateRoot(question, lens)` and `generateAsk(parent, anchor,
  question, lens)`, all with a `synthesize()` fallback so *any*
  selection/question produces plausible text. **To wire a real LLM, replace
  these behind the same interfaces** (title, body, citations, estReadSeconds);
  the end-to-end plan (`docs/`) keeps this mock as the offline/demo adapter.
- `styles.css` uses CSS custom properties in `:root` + `html[data-theme=...]`.
  Kind colors are `--k-dive/-eli5/-example/-define/-note`. Side cards
  (`.side-card`), question sections (`.question-section`) and the results menu
  (`.toolbar-results`) are the newer component styles.
- Bodies use `**phrase**` markers to seed curated anchors; rendered to
  `.anchor` spans. Nothing is pre-highlighted.

### Known limitations / next steps

- The app still runs on the mock content (`content.js`); it is not yet wired to
  the backend. The backend itself exists and is being built out in
  `docs/PLAN.md` (Phase 3 in progress: content layer, learning graph, generation
  orchestration and metering are in; the HTTP/SSE surface and the app wiring are
  next).
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

### Backend (`server/`)

- Django 5 + DRF on Postgres/pgvector; ASGI; DeepSeek behind
  `generation/llm` only. Read `docs/ARCHITECTURE.md`, `docs/DATA-MODEL.md`,
  `docs/API.md`, `docs/PLAN.md` before writing backend code.
- **Layering (enforced):** one entity per concept (the Django model — no
  dataclass/mapper duplicates); all decisions in framework-free `policies.py`
  (and `lenses/`, `safety/`, `core/constants.py`) that must **not import
  Django**; `services.py` runs use cases and owns `transaction.atomic`; `api.py`
  is thin. ORM imports stay in models/services/selectors/admin.
- Two layers: shared immutable `Concept`/`ContentVariant` (lens-indexed,
  reusable) referenced by per-user `Thread`/`Span`/`Node`. Reuse is a reference,
  never a copy. `ContentVariant` rows are immutable — a new `prompt_version`
  instead of an update.
- Credits are integer micro-credits in an append-only `CreditEntry` ledger;
  balance is a cached sum guarded by `select_for_update`. Never a float.
- A **screening layer** (`safety/`) runs before any spend; MVP policy is
  allow-all, but the interface and the `422 content_blocked` path exist.
- Every metered call creates a `RequestLog`; credits, usage, screening and vendor
  cost reference it. **Vendor LLM cost** (`vendor_cost_micros`, from the
  versioned `ModelPrice` table) is tracked separately from the credits charged.
- **Cache hits are charged** a configurable fraction (`CACHE_HIT_RATIO`), never
  free.
- All tunables (model id, prices, per-kind costs, depth multipliers, cache ratio,
  signup grant, screening policy, prompt version) live in `core/constants.py`,
  not scattered literals.
- Generation requests carry an `Idempotency-Key`; debit is reserve→settle, and
  failures refund. Never charge for a failed generation.
- No vendor SDK calls outside `generation/`; keep the DeepSeek client behind an
  interface so it can be swapped. Default model is `deepseek-flash`.
- No PII in the lens; never join lens data to identity.
