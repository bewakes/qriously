# Qriously — Immersive Learning App: Interaction Spec

**Status:** Draft v1 · for review
**Surface:** `qriously/app/` (new; the landing designs are untouched)
**Scope of this doc:** product concept, interaction model, content model, and MVP plan. No implementation yet.

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
| Reader | Reading column + branch rail + trail. The heart of the app. |
| Branch card | A dive-in, ELI5, example, etc. Recursively branchable. |
| Selection toolbar | Contextual actions for the selected span. |
| Trail | Clickable ancestry; doubles as a study outline. |
| Notebook | Saved spans + context + generated text; assemble/export. |
| Map (later) | Graph overview of the trail/tree. |

## 5. Screen flow

```
HOME
 └─[ask]─► CALIBRATION LENS        (skippable → defaults)
              └─[start reading]─► READER
                    ├─[select span]─► SELECTION TOOLBAR
                    │                    ├─ Dive in ─┐
                    │                    ├─ ELI5     │→ BRANCH CARD (in rail)
                    │                    ├─ Examples ┘   ├─[select span]─► nested card…
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
│ TOP BAR   Qriously      [ lens ▾ ]   [ search ]  [ notes ] [◐] │
├───────────────────────────────────────────────────────────────┤
│ TRAIL     Root › Rayleigh scattering › Why not violet …        │
├───────────────────────────────┬───────────────────────────────┤
│                               │  BRANCH RAIL                   │
│  READING COLUMN               │  ┌─────────────────────────┐   │
│                               │  │ ▸ DIVE · "scattering"    │   │
│  Streamed prose. Every        │  │   …content…              │   │
│  span is selectable.          │  │   ┌──────────────────┐   │   │
│  Anchored spans stay          │  │   │ ▸ ELI5 · "wave-  │   │   │
│  highlighted.                 │  │   │   length"        │   │   │
│                               │  │   └──────────────────┘   │   │
│                               │  └─────────────────────────┘   │
├───────────────────────────────┴───────────────────────────────┤
│ STATUS    ~4 min · 3 branches open · small print / sources     │
└───────────────────────────────────────────────────────────────┘
```

- **Reading column:** measure 60–72ch, generous line-height. The only element that holds the "main thread."
- **Branch rail:** independently scrollable, sticky. Each card is a node; children stack beneath their parent with a depth gutter.
- **Trail:** horizontal, scrollable breadcrumb of the current path; click any crumb to focus that ancestor.
- **Status bar:** estimated read time, open-branch count, and a sources/￼small-print link.

### 7.2 Reading behavior
- Content **streams** token-by-token; a skeleton holds layout to avoid jumps.
- Paragraphs fade/slide in gently; nothing bounces.
- The column never reflows when a branch opens (that is the entire point of the rail).
- Long content: sticky subsection headers, progress indicator, and a "collapse all branches" control.

### 7.3 Anchor model
- Selecting a span marks it an **anchor**. Anchors persist as Highlights while their branch is open, and are listed in the trail.
- Clicking a branch card's quoted span scrolls the column to the original and re-flashes the anchor.
- Anchors are semantic (a phrase/sentence), not pixel ranges, so they survive re-renders.

## 8. Selection toolbar

Appears anchored just above the selection (or as a bottom bar on mobile). Shows the selected text as a quiet preview.

| Action | Kind | What it produces | MVP |
|---|---|---|---|
| Dive in | `dive` | A deeper, more detailed treatment | ✓ |
| ELI5 | `eli5` | The simplest possible version | ✓ |
| Examples please | `example` | Concrete, preferably local examples | ✓ |
| Save as note | `note` | Capture span + context into Notebook | ✓ |
| Define | `define` | Meaning, usage, etymology | ✓ |
| Visualize | `visual` | A diagram/chart sketch | later |
| Why it matters | `relevance` | Significance and connections | later |

**Rules**
- One primary action is visually emphasized (Dive in); the rest are peers.
- Fully keyboard-operable and screen-reader announced (see §13).
- Dismiss on Escape / click-away; focusing returns to the span.
- Repeat actions allowed (branch the same span twice for two angles).

## 9. Branch cards & nesting

### 9.1 Card anatomy

```
┌─────────────────────────────────────────────────┐
│ ● DIVE INTO               depth 2   ⌄   ⋯       │  ← kind badge · depth · collapse · menu
│ ───────────────────────────────────────────────  │
│ “Rayleigh scattering”                            │  ← quoted source anchor (click → jump)
│                                                  │
│ …streamed explanation…                           │  ← body, itself fully selectable
│                                                  │
│ ↩ Dive in  ↺ ELI5  ⊞ Examples  ★ Save   sources  │  ← quick actions + citations
└─────────────────────────────────────────────────┘
```

### 9.2 Nesting rules
- Children render **inside** the rail beneath their parent, indented one step and accent-colored by depth.
- Collapsing a card folds its entire subtree and shows a count ("3 branches hidden").
- Selecting text inside a card opens a new nested card — depth is unbounded.
- **Depth gutter:** a thin vertical line per level; hover highlights the lineage.
- **Focus mode:** expand any card to full reading width (others dim); return restores the rail.
- **Return to thread:** at depth ≥ 4, a gentle prompt appears: *"You're deep in the weeds — jump back to the main thread?"* with a one-click link. Non-blocking.

### 9.3 Branch kinds (visual language)
Each kind gets a distinct badge/accent so the rail is scannable at a glance: `dive`, `eli5`, `example`, `note`, `define`, `visual`, `relevance`. Color is never the only signal — badges carry text/icons too.

## 10. Trail

The trail is the ordered ancestry of the current focus: `Root › A › B › C`.

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
| ≥ 1100px | Two-zone: reading column + persistent branch rail. |
| 760–1099px | Reading column + narrower rail; rail may overlay as a drawer. |
| < 760px | Reading is full-width. Branching opens a **bottom sheet / full-screen** card with a swipe-back gesture; a compact trail sits under the top bar; the selection toolbar becomes a bottom action bar. |

## 15. Visual direction — "Lumen" (reading-first theme)

A purpose-built reading theme; working name **Lumen**.

- **Typography:** humanist serif for prose (candidate: *Source Serif 4* or *Newsreader*), geometric sans for UI (*Inter*), mono for citations/labels (*JetBrains Mono*).
- **Measure:** 60–72ch; line-height ≈1.7; clear heading hierarchy with sticky section labels.
- **Color:** calm, high-contrast. Dark default (`#0e0f13`) with a light toggle. One warm accent (`amber`) for anchors/active trail; a small, distinct palette for branch kinds; muted surfaces for cards.
- **Motion:** gentle only. Anchor highlight pulse, card slide-in, streaming reveal. Reduced-motion collapses all of it.
- **Tone:** the reader disappears; the content is the interface.

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

**MVP (mock content, no backend)**
- Home → Calibration lens → Reader.
- Reading column + branch rail + trail.
- Selection toolbar: Dive in, ELI5, Examples, Save as note, Define.
- Nested cards with collapse, depth gutter, focus mode, depth guardrail.
- Notebook drawer (save/list/search notes).
- One seed topic with a ~12–16 node scripted graph.
- Responsive (desktop two-zone; mobile bottom sheet) and accessible.

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
3. How aggressive should the depth guardrail be (nudge at 4, hard stop never)?
4. Multi-select spans (compare A vs B) — v2?
5. Local-first vs cloud for notes/trail — affects privacy story and sync.
6. Do we ever let a branch replace the main thread, or is the margin rail absolute?
