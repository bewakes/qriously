# Qriously — Immersive Learning App: Interaction Spec

**Status:** Living spec · prototype implemented (`app/index.html`); current interaction is **model v10** (see §20 Decision log). Where this doc and the code differ, **the code is the source of truth** — update the doc in the same change.
**Surface:** `qriously/app/` (the landing designs are untouched)
**Scope of this doc:** product concept, interaction model, content model, and MVP plan.

---

## 1. Problem & insight

LLMs can already explain anything. The bottleneck is not generation — it is **navigation**. A chat thread is linear: each answer overwrites the last, and following a tangent means losing the place you came from. But learning is not linear. It branches, fans out, and loops back.

**The insight:** the atomic unit of learning is not the answer, it is the **span**. Any phrase in an explanation is a potential doorway. Diving through one must **not destroy the path that led there**.

So the product is not "AI that answers." It is **branching that preserves ancestry**: content fans out in place, the parent stays visible, and the learner never loses the thread.

## 2. Principles

1. **Never lose the thread.** Following a branch keeps its ancestry visible and one click away.
2. **The parent is sacred.** Branching must not reflow or discard the reading context.
3. **Earn the user's attention, then stay out of the way.** The tool should feel invisible once reading begins.
4. **Personalize by dimension, not by identity.** We adapt to skill, depth, and goal — never to PII.
5. **Every path is a personal artifact.** The trail and notes are study material, not exhaust.
6. **Depth with guardrails.** Go as deep as you want, but always know how deep you are and how to surface.

## 3. The core loop

```
Ask  →  Calibrate  →  Read  →  Branch  →  Nest  →  Save  →  (Compose)
 |_____________ repeat, recursively, without losing context __________|
```

1. **Ask** — a single Google-like input: *"What made you curious today?"*
2. **Calibrate** — a fast, skippable "lens" (level, depth, style, goal).
3. **Read** — an immersive reading view of the generated answer.
4. **Branch** — select any span → choose an action (Dive in, ELI5, Examples, Save…).
5. **Nest** — the branch opens in a margin rail, stacked beneath its parent; the parent stays put.
6. **Save** — capture spans + context into the Notebook; the trail becomes a study outline.
7. **Compose** (later) — assemble the trail + notes into a summary or lesson.

## 4. Surfaces

| Surface | Purpose |
|---|---|
| Home | The single input. One field, one question. |
| Calibration lens | One-tap personalization; skippable, editable anytime. |
| Reader | Reading column + branch list + trail. The heart of the app. |
| Composer | A persistent bottom ask box; asking here **appends a new question section** below the current reading (it does not replace the session). |
| Question section | A new question (from the composer) rendered as a section below the current reading, with its own answer and nested dives. |
| Dive section | A **Dive in** result rendered inline below the content, titled with the selection; dives nest recursively. |
| Side rail ("Wider angles") | Non-dive results (**ELI5 / Examples / Define**) rendered as collapsible cards alongside the reading sheet. |
| Selection toolbar | Contextual actions for a span, a free-text **Ask** field, plus (when it has results) a list of existing results to jump to. |
| Trail | Clickable ancestry; doubles as a study outline. |
| Notebook | Saved spans + context + generated text; assemble/export. |

## 5. Screen flow

```
HOME
 └─[ask]─► CALIBRATION LENS        (skippable → defaults)
              └─[start reading]─► READER
                    ├─[select span]─► SELECTION TOOLBAR
                    │                    ├─ Dive in ──► DIVE SECTION (inline below)
                    │                    ├─ ELI5     ┐
                    │                    ├─ Examples ┼─► SIDE CARD (Wider angles rail)
                    │                    │           ┘   ├─[select span]─► dive / card…
                    │                    └─ Save ──► NOTEBOOK
                    ├─[collapse]  fold subtree
                    ├─[trail]     jump to any ancestor / the root
                    └─[notebook]  review & assemble
```

## 6. Calibration lens

A single card shown immediately after the query. Every field has a sensible default preselected, so **"Skip" = accept defaults**, never "get a worse result."

| Dimension | Options | Default | Applies to |
|---|---|---|---|
| Familiarity | New to this · Know the basics · I'm an expert | Know the basics | Vocabulary, assumed prior knowledge |
| Depth | Quick ≈2 min · Solid ≈7 min · Deep ≈15 min | Solid | Length, number of examples |
| Style | Plain · With analogies · Technical | Plain | Tone, jargon, structure |
| Goal (optional) | Curious · For a project · Exam prep · Teach someone | Curious | Framing, emphasis, callouts |

**Rules**
- Non-PII only. No name, no email, no account required.
- Stored locally; one "Reset lens" action.
- **Editable mid-session** via a persistent *lens chip* in the top bar. Changing it re-tunes subsequent branches; it does not rewrite what's already read.
- Skipping is allowed and frictionless; the chip invites re-calibration later ("Make this more technical →").

## 7. The Reader

### 7.1 Layout zones (desktop)

```
┌───────────────────────────────────────────────────────────────┐
│ TOP BAR   Qriously   [ lens ▾ ]            [ notes ] [◐] [＋]  │
├───────────────────────────────────────────────────────────────┤
│ TRAIL     Question › Rayleigh scattering › violet …            │
├───────────────────────────────┬───────────────────────────────┤
│  READING (sheet)              │  WIDER ANGLES                  │
│                               │  ◆ ELI5  "nitrogen"            │
│  …answer…                     │  …card, collapsible…           │
│  3 sources · verified         │  ◆ EXAMPLES  "wavelength"      │
│                               │  …card, collapsible…           │
│  │▸ DIVE  "Rayleigh scat…"    │                               │
│  │  …inline, collapsible…      │                               │
│  │  │▸ DIVE  "violet"           │                               │
│  │  │  …nested dive…            │                               │
├───────────────────────────────┴───────────────────────────────┤
│ COMPOSER   [ ask a new question…          ] [ Ask ]            │
│            ≈ 1 min read · 5 actions                            │
└───────────────────────────────────────────────────────────────┘
```

- **Reading sheet:** measure ~720px, generous line-height; holds the root answer plus inline **dive sections**. A quiet meta line (sources · verified) sits directly under the title, above the body.
- **Dive sections:** only **Dive in** renders as a collapsible section **below the content**, titled with the selected phrase. Dives **nest** under dives — select inside a dive to go deeper. This is the only content that grows the sheet.
- **Wider angles (side rail):** non-dive actions (**ELI5 / Examples / Define**) render as collapsible **cards in the right rail**, never below the text. They are always one step off the main line of reading.
- **Trail:** horizontal breadcrumb of the active path; click any crumb to jump.
- **Composer:** persistent bottom ask box with read-time/action counters. Submitting **adds a new question section** below the current content (streamed, with its own dives nested under it and its asides in the side rail), rather than wiping the reader. The session can therefore hold several questions stacked down the sheet; the trail's base crumb follows the active question.

### 7.2 Reading behavior
- Content **streams** token-by-token; a skeleton holds layout to avoid jumps.
- Paragraphs fade/slide in gently; nothing bounces.
- Dives open **inline**, so the sheet reflows — mitigated by per-section collapse, capped indentation, the trail and the results menu for jumping. Asides sit in the side rail and never reflow the sheet.
- Long content: sticky subsection headers and a progress indicator.

### 7.3 Anchor & action marks
- Nothing is highlighted on arrival. A span becomes an **anchor** only once the user acts on it.
- Actioned anchors are deliberately **subtle**: a dotted underline plus a tiny, muted **direction marker** that says where the result lives — `↓` (bottom) for Dive in, `→` (side) for ELI5 / Examples / Define, `★` for a saved note. An anchor with both a dive and an aside shows both, e.g. `↓→`. Kind is still carried by the marker's colour and its tooltip. They must not compete with the prose.
- Clicking the anchor opens the **results menu** (see §8): existing results first, action buttons below, so you can jump to what exists or branch again. Clicking the tiny marker jumps to the single existing result, or opens that menu when there are several.
- The active action's source anchor gets a faint tint so the origin is findable. The tint is transient: it clears when you click outside the sections/anchors, or collapse the action it belongs to — there is no lingering highlight.
- Anchors are semantic (a phrase), not pixel ranges, so they survive re-renders and streaming.

## 8. Selection toolbar

Appears anchored just above the selection (or as a bottom bar on mobile). Shows the selected text as a quiet preview, then **any results that phrase already has**, then the action buttons.

When the phrase already has results, the toolbar is a **results menu**: a scannable list (`↓ Dive · "…"`, `→ ELI5 · "…"`) above the action buttons. Click a row to scroll to that result and expand it; the buttons below still create another. This means one click on an actioned phrase both reveals what exists and offers the way to go further. If the phrase has no results yet, only the action buttons show. Clicking the inline **marker** jumps straight to the result when there is exactly one, and opens this menu when there are several.

Below the action buttons sits a small **Ask** field ("Ask about this…"). It covers the cases the presets can't: it takes a free-text question scoped to the selected phrase and produces **one** inline answer node (kind `ask`, titled with your question), anchored to the phrase so it also appears in the results menu and the marker. It is deliberately single-shot — submitting creates one section and closes the toolbar; there is no chat/thread state. Further depth is reached the normal way (select inside the answer), and the bottom composer remains the route for a fresh, top-level line of questioning.

| Action | Kind | What it produces | MVP |
|---|---|---|---|
| Dive in | `dive` | A deeper, more detailed treatment | ✓ |
| ELI5 | `eli5` | The simplest possible version | ✓ |
| Examples please | `example` | Concrete, preferably local examples | ✓ |
| Save as note | `note` | Capture span + context into Notebook | ✓ |
| Define | `define` | Meaning, usage, etymology | ✓ |
| Ask… (free text) | `ask` | One answer to a custom question about the span | ✓ |
| Visualize | `visual` | A diagram/chart sketch | later |
| Why it matters | `relevance` | Significance and connections | later |

**Rules**
- One primary action is visually emphasized (Dive in); the rest are peers.
- Fully keyboard-operable and screen-reader announced (see §13).
- Dismiss on Escape / click-away; focusing returns to the span.
- Repeat actions allowed (branch the same span twice for two angles).
- The Ask field is available on **every** selection (main text and inside any generated section); each submit is one node.

## 9. Actions: dives inline, asides on the side

An **action** is what the user does to a span (Dive in, ELI5, Examples, Define). Actions are split by kind, deterministically:

- **Dive in** and **Ask…** → an inline section below the content, recursively nested under dives.
- **ELI5 / Examples / Define** → a **side card** in the "Wider angles" rail.

### 9.1 Dive section anatomy

```
│▸ DIVE  "Rayleigh scattering"                       ✕
│   …streamed explanation, fully selectable…
│   │▸ DIVE  "violet"                                 ✕
│   │   …nested dive…
```

- The section renders **below the content it was taken from**, inside the reading sheet.
- Its header shows the collapse toggle (`▼`/`▶`), the kind, the title, a **backlink** (`↩`, shows where the section came from in the text) and remove. Depth is **not** shown as a label — it is conveyed by indentation, the trail and the results menu.
- Clicking the **title** toggles collapse (same as the chevron); the `↩` backlink scrolls to and highlights the source phrase instead.
- The body is fully selectable, so a dive can be taken again inside it — **recursion is inline**, not a new window.

### 9.2 Recursion
- Selecting inside a **dive** and choosing Dive in creates a **nested** dive beneath it.
- Selecting inside a **side card** and choosing Dive in still renders the dive below the main content (dives never nest inside the rail). Choosing ELI5 / Examples / Define always lands a card in the rail.
- Depth is unbounded; indentation is capped so deep chains stay readable, and each section collapses independently.

### 9.3 Wider angles (side rail)
- Lists every non-dive action as a collapsible card, newest last; the card for the active action is highlighted.
- Clicking a card's **title** collapses/expands it (like the toggle); `↩` scrolls to and highlights the phrase it came from in the reading sheet; `✕` removes it (with any descendants).
- Side cards are fully selectable, so they can spawn further dives (which go below) or more asides (which go to the rail).
- Ancestry is spatial: a dive's indent plus the trail breadcrumb.

### 9.4 Action kinds (visual language)
The inline marker on an actioned word is a **direction**, not a kind: `↓` means content below (dive or ask), `→` means an aside on the side, `★` a saved note (an anchor with more than one kind shows the combined arrows). Each kind still has its own colour and label — `dive`, `ask`, `eli5`, `example`, `define`, `note` (plus `visual`, `relevance` later) — used on the section / side-card header, so a word traces to its result. Dive and ask sections are full weight; side cards are lighter. Colour is never the only signal.

> Pushback logged: inline dives reintroduce reflow/deep-indentation risk (the reason the margin rail was proposed originally). Mitigations: only dives grow the sheet (asides are off to the side), per-section collapse, capped indentation, and the trail. If dives still prove too noisy at depth, the fallback is the single floating window (see the v2/v4 decision-log entries).

## 10. Trail

The trail is the ordered ancestry of the current focus: `Question › A › B › C`.

- The first crumb is the **base question** of the active path — the original question or a later one added from the composer — and scrolls to that question's sheet.
- Click any crumb to set focus there (the rail scrolls/filters to that subtree).
- The trail is **persistent history**, not just the current path; siblings are discoverable from it (a subtle "x other branches here" affordance).
- It doubles as a **study outline**: exportable as markdown (headings = trail, body = notes).
- Later: a **Map** toggle renders the same graph as a tree/graph for overview.

## 11. Notebook

- Saving a span creates a note capturing: the **selected text**, its **source context** (the paragraph it lives in), the **action/kind** used, and any **generated content** attached to it.
- Notes are editable, taggable, and searchable.
- **Assemble** (later): choose notes → produce an ordered outline/summary; export to markdown.
- Notebook is a drawer; it must not cover the reading column on desktop (rail-width overlay is acceptable).

## 12. Content model

### 12.1 Node schema

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable id |
| `parentId` | string \| null | `null` for the root answer |
| `kind` | enum | `root` \| `dive` \| `eli5` \| `example` \| `note` \| `define` \| `visual` \| `relevance` |
| `anchor` | `{ text, spanId }` | The selected span this node answers |
| `title` | string | Card heading |
| `body` | markdown | Streamed; may contain new selectable spans |
| `citations` | array | Sources for trust |
| `estReadSeconds` | number | Feeds the status bar |
| `status` | enum | `queued` \| `streaming` \| `done` \| `error` |
| `order` | number | Sibling ordering in the rail |

The entire app is a single **node graph**. The trail is a path, notes are flagged nodes, collapse is subtree state, and the map is the same graph rendered differently. One model, four views.

### 12.2 Generation contract (for the LLM phase)
Input: `(parentContext, anchor.text, kind, lens)`. Output: a node with `title`, `body`, `citations`, `estReadSeconds`, and **suggested follow-up anchors** (entities worth branching).

- **Stream** tokens; patch the node as they arrive.
- **Cache** by hash of `(parentId, anchor.text, kind, lens)`.
- **Prefetch** likely next branches (top entities in the streamed text) so dives feel instant.
- **Trust:** every non-trivial claim carries a citation; add a quiet "simplified for your level" note when ELI5/level changes fidelity.

### 12.3 Mock content plan (MVP)
No backend. Ship a hand-authored graph for one or two seed topics.

- **Seed:** *"Why is the sky blue?"*
- **Shape (illustrative):**
  - `root` — Why is the sky blue?
    - `dive` on "Rayleigh scattering"
      - `dive` on "why blue and not violet"
      - `eli5` on "wavelength"
      - `example` on "sunset colors"
    - `eli5` on the whole answer
    - `example` on "the sky on Mars"
    - `define` on "scattering"
- Aim for ~12–16 nodes with at least one 3-level chain, to stress nesting, collapse, trail, and notes.

## 13. Accessibility

- **Keyboard:** the reader is fully navigable. Provide an explicit **Explore mode** that turns prose into a grid of selectable spans (arrow keys to move, Enter to open the toolbar) — avoiding hundreds of tab stops in normal reading.
- **Screen readers:** streamed text announced via polite live regions; opening a branch moves focus to the card and announces "Branch opened: Dive into Rayleigh scattering"; collapsing announces the hidden count.
- **Selection toolbar** implemented as an accessible menu/dialog with roving focus; every action has a keyboard route and a text label.
- **Not color-only:** branch kinds carry text badges; anchors carry an underline/pattern, not just a tint.
- **Respect** `prefers-reduced-motion`, `prefers-contrast`, and `prefers-color-scheme`.
- **Zoom/reflow:** usable to 200% and at 320px width.

## 14. Responsive behavior

| Breakpoint | Behavior |
|---|---|
| ≥ 1100px | Two-zone: reading sheet + branch list (master) + floating branch window (detail). |
| 760–1099px | Reading sheet full width; branch list stacks below; window docks bottom. |
| < 760px | Reading full-width; the branch window becomes a full-width bottom layer (the replace + back-stack model already behaves like a navigation stack). Selection toolbar becomes a bottom bar. |

## 15. Visual direction — calm, near-flat, one accent

**History:** early versions used a luminous "Lumen" direction ("the page lights up as you learn") — an ambient canvas driven by `--energy`, motes and bloom. That read as too flashy and was retired in v6; the header is kept here as the record of that turn.

The visual system is **reading-first**: the prose and the branching structure carry the experience, not decoration. Delight comes from motion that clarifies (unfold, bloom) rather than atmosphere that competes.

- **Typography:** humanist serif for prose (*Source Serif 4*), geometric sans for UI (*Inter*), mono for labels/citations (*JetBrains Mono*). Large serif drop cap on the root answer.
- **Reading surface:** a quietly-shadowed "sheet" on a calm, near-flat dark canvas.
- **Calm, not luminous (v6):** the drifting ambient colour fields, rising motes and the `--energy` glow model were removed after they read as "too flashy". A single flat accent carries emphasis; gradients and glow-on-hover were stripped from buttons, the title, links and cards.
- **Branching as unfolding:** acting on a span emits a small **bloom** (a short radial pulse from the word) and the new section/card **unfolds** into focus (scale + blur → clear), rather than sliding panels. Calm prose, alive edges.
- **Color:** deep warm near-black `#0b0a10` (light toggle retained); one warm accent (`amber`); a distinct gem-like palette per branch kind.
- **Motion:** the core metaphor is *unfolding*, never bouncing/popping. Reduced motion collapses all of it.
- **Tone:** a quiet knowledge environment; restrained rather than premium-spectacle.


## 16. Edge cases & states

| State | Behavior |
|---|---|
| Empty | Home input with sample prompts; no reader until asked. |
| Calibrating | Lens card; reader skeleton behind it. |
| Streaming | Token reveal; skeleton holds layout; actions enabled once enough text exists. |
| Loading a branch | Card appears immediately with a shimmer; content streams in. |
| Error | Inline retry on the card; the rest of the session is unaffected. |
| Offline | Serve cached root + visited branches; new branches show "needs connection." |
| Rate-limited | Queue branches; show position; keep reading. |
| Very deep chain | Depth-4 prompt, collapse-all, jump-to-root. |
| Long content | Sticky headers, progress bar, collapse-all. |
| Ambiguous span | Toolbar offers options; "Dive in" uses full-sentence context. |

## 17. Metrics (what "immersive and effective" means)

- **Engagement:** time-to-first-branch, branches per session, median depth reached.
- **Branching health:** return-to-thread rate (guardrail working), collapse usage.
- **Retention of intent:** notes saved per session, trails exported/revisited.
- **Comprehension (later):** optional 1–2 question check-in after a branch.
- **Cost/latency (LLM phase):** tokens per branch, cache hit rate, prefetch accuracy.

## 18. MVP scope & non-goals

**MVP (prototype built)**
- Home → Calibration lens → Reader.
- Reading column + **branch list (master)** + **branch window (detail)** + trail.
- Selection toolbar: Dive in, ELI5, Examples, Save as note, Define.
- Actioned words underlined with a kind icon; no pre-highlighting.
- One floating window with replace + jump-back (recursion linearized) and breadcrumb.
- Notebook drawer (save/list/search notes).
- One seed topic with a scripted graph (`?demo=1`).

**Non-goals (v1)**
- Real LLM generation, accounts, sync, collaboration, quizzes, spaced repetition, offline PWA, i18n.

**Roadmap after MVP**
1. Wire a real LLM behind the same node interface (streaming, cache, prefetch, citations).
2. Persistence + lightweight profile (still non-PII).
3. Notebook "assemble" → outline/summary export.
4. Map view; share a trail.
5. Spaced repetition from saved trails.

## 19. Open questions

1. Serif vs sans body as the default (serif reads better long-form; sans feels more "product").
2. Should branches auto-expand suggested follow-ups, or always wait for the user?
3. Multi-select spans (compare A vs B) — v2?
4. Local-first vs cloud for notes/trail — affects privacy story and sync.
5. At what depth should indentation cap, and should deep siblings auto-collapse?

## 20. Decision log

- **v1 (this doc):** branch content in a growing margin rail; child cards nested inline; pre-highlighted "suggested" terms.
- **v2 (superseded):** replaced the growing rail with a **master–detail** model — a creation-ordered **branch list** plus a **single floating window**. Recursion is **linearized** (replace + jump-back + breadcrumb) rather than nested. Removed pre-highlighting; a word shows **underline + kind icon only after it is actioned**. Prev/next walk creation order.
- Rationale: the rail grew unbounded and the pre-highlights read as "already visited"; nested windows would sprawl. The tradeoff accepted is losing simultaneous parent/child view, recovered via the breadcrumb, jump-back, and the active-anchor highlight on the origin word.
- **v3 (visual):** an explicit **experience-first** push. Luminous ambient canvas that intensifies with branching (`--energy`), bloom-on-branch, and unfold transitions. Home keeps a centered hero input; the reading view uses a persistent bottom composer aligned to the reading column. Rationale: aesthetic quality drives engagement/motivation now; retention mechanics (retrieval, learner state) are deferred but designed to sit alongside this rather than replace it.
- **v4:** the **spark map was cut** — a passive overlay that did no work and read as "look what I did." Revisit only if it can earn a job (retrospective artifact / live orientation), not as decoration.
- **v5:** **action sections render inline** below the content (collapsible, titled with the selection, recursively nestable), replacing the floating branch window. The right panel is renamed **"Your actions"** (a collapsible index). Anchor marks were made **subtler** (dotted underline + tiny muted glyph). Home keeps a centered hero input; the reading view has a persistent bottom composer aligned to the reading sheet.
- **v6:** actions are **split by kind**. Only **Dive in** renders inline below the content (and nests under dives); **ELI5 / Examples / Define** render as **cards in the right rail**, now titled **"Wider angles"**, replacing the flat action index and its prev/next/expand controls. Rationale: the sheet should grow only along the main line of inquiry; asides belong beside it, not beneath it. Branches taken from a side card obey the same rule (dives go below, asides stay in the rail). Same change **calms the visuals**: the drifting ambient colour fields and rising motes are removed, buttons/title/links lose their gradients and glow, and the reading sheet sits on a flat surface — the "Lumen" energy model (`--energy`, bloom-on-action tied to it) is retired in favour of a quiet, near-flat dark canvas.
- **v7:** clicking an already-actioned phrase opens a **results menu** in the selection toolbar: the phrase's existing results are listed first (kind, phrase; click to jump + auto-expand), with the action buttons below so more branches can be created from the same menu. This fixes the earlier dead end where only the *latest* result was reachable (via the marker), hiding earlier ones. Rule for the marker: one result → jump to it; several → open the menu. Multiple results are always presented as a **list** (not a cycle), so each is directly reachable.
- **v8:** two changes. (1) The `L1`/`L2` depth labels were **removed** from section headers and the results menu — depth is conveyed spatially by indentation and the trail. (2) The bottom composer **appends a new question section below** the current reading instead of replacing the session (`addQuestion()`, `generateRoot()` in `content.js`), so a session can accumulate several questions. Each question section owns its nested dives; its asides join the shared side rail and its inline marker on the origin uses the same direction rules. Removing a question removes its descendants; the trail's leading crumb is the active path's base question.
- **v9:** added a free-text **Ask** field to the selection toolbar for questions the presets can't express. It creates **one** inline node (kind `ask`; anchor = the phrase, title = your question), scoped to the selection and available on every selection. Deliberately **single-shot** — no chat/thread state in the toolbar; deeper follow-ups go through normal selection, and the bottom composer stays the route for a fresh top-level question. Rationale: the presets cover the common angles; a scoped free-text ask covers the long tail; the two composers differ by **scope** (span vs. session), not by capability.
- **v10 (current):** section/side-card header affordances were made explicit. Clicking a section **title** now toggles collapse (previously it "focused" a section already in view and felt inert), and a small **backlink** (`↩`) jumps to and highlights the source phrase in the reading sheet — replacing the old side-card behavior where the title silently highlighted the origin. The chevron and title do the same thing; `↩` is the inverse of clicking the anchor. Headers are non-selectable (`user-select: none`) so clicking a title can never spawn a text selection and pop the toolbar, and the anchor highlight is cleared on outside-click and when its section is collapsed.

## 21. Implementation map

- `index.html` — app shell: top bar (lens chip, theme, notebook, new), home
  (centered input + samples), reader (trail, reading sheet with
  `#readingBody` + `#readingSections` for dives, and the `#actions` rail
  containing `#sideList` for asides), the bottom composer, selection `#toolbar`,
  the lens overlay, and the notebook drawer.
- `script.js` — all behavior. `state = { lens, question, nodes, rootId, order,
  activeId, counter, toolbarContext, marks, notes }`. Entry: `startReader()`
  (first question) and `addQuestion()` (later questions from the composer).
  Actions: `createSection()` (routes dives/asks to `diveHost(parent)` and asides
  to `#sideList`) / `createAsk()` → `registerMark()` → `applyMarks()`. Rail:
  `renderSide()` / `updateActions()` / `focusSection()`. Sections:
  `toggleSection()` / `removeSection()` (removal walks the graph via
  `descendantIds()`). Anchors/marks in `decorateAnchor()`; toolbar + results menu
  in `showToolbar()` / `renderToolbarResults()` / `performAction()`; trail in
  `renderTrail()` / `rootOf()`; `bloomAt()` is the only remaining
  experience-layer effect. Lens/theme/notes/composer are here too.
- `content.js` — the mock generator. `SEED_ROOT.body` is the answer text
  (`**phrase**` marks curated anchors). `LIBRARY` maps `normalizeKey(phrase)` →
  `{ dive, eli5, example, define }` bodies. `generateNode(parent, anchor, kind,
  lens)` returns `{ title, body, citations, estReadSeconds }` and falls back to
  `synthesize()`; `generateRoot(question, lens)` answers a brand-new question;
  `generateAsk(parent, anchor, question, lens)` answers a scoped free-text ask.
  **Swap these functions for a real LLM behind the same signatures.**
- `styles.css` — tokens in `:root` / `html[data-theme="dark|light"]`. Key
  selectors: `.anchor`/`.anchor-icon`, `.action-section`/`.as-*` (dives/asks),
  `.question-section` (questions), `.side-list`/`.side-card` (asides),
  `.toolbar-results`/`.toolbar-result`, `.toolbar-ask`, `.actions`, `.composer*`,
  `.bloom-pulse`.
  The ambient/mote layers and `--energy` were removed in v6.
- Demo: `?demo=1` seeds a session in `script.js`.
