# Qriously — Build Plan

**Status:** Proposed · awaiting approval. This is the execution order for
`ARCHITECTURE.md` / `DATA-MODEL.md` / `API.md`. Each phase is independently
verifiable and leaves the product demoable.

Guiding rules: no phase breaks the existing prototype (`app/` stays runnable
with `?demo=1` throughout); every phase ends with docs updated; the app's
interaction model is frozen (see Decision log, spec v10) — this work wires it to
a backend, it does not redesign it.

---

## Phase 0 — Docs & orientation (this turn)

- [x] `docs/ARCHITECTURE.md`, `docs/DATA-MODEL.md`, `docs/API.md`, `docs/PLAN.md`.
- [x] Update `PROJECT.md` (backend era) and `AGENTS.md` (layout + commands).
- [x] Add a spec decision-log entry (v11: "server-backed, lens-indexed reuse")
      referencing these docs.
- [ ] Approve stack + decisions; freeze the API contract for Phase 3.

**Done when:** the plan is accepted and the API/model docs are frozen.

---

## Phase 1 — Backend foundation

Scaffold and prove the boring parts.

- Django 5 + DRF project under `server/`; split settings; `.env.example`.
- `docker-compose.yml` with Postgres + pgvector; `make`/README commands.
- `core/constants.py` (single source for model id, `BASE_COST`, `DEPTH_MULTIPLIER`,
  `CACHE_HIT_RATIO`, `SIGNUP_GRANT`, `SCREENING_POLICY`, `PROMPT_VERSION`) — no
  literals in flow code.
- Custom `User`, `DeviceSession`; anonymous device auth + `POST /auth/device`.
- `Wallet` + append-only `CreditEntry` + `signup_grant` on creation. Gift is per
  **account**, no decay for now.
- `telemetry`: `RequestLog` + versioned `ModelPrice` models and admin; every
  metered call will create one `RequestLog`.
- `safety` app scaffold: `screening.check()` interface + `AllowAllPolicy`.
- `select_for_update` spend helper + a `credits/pricing.py` reading constants.
- `GET /me`, `GET /credits/balance`, `GET /credits/ledger`.
- Admin registered for all models; health check endpoint.
- `ruff` + `pytest` wired; model + auth + ledger + pricing tests.

**Done when:** a device can get a token, receive a mock grant, read its balance,
and the ledger records every change; tests green.

---

## Phase 2 — Content layer & lens index

The reuse engine, still without the LLM.

- `Concept` normalization + upsert; `ContentVariant` with unique-lens tuple,
  `lens_bucket`, `lens_vector`, `context_fingerprint`, `prompt_version`.
- `content.reuse.find_variant()` implementing exact → broadened lookup.
- `ConceptLink` recorded when a branch resolves.
- Unit tests for normalization, bucketing, exact/broadened hits, and
  immutability (new prompt version never mutates old rows).
- Seed a few `ContentVariant`s so hits are demonstrable before DeepSeek.

**Done when:** given `(concept, kind, lens)`, the service deterministically
returns an existing variant or a clean miss, with tests.

---

## Phase 3 — Generation, streaming, metering (the spine)

- `generation.llm`: OpenAI-compatible DeepSeek streaming client behind an
  interface; `DEEPSEEK_API_KEY` from env; `DEFAULT_MODEL=deepseek-flash`; timeout
  + retry policy.
- Prompt builder: system prompt parameterized by lens; instructs bounded length
  (depth), style (plain/analogy/technical), assumed knowledge (familiarity),
  framing (goal); instructs `**anchor**` markers for branchable phrases; no
  fabricated "verified sources".
- Orchestration: **open `RequestLog` → screen (allow-all) → resolve concept →
  lookup → hold credits → (hit: reuse | miss: stream) → persist variant + node →
  settle/debit → `UsageEvent`**, all referencing the request.
- `GenerationJob` created only on a miss; `tokens_in/out` converted to
  `vendor_cost_micros` via `ModelPrice` and stored separately from the credits
  charged.
- **Cache hits are charged** `CACHE_HIT_RATIO × price` (never free).
- SSE endpoints (`POST /generate`, `GET /generate/{job_id}/stream`) with the
  event shape in `API.md` (including `request_id`, `vendor_cost_micros`); cached
  hits replay through the same sequence.
- Screening blocks → `422`, request `blocked`, nothing charged; failures void the
  hold and emit `error`; idempotency key dedupes retries.
- `POST /threads`, `POST /threads/{id}/nodes`, `GET /threads/{id}`,
  `PATCH /nodes/{id}`, `DELETE /nodes/{id}`, notes CRUD, `GET .../outline`.
- Tests: metering math, fractional cache-hit cost, refund-on-failure,
  idempotent replay, vendor-cost calculation, screening block path, graph
  snapshot round-trip, subtree removal.

**Done when:** curl can start a thread, stream a real DeepSeek answer, create a
nested dive, and show the balance decremented — and a repeat request hits the
cache and is charged only the small fraction (with `vendor_cost_micros` null).

---

## Phase 4 — Frontend wiring & component extraction

Refactor in place; the DOM result should look identical.

- Extract `src/core` (store, dom), `src/api` (client, sse reader, auth),
  `src/components`, `src/features`; move `content.js` → `src/content/mock.js`.
- `content/adapter.js` selects API vs mock (`?demo=1`, offline, or `VITE`-less
  runtime flag).
- Device auth bootstrap; persist token; `GET /me`.
- Replace `generateNode`/`generateRoot`/`generateAsk` with API calls; consume
  SSE and feed the existing `streamInto` path.
- `CreditMeter` component in the top bar/status line: optimistic decrement,
  reconcile on `usage`; fractional charges on reuse are shown, not hidden; `402`
  opens a quiet "out of credits" state; `422` shows a gentle "can't help with
  that one" without leaking the category.
- Preserve behavior: anchors/markers/results menu, collapse, trail, notes,
  reduced-motion, keyboard routes.
- Theming: split tokens into `theme/tokens.css`; keep `[data-theme]` for
  dark/light; reserve `[data-skin]` for the landing directions.
- Error/retry UI per node; offline fallback to mock with an honest status.

**Done when:** the app runs end-to-end against the backend with the same feel;
`?demo=1` still works with no server.

---

## Phase 5 — Hardening & polish

- Rate limiting beside the credit gate; request size/shape validation.
- Observability over `RequestLog` + `UsageEvent`: cache hit rate, cost/node,
  tokens/branch, p95 latency, **spend and margin by kind/lens** (spec §17). Data
  is captured in Phases 1–3; this phase adds the admin summary/view.
- CORS/deploy config; secrets handling; retention decision for request/usage logs.
- Accessibility re-audit of the new async states (live regions for streamed
  tokens, credit changes announced politely).
- Mobile composer/credits layout layout pass.
- Final doc pass; update `INTERACTION-SPEC.md` generation contract §12.2 to name
  the real backend.

**Done when:** metrics are visible, the app is deployable, and docs match code.

---

## Later (designed-for, not in this plan)

1. **Semantic reuse** — fill `Concept`/`ContentVariant` embeddings and enable
   lookup layer 3 with lens-weighted distance.
2. **Payments** — Stripe checkout/webhooks → `CreditEntry(purchase)`; plans and
   subscriptions; refill jobs.
3. **Query-cost analytics** — a proper dashboard over `RequestLog` to find which
   kinds/concepts/lenses burn the most credits and vendor spend. (MVP captures
   the data; this builds the view.)
4. **Moderation policies** — replace `AllowAllPolicy` with tiered rules + a
   classifier; add a `review` queue; measure policy impact from `RequestLog`.
5. **Grant anti-abuse** — the per-account gift with **exponentially decaying**
   grants for new signups (or an IP/device guard), if device farming appears.
6. **Grounded citations** — retrieval step feeding real sources; update the
   trust UI.
7. **Prefetch** — use `ConceptLink` + depth to warm likely next branches.
8. Map view, sharing a trail, spaced repetition.

---

## Acceptance criterion for the MVP (end-to-end)

A first-time visitor can, without an account: ask a question, calibrate a lens,
read a streamed DeepSeek (`deepseek-flash`) answer, dive/ELI5/define/example/
save, ask a new question below, and see a credit balance that goes down per
generation and down by only a small **fraction** on a repeated/similar request —
all persisted so a reload restores the thread, with every charge traceable to a
`request_id` and the mock still available offline.

---

## Decisions locked (from review)

1. **Repo shape:** `server/` alongside `app/` in this monorepo. ✅
2. **Numbers:** tunable constants in `core/constants.py` (see `ARCHITECTURE.md`
   §5); initial values are placeholders, changed without touching flow code. ✅
3. **Model:** default `deepseek-flash` (configurable); `deepseek-reasoner` for
   `depth=deep` remains an option, not default. ✅
4. **Anonymous credit reset:** gift per account, **no decay** for now (single-user
   testing); decay/anti-farming deferred. ✅
5. **Cache hits are charged** a configurable fraction — never free. ✅
6. **Screening** exists in the pipeline from day one (allow-all MVP). ✅
7. **Per-request metering** (`RequestLog`) + **vendor LLM cost** tracked
   separately from credits charged, from day one. ✅

