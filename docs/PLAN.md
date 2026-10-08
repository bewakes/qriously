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

Scaffold and prove the boring parts. **Status: complete** (PRs #2, #5, #9, #10, #11;
layering codified in #4). All backend code follows the layering rule in
`ARCHITECTURE.md` §5: the Django model is the single entity, decisions live in
framework-free `policies.py`/`lenses/`/`safety/`, services own transactions, and
`api.py` is thin.

- [x] Django 5 + DRF project under `server/`; env-driven settings; `.env.example`.
- [x] `docker-compose.yml` with `pgvector/pgvector:pg16`; README commands.
- [x] `core/constants.py` (single source for model id, `BASE_COST`,
      `DEPTH_MULTIPLIER`, `CACHE_HIT_RATIO`, `SIGNUP_GRANT`, `SCREENING_POLICY`,
      `PROMPT_VERSION`) — no literals in flow code.
- [x] Custom `User`, `DeviceSession`; anonymous device auth + `POST /auth/device`.
- [x] `Wallet` + append-only `CreditEntry` + `signup_grant` on creation (per
      account, no decay). `Credits/policies.price()` handles the fractional
      cache-hit charge.
- [x] `telemetry`: `RequestLog` + versioned `ModelPrice` (+ seed) and admin;
      every metered call creates one `RequestLog`. `CreditEntry.request` links a
      charge to its request; `vendor_cost_micros` tracked separately.
- [x] `safety`: pure `ScreeningPolicy` interface + `AllowAllPolicy` + registry.
- [x] `select_for_update` spend helper + `credits/policies.py` reading constants.
- [x] `GET /me`, `GET /credits/balance`, `GET /credits/ledger`.
- [x] Admin registered for all models; `/health` + `/health/ready`.
- [x] `ruff` + `pytest` wired; constants, auth, ledger, pricing, telemetry,
      screening and a layering-guard test (pure modules never import Django).

**Done when:** a device can get a token, receive a mock grant, read its balance,
and the ledger records every change — with each charge traceable to a request
and vendor cost recorded separately; tests green.

---

## Phase 2 — Content layer & lens index

The reuse engine, still without the LLM. **Status: complete.** New `content`
app (`Concept` / `ContentVariant` / `ConceptLink`); pure text helpers in
`content/text.py`; lookup in `content/reuse.py`; use cases in
`content/services.py`; `python manage.py seed_content` seeds demonstrable hits.

- [x] `Concept` normalization + upsert; `ContentVariant` with unique-lens tuple,
      `lens_bucket`, `lens_vector`, `context_fingerprint`, `prompt_version`.
- [x] `content.reuse.find_variant()` implementing exact → broadened lookup.
- [x] `ConceptLink` recorded when a branch resolves.
- [x] Unit tests for normalization, bucketing, exact/broadened hits, and
      immutability (new prompt version never mutates old rows).
- [x] Seed a few `ContentVariant`s so hits are demonstrable before DeepSeek.

**Done when:** given `(concept, kind, lens)`, the service deterministically
returns an existing variant or a clean miss, with tests. ✅

---

## Phase 3 — Generation, streaming, metering (the spine)

**Status: in progress.** The LLM client, prompt builder, metering and the
generation orchestration service are in; the HTTP/SSE surface is next. The
`learning` app (Thread/Span/Node/Note) and the metering models
(`UsageEvent`, `GenerationJob`) have landed.

- [x] `generation.llm`: OpenAI-compatible DeepSeek streaming client behind an
      `LLMClient` interface; `DEEPSEEK_API_KEY` from env;
      `DEFAULT_MODEL=deepseek-flash`; timeout + retry policy.
- [x] Prompt builder parameterized by lens and kind; assumes knowledge
      (familiarity), bounds length (depth), sets voice (style) and framing
      (goal); instructs `**anchor**` markers; no fabricated "verified sources".
- [x] Orchestration split in two: `prepare_generation` (**open `RequestLog` →
      screen (allow-all) → resolve concept → exact/broadened lookup →
      price/guard credits → enqueue `GenerationJob`**) and `stream_generation`
      (**hit: replay | miss: stream → persist variant + node → settle via
      `record_generation` → close request**). Failures mark the job/node `error`
      and charge nothing.
- [x] `GenerationJob` (`generation`) and `UsageEvent` (`credits`) bookkeeping;
      `tokens_in/out` → `vendor_cost_micros` (via the constant `MODEL_PRICE`)
      stored separately from credits charged; every metered call a `RequestLog`.
- [x] **Cache hits charged** `CACHE_HIT_RATIO × price` (never free).
- [x] Tests: metering math, fractional cache-hit cost, vendor-cost calculation,
      charge-on-success (no charge on upstream failure), orchestration
      hit/miss/error, subtree removal.
- [ ] SSE endpoints (`POST /generate`, `GET /generate/{job_id}/stream`) with the
      event shape in `API.md`; cached hits replay through the same sequence.
- [ ] `POST /threads`, `POST /threads/{id}/nodes`, `GET /threads/{id}`,
      `PATCH /nodes/{id}`, `DELETE /nodes/{id}`, notes CRUD, `GET .../outline`.
- [ ] Remaining tests: idempotent replay, screening-block path, graph snapshot
      round-trip.

**Done when:** curl can start a thread, stream a real DeepSeek answer, create a
nested dive, and show the balance decremented — and a repeat request hits the
cache and is charged only the small fraction (with `vendor_cost_micros` null).
**Not yet: the HTTP surface above.**

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

