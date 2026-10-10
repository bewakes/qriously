# Qriously — End-to-End Architecture

**Status:** Proposed · awaiting approval before implementation.
**Scope:** How the prototype (`app/`) becomes a real, metered, lens-indexed
product on DeepSeek. Supersedes the "no backend" MVP stance in `PROJECT.md`.
**Companion docs:** `DATA-MODEL.md`, `API.md`, `PLAN.md`, and the interaction
spec at `app/INTERACTION-SPEC.md`.

---

## 1. The thesis

The product is **branching that preserves ancestry**. The atomic unit of
learning is the **span**, not the answer; any phrase is a doorway, and walking
through it must not destroy the path that led there. One graph powers reading,
actions, the trail, and notes.

Wiring generation changes three things, and they are three *different* designs:

1. **Lens** — a non-PII vector `{familiarity, depth, style, goal}`. It *shapes*
   generation and *describes* the audience a piece of content suits.
2. **Lens-indexed reuse** — generated content is stored tagged with the lens it
   was made for and reused for later *similar* questions/spans under a *similar*
   lens. This is the cost/latency lever; the index is a content corpus keyed by
   **concept × lens**, not merely an HTTP cache.
3. **Metered credits** — every generation draws on an authoritative ledger.
   Reuse is cheap or free. The meter is server-truth; the UI is optimistic.

The spine:

```
UI action ──► API ──► [concept + lens lookup] ──► hit? reuse ──► persist node
                                            └─► miss ─► DeepSeek (stream) ─►
                                            persist variant + node ─► debit ledger
         ◄── SSE tokens / usage ── UI updates optimistically, then reconciles
```

## 2. The central design decision: two layers, one DAG

The challenging part is that "threads and links between items" is really **two
graphs sharing vertices**:

- **Content layer (shared, immutable, reused).**
  `Concept` (what is being explained) → `ContentVariant` (a body generated for
  one `concept × kind × lens bucket × context fingerprint × prompt version`).
  Variants are never mutated; a new prompt/model produces a new version.

 - **Thread layer (per user, mutable traversal).**
  `Thread` → `Span` (a selected phrase in some node's body) → `Node` (a branch
  produced from a span: dive / eli5 / example / define / ask, or a root
  question, or a composer **`followup`**) → `Note` (a saved span). Ordering,
  collapse, and removal are thread-local. A `Thread` also carries a rolling
  **`summary`** for context.

A `Node` **references** the `ContentVariant` it renders. Therefore:

- Reuse = *many nodes point at one variant*. No copying, no drift, full
  provenance ("this answer was reused from an earlier query").
- Removing a node removes a thread edge, never shared content.
- The user's graph is a **DAG**: nodes link to spans/parents within the thread
  and to shared variants across threads.

**Which answers are shared (v23).** `root` (the opening question, no context)
and the span-scoped actions (`dive`/`eli5`/`example`/`define`/`ask`, grounded
only in shared content — a parent frame plus a bounded passage window) are reused
across users.
A composer **`followup`** is grounded in per-user trajectory (the root question,
`Thread.summary`, and a server-derived action log), so its context fingerprint is
unique per thread and it is **never shared** — it lives in `ContentVariant` but is
effectively a per-user row. This keeps the shared cache honest: an answer is only
reused when its inputs were shared.

A third, passive structure makes the knowledge reusable over time:
`ConceptLink(parent_concept, child_concept, kind)` records which concepts were
reachable from which, discovered as users branch. This is the substrate for
prefetching, "similar branches", and later retrieval.

See `DATA-MODEL.md` for the exact tables and invariants.

## 3. Lens encoding

The lens is four enums (defaults from the spec):

| Dimension | Values | Default |
|---|---|---|
| familiarity | `new` · `basics` · `expert` | `basics` |
| depth | `quick` · `solid` · `deep` | `solid` |
| style | `plain` · `analogy` · `technical` | `plain` |
| goal | `curious` · `project` · `exam` | `curious` |

- **`lens_bucket`** — the canonical string `familiarity:depth:style:goal`
  (e.g. `basics:solid:plain:curious`). 3×3×3×4 = 108 buckets. This is the
  index key. It is what makes "same content, similar lens" cheap to find.
- **`lens_vector`** — a small fixed-order numeric encoding of the same enums,
  so a semantic layer can weight distance per dimension (style and depth matter
  more to wording than goal does). It is model-independent, so it is stored now;
  embeddings and the `pgvector` index arrive with the semantic layer. Not used
  for the MVP lookup.
- The lens is snapshotted **per node**, because the spec allows mid-session
  re-tuning ("re-tunes subsequent branches; does not rewrite what's read").

**Lookup order** for a new node (MVP = layers 1–2, layer 3 stubbed):

1. **Exact**: `(concept, kind, lens_bucket, context_fingerprint, prompt_version)`.
2. **Broadened**: drop `context_fingerprint` (same concept + lens, any parent).
3. **Semantic** (later): nearest variant by `embedding` + `lens_vector` distance.
4. **Miss**: generate with DeepSeek, persist a new variant, index it.

`context_fingerprint` is a bounded hash of the immediate parent concept, not the
whole ancestry, so deep chains still share top-level explanations while
ambiguous spans stay context-sensitive. For an **`ask`** the key also folds in
the selected span: the same question asked about two different phrases under one
parent must not collapse to one cached answer (the question is the concept, so
without the span they would otherwise collide).

## 4. Stack

| Concern | Choice | Why |
|---|---|---|
| Backend | **Django 5 + DRF** | Batteries-included ORM/migrations/admin/auth; fast to build correctly. |
| API style | REST + **SSE** for streaming | SSE is one-directional and ideal for token streams; simpler than WebSockets. |
| Runtime | **ASGI (uvicorn/daphne)** | Long-lived streaming responses and async DeepSeek calls (`httpx`). |
| DB | **PostgreSQL** (+ **pgvector** when the semantic layer lands) | Relational graph + transactional ledger now; vector index added with embeddings in one store. |
| LLM | **DeepSeek** (`deepseek-flash` default, configurable; OpenAI-compatible) | Requested; streaming support. Key stays server-side. Model id is a config constant. |
| Frontend | **Vanilla ES modules + component layer** | Honors the no-build ethos; reusable components + CSS-token themes. |
| Local dev | **docker-compose** (Postgres/pgvector) | One-command parity; no external services needed. |

Python dependencies (indicative): `django`, `djangorestframework`,
`django-cors-headers`, `psycopg[binary]`, `httpx`, `dj-database-url`,
`python-dotenv`; dev: `pytest`, `pytest-django`, `ruff`. (`pgvector` returns with
the semantic layer.)

## 5. Backend layout & layering

Boundaries are by **responsibility, not framework**. Each context is a Django app
that owns its single entity (the Django model) plus a framework-free
`policies.py` and an orchestrating `services.py`. Cross-cutting pure code (lens,
safety, constants) lives in framework-free packages.

```
server/
├── manage.py
├── config/            # Django project: settings, urls, asgi, wsgi
├── core/
│   ├── constants.py   # pure tunables (no Django)
│   └── models.py      # shared abstract mixins (UUID, timestamps)
├── accounts/          # User, DeviceSession  ← the only entities
│   ├── models.py · policies.py · services.py · authentication.py
│   └── api.py · urls.py · admin.py · migrations/
├── credits/           # Wallet, CreditEntry  ← the only entities
│   ├── models.py · policies.py · services.py
│   └── api.py · urls.py · admin.py · migrations/
├── lenses/values.py   # Lens value object + bucket encoding (pure)
├── safety/            # Decision + ScreeningPolicy + AllowAllPolicy (pure)
├── telemetry/         # RequestLog
├── generation/        # DeepSeek client, prompts, SSE orchestration
└── content/ learning/ # content layer + thread layer
```

**Layering rules**

1. **One entity per concept.** The Django model *is* the entity — no parallel
   dataclasses, no mappers. A model may carry trivial in-memory behavior
   (`Wallet.debit`, `DeviceSession.revoke`) but a behavior method never issues
   queries.
2. **Pure core is framework-free.** `policies.py`, `lenses/`, `safety/`, and
   `core/constants.py` must not import Django. All decisions (pricing, ledger
   arithmetic, lens encoding, screening) live here and are unit-testable with no
   database.
3. **Services orchestrate and may use the ORM.** `services.py` runs use cases,
   owns `transaction.atomic`, and delegates every decision to policies. ORM
   imports stay out of `policies.py`, `lenses/`, and `safety/`.
4. **API modules are thin.** Serializers/views translate HTTP ↔ services; no
   business rules.

Other invariants: every write touching credits or content runs in one
transaction; money/credits are integers (micro-credits), never floats; every
generation request carries an idempotency key; screening runs **before** any
spend; every metered call is a `RequestLog`; no vendor SDK outside `generation/`.

### Configuration & constants (single source)

All tunables live in one place so we never sprinkle literals — `core/constants.py`
(and Django settings for deployment-level values). No pricing, model id, or
threshold should be duplicated in the flow code.

| Constant | Purpose | Initial value (tune freely) |
|---|---|---|
| `DEFAULT_MODEL` | DeepSeek model id | `deepseek-flash` |
| `MODEL_PRICE` | vendor cost per model (in/out per 1k micros) | `deepseek-flash`: 140 / 280 (constant; a versioned table arrives with billing) |
| `BASE_COST[kind]` | credit price per action kind | dive 12 · ask 10 · eli5 6 · example 6 · define 5 · root 15 |
| `DEPTH_MULTIPLIER` | lens depth scaling | quick 0.7 · solid 1.0 · deep 1.6 |
| `CACHE_HIT_RATIO` | fraction of price charged on reuse | `0.25` (never free) |
| `MAX_OUTPUT_TOKENS[kind]` | per-kind output cap sent to the model (bounds vendor cost) | dive 900 · ask 600 · eli5 320 · example 320 · define 200 · root 1200 (depth-scaled for open-ended kinds) |
| `SIGNUP_GRANT` | gift on account creation | `5000` micro-credits |
| `SCREENING_POLICY` | active safety policy | `allow_all` |
| `PROMPT_VERSION` | cache-key prompt version | `v4` |

Pricing is `ceil(BASE_COST[kind] * DEPTH_MULTIPLIER[depth] * (hit ? CACHE_HIT_RATIO : 1))`.


## 6. Query screening & safety

Every incoming question/span passes a **screening layer** before concept
resolution, cache lookup, or spend. It is a single interface plus a policy, so
the MVP can allow everything while a production policy is swapped in later
without touching callers.

- **Interface:** `screening.check(text, context) -> Decision(allow|block|review, category, score, provider)`.
- **MVP policy:** `AllowAllPolicy` — nothing is blocked; decisions are still
  recorded. This keeps the interception point real and testable from day one.
- **Position:** step 0 of the generation pipeline, **before credits are held**.
  A blocked request is never charged and nothing is generated.
- **Later policies:** deny-lists / cheap rules first, then a classifier or
  provider moderation; compose in order. A `review` outcome can queue rather
  than hard-block.
- **Response:** `422 content_blocked` with a generic, non-leaky message and a
  `category`; never echo harmful text back.
- **Audit:** the decision is returned to the pipeline; the `RequestLog` gains its
  `screening_*` fields when this integration lands (the MVP `RequestLog` is kept
  to the fields the pipeline writes today). The decision carries no PII.

Screening is deliberately **not** part of the content-cache key: a cache hit
still passes screening, because it is the *query* (not the cached text) that may
be disallowed.

## 7. Generation & metering flow

Every metered call opens a **`RequestLog`** up front (step 1), so credits,
tokens, vendor cost, cache layer, latency and screening decisions all attach to
one auditable context. This is what later answers "which kinds of queries cost
the most?" without re-plumbing.

1. **Open request**: authenticate device/user; create a `RequestLog` capturing
   endpoint, kind, lens bucket and the idempotency key. Resolve the `Wallet`.
   (More context — thread/node, client fingerprint — is added when those exist.)
2. **Screen**: `safety.screening.check(...)`. Blocked → `422`, request closed
   `failed` with `error_code=content_blocked`, **nothing charged**. (The
   `screening_*` fields land on `RequestLog` here.)
3. **Resolve concept** from the span/question (`normalize` → `Concept` upsert);
   build `context_fingerprint` from the parent concept.
4. **Lookup** variant (`content.reuse.find_variant`, exact → broadened).
5. **Authorize spend**: `cost = price(kind, lens.depth, cache_hit)`. A **cache
   hit is charged a configurable fraction** of the generated price — never free,
   so reuse keeps producing revenue while unit cost stays far below a fresh call.
   Check the balance covers `cost` (`select_for_update`); insufficient → `402`,
   request closed `failed` with `error_code=insufficient_credits`. (MVP checks
   the balance up front and charges at settle, so a failed generation is never
   charged and needs no refund; a dedicated reserve/settle `CreditHold` is
   deferred.)
6. **Hit**: skip generation; emit `meta(cache_hit=true, cost)`; replay the body
   as a single `token`; go to 8.
7. **Miss**: stream from DeepSeek, relay tokens over SSE; on completion persist a
   `ContentVariant` (idempotent on the request key), record `tokens_in/out`, and
   compute the **vendor cost** from the configured price (`core/constants.MODEL_PRICE`;
   a versioned table arrives with billing), stored separately from credits charged.
8. **Persist node**: create the `Node` linked to the variant (hit or miss),
   snapshot lens, `status=done`.
9. **Settle**: debit the wallet, write `UsageEvent` + `CreditEntry` (each
   referencing the request), close the request, emit `usage`.
10. **Failure**: mark the job and node `error`, close the request `failed`, emit
    `error`; nothing was charged, so there is nothing to refund, and the rest of
    the session is unaffected. Retry reuses the same idempotency key.

The MVP implements this as two services: **`prepare_generation`** (steps 1–5,
plus enqueuing a `GenerationJob` — also for a hit, so the stream can replay it)
and **`stream_generation`** (steps 6–10). Pricing is a small pure function in
`credits/policies.py` reading the constants above, so it can grow into
subscriptions/plans without touching the flow.

## 8. Streaming contract (SSE)

`POST /api/v1/generate` performs steps 1–4 synchronously enough to return
`{job_id, node_id, cache_hit, cost, balance}`; the client then opens
`GET /api/v1/generate/{job_id}/stream` and reads `text/event-stream` events:

```
meta   { request_id, node_id, concept, kind, lens_bucket, cache_hit, cost, balance }
token  { text }
done   { node_id, content_variant_id, title, est_read_seconds, gist, summary }
usage  { request_id, credits_charged, balance, cache_hit, lookup_layer,
         tokens_in, tokens_out, vendor_cost_micros, latency_ms }
error  { code, message, retryable }
```

Cached hits emit `meta` + a single `token` with the full body + `done` + `usage`
immediately, so the client has one code path. The frontend consumes SSE via
`fetch()` + a stream reader (not `EventSource`) so it can send `POST` bodies and
auth headers. Full request/response schemas are in `API.md`.

## 9. Frontend architecture (vanilla + component layer)

No build step; native ES modules served as-is. The prototype's behavior is
preserved; only the data source changes.

```
app/
├── index.html                 # shell (unchanged structure)
├── styles.css                 # imports tokens + components (or split)
├── src/
│   ├── core/     store.js (tiny observable state), dom.js (h/on), events.js
│   ├── api/      client.js (REST), sse.js (stream reader), auth.js (device token)
│   ├── content/  adapter.js (chooses API vs mock), mock.js (old content.js)
│   ├── components/ Anchor, ActionSection, SideRail, Toolbar, LensCard,
│   │               Composer, Trail, Notebook, CreditMeter, Toast, ThemeToggle
│   └── features/ home.js, reader.js
└── theme/  tokens.css, dark.css, light.css, skins/*.css (direction themes)
```

Principles:

- **Components are factory functions** returning a DOM node plus an `update`
  / `destroy` pair; they take explicit props and emit events — no globals.
  This keeps them reusable and testable without a framework.
- **One store**, unidirectional updates; rendering subscribes. Server truth
  reconciles over optimistic UI (especially the credit meter).
- **Theming** is CSS custom properties (already the pattern). `[data-theme]`
  carries dark/light; a separate `[data-skin]` attribute reserves the space for
  the landing design directions (daylight, playtime, atelier) as future
  product skins. Components never hard-code colors.
- **`content/adapter.js`** keeps the mock generator behind the same
  `generateRoot` / `generateNode` / `generateAsk` interface, selected by
  `?demo=1` or when the API is unreachable — so the app stays demoable offline.

## 10. Non-functional decisions

- **Money & credits:** integer micro-credits; ledger is append-only; balance is
  a cached sum guarded by row locks. No floats anywhere near a balance.
- **Idempotency:** client sends `Idempotency-Key` on generate/note writes;
  server stores it to make retries safe and double-charges impossible.
- **Auth:** anonymous device token (opaque, rotated) by default; upgrade attaches
  email/OAuth to the same user and keeps threads + credits. No PII is required
  to answer a question.
- **Trust/citations:** real sourcing is deferred. The `ContentVariant.citations`
  field exists and is populated as `unverified` model-provided references at
  most; the UI must not claim "verified sources" (corrects the prototype's
  "3 sources · verified" line).
- **Privacy:** lens is behavioral, not identity; never join lens to PII.
- **Request context & metering:** every metered call is a `RequestLog`;
  `CreditEntry` references it today, and `UsageEvent`, the screening decision and
  the cache layer will too — so "what kinds of queries cost the most?" becomes a
  query, not a new pipeline.
- **Vendor cost vs credits:** token usage is converted to vendor cost through the
  configured model price and stored per request, **separately** from the credits
  charged. This is how LLM cost-per-request is tracked without coupling
  it to the price users pay.
- **Observability:** per-generation `UsageEvent` + `RequestLog` yield the spec
  §17 metrics (tokens/branch, cache hit rate, cost/latency, and now cost by kind
  and lens) directly.
- **Rate limiting:** per-wallet throttling sits beside the credit gate (a
  rate-limited request is not charged).

## 11. MVP boundary

**In:** device auth; threads/questions/branches/notes; lens; DeepSeek
(`deepseek-flash`) streaming; concept+lens-tagged variant cache with exact +
broadened lookup (**hits charged a fraction, never free**); authoritative credit
ledger with mock grant and metering; a **screening hook** (allow-all policy) and
one `RequestLog` per metered call including vendor cost; SSE; the frontend wired
to the API with the mock as fallback; admin + tests.

**Out (designed-for, not built):** live Stripe/subscriptions; semantic embedding
lookup (`lens_vector` stored now; embeddings + pgvector arrive with it); real
moderation policies (interface + allow-all only),
retrieval-grounded citations; prefetch; cost-analytics dashboard (data captured,
no UI); collaboration/sharing; spaced repetition; the spark map.

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Reuse serves stale/inferior content | `prompt_version` + immutable variants; lookup can be pinned/invalidated per version; provenance is visible. |
| Semantic cache serves subtly wrong answers | MVP uses exact/broadened only; semantic is opt-in and threshold-guarded. |
| Double-charge on retries/refresh | Idempotency keys + transactional hold/settle. |
| Long SSE held connections strain workers | ASGI + async httpx; per-wallet connection cap. |
| Django coupling to a vendor | All DeepSeek calls behind `generation.llm` interface. |
| Lens fragments the cache too finely | Bucketing + broadened lookup; dimension weights reserved for the semantic layer. |
| Harmful/illegal queries | Screening interface is in the pipeline from day one (allow-all MVP); policies are swappable and run before any spend. |
| Charging for reuse feels unfair, discourages reuse | Hit price is a small configurable fraction (`CACHE_HIT_RATIO`), shown transparently; still a large discount vs a fresh call and far below vendor cost. |
| Unbounded/abusive usage burns credits or vendor spend | Per-wallet rate limiting beside the credit gate; `RequestLog` makes spend by query type visible. |
| Vendor costs invisible until too late | Configured model price + per-request `vendor_cost_micros` from day one, separate from credits charged. |

## 13. Decision log

- **A1:** Backend is Django 5 + DRF on Postgres/pgvector, ASGI, DeepSeek via an
  OpenAI-compatible streaming client; frontend stays vanilla ES modules with a
  component layer and token themes.
- **A2:** The persistent model is **two layers** — a shared, immutable
  `Concept`/`ContentVariant` content layer and a per-user `Thread`/`Span`/`Node`
  graph that **references** variants. Reuse is a reference, not a copy; the user
  graph is a DAG.
- **A3:** Lens is encoded as a discretized `lens_bucket` string (the index key)
  plus a stored, model-independent `lens_vector`; embeddings + pgvector arrive
  with the semantic layer. Lookup is exact → broadened (drop context) → semantic
  (later) → generate.
- **A4:** Credits are an append-only ledger of integer micro-credits with a
  transactional reserve/settle around each generation; cache hits are
  discounted. Payment providers are pluggable but not wired in the MVP.
- **A5:** Streaming is SSE over `fetch()`; cached hits replay through the same
  event sequence so the client has one path.
- **A6:** Citations are deferred; the UI stops asserting verification and the
  data model keeps a place for real sources.
- **A7:** A **screening layer** (`safety/`) runs as step 0 of every metered call,
  before spend. MVP policy is **allow-all**, but the interface, decision record
  and `422 content_blocked` path exist so a real policy drops in without
  touching callers. The cache key excludes screening (queries, not cached text,
  are screened).
- **A8:** Every metered call opens a **`RequestLog`**; `CreditEntry` references
  it today (and `UsageEvent`/screening will). Credits (revenue) and **vendor
  cost** (DeepSeek spend, via the configured `MODEL_PRICE`; a versioned table
  arrives with billing) are tracked separately per request. Cost analytics is
  deferred, but the
  data model supports it from day one.
- **A9:** **Cache hits are charged** a configurable fraction of the generated
  price (`CACHE_HIT_RATIO`, default 0.25) — never free — so reuse produces
  revenue while staying far cheaper than a fresh LLM call for the user.
- **A10:** All tunables (model id, prices, per-kind costs, depth multipliers,
  cache ratio, signup grant, screening policy, prompt version) live as
  **constants in one place** and are configurable without code changes in the
  flow.
- **A11:** Default generation model is **`deepseek-flash`** (configurable); the
  vendor client stays behind `generation.llm`.
- **A12:** Layering is by **responsibility**: one Django-model entity per concept
  (no parallel dataclasses/mappers), pure framework-free `policies.py` +
  `lenses/` + `safety/` for all decisions, `services.py` for use cases (the only
  place that uses the ORM besides models), and thin `api.py` for HTTP. The ORM
  never leaks into the pure modules.
