# Qriously — Data Model

**Status:** Proposed. Pairs with `ARCHITECTURE.md` (§2, §3) and `API.md`.
**DB:** PostgreSQL + pgvector. Django ORM models; UUID primary keys.

Two layers share vertices:

```
CONTENT LAYER (shared, immutable)         THREAD LAYER (per user, mutable)
Concept ──< ContentVariant                Thread ──< Node ──> ContentVariant (ref)
   │                                          │  ▲
   └──< ConceptLink >──┐                      │  │
                       └── Concept           Span ──< Note
                                              ▲
                                          Node.span_id
```

Reuse = many `Node` rows pointing at one `ContentVariant`. No copying.

---

## 1. Identity (`accounts`)

### `User`
Wraps `django.contrib.auth`'s user (custom user model from day one).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `email` | citext, null, unique | null until upgrade |
| `is_anonymous_device` | bool, default true | true = not yet claimed |
| `display_name` | text, null | non-PII; optional |
| `created_at` | timestamptz | |

### `DeviceSession`
Anonymous-first identity. The client stores the opaque token; the server stores
only its hash.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `user` | FK User, related `device_sessions` | one live user per session |
| `token_hash` | bytea, unique | never store the raw token |
| `label` | text, null | "Chrome on macOS" |
| `last_seen_at` | timestamptz | rotated on activity |
| `revoked_at` | timestamptz, null | |
| `created_at` | timestamptz | |

Anonymity here means: no email required to ask. `User.is_anonymous_device`
flips false on upgrade; `DeviceSession`s stay attached.

---

## 2. Credits (`credits`)

### `Wallet`
| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `user` | OneToOne User | one wallet per user (device → user) |
| `balance` | bigint, default 0 | **micro-credits**, cached; ledger is truth |
| `lifetime_granted` | bigint | lifetime credits granted |
| `lifetime_spent` | bigint | lifetime consumed |
| `updated_at` | timestamptz | |
| `version` | int | optimistic-lock counter |

### `CreditEntry` (append-only ledger)
| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `wallet` | FK Wallet | |
| `delta` | bigint | + grant/refund, − debit |
| `balance_after` | bigint | set under row lock |
| `entry_type` | enum | `grant` · `debit` · `refund` · `adjust` · `expire` |
| `reason` | enum | `signup_grant` · `generation` · `cache_reuse` · `failed_generation` · `plan_refill` · `purchase` · `manual` |
| `idempotency_key` | text, null, unique | dedupes retries |
| `request` | FK RequestLog, null | the request this credit change belongs to |
| `usage_event` | FK UsageEvent, null | links a debit to its generation |
| `metadata` | jsonb | pricing inputs, plan, provider ref |
| `created_at` | timestamptz | |

### `CreditHold` (reservation)
| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `wallet` | FK Wallet | |
| `amount` | bigint | reserved up-front |
| `generation` | FK GenerationJob, null | |
| `status` | enum | `held` · `settled` · `voided` |
| `created_at`, `settled_at` | timestamptz | |

No balance row is ever written without a matching ledger entry, inside one
transaction.

### `UsageEvent` (observability + pricing)
| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `wallet` | FK Wallet | |
| `request` | FK RequestLog, null | the request that produced this usage |
| `thread` | FK Thread, null | |
| `node` | FK Node, null | |
| `content_variant` | FK ContentVariant, null | |
| `kind` | text | action kind |
| `lens_bucket` | text | |
| `cache_hit` | bool | |
| `lookup_layer` | enum | `exact` · `broadened` · `semantic` · `generated` |
| `cost` | bigint | micro-credits **charged to the user** |
| `tokens_in`, `tokens_out` | int | null on cache hit |
| `vendor_cost_micros` | bigint, null | what the LLM call cost us; null on cache hit |
| `price_version` | text, null | `ModelPrice.version` used for the vendor cost |
| `latency_ms` | int | |
| `model` | text | e.g. `deepseek-flash` |
| `created_at` | timestamptz | |

Spec §17 metrics (tokens/branch, cache hit rate, cost/latency) are queries over
this table. Because `cost` (revenue) and `vendor_cost_micros` (our spend) are
separate columns on the same request, "which kinds of queries cost the most"
and margin-per-request are both simple aggregations.

### `RequestLog` (per-request context, `telemetry`)
The auditable context every credit change hangs off. One row per metered call,
created before screening/spend. **MVP subset** — only the fields the pipeline
writes today.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | the `request_id` surfaced to the client |
| `user` | FK User | |
| `wallet` | FK Wallet | |
| `endpoint` | text | e.g. `nodes.create`, `generate` |
| `kind` | text | action kind / `root` |
| `lens_bucket` | text | |
| `status` | enum | `pending` · `succeeded` · `failed` |
| `error_code` | text, null | |
| `credits_charged` | bigint, default 0 | set at settle |
| `vendor_cost_micros` | bigint, null | our LLM spend, separate from credits charged |
| `tokens_in`, `tokens_out` | int, null | |
| `latency_ms` | int, null | |
| `idempotency_key` | text, null, unique | |
| `created_at`, `completed_at` | timestamptz | |

**Deferred until their code exists** (nullable fields are cheap to add then):
`thread`/`node`/`concept`/`generation_job` FKs, `cache_hit`/`lookup_layer`
(reuse layer), `screening_*` (safety integration), `client_fingerprint`,
`price_version`.

### Vendor pricing (MVP)
Vendor prices live in **`core/constants.MODEL_PRICE`** rather than a table
(`deepseek-flash`: 140 input / 280 output micros per 1k). A versioned
`ModelPrice` table — so historical requests keep their original cost — replaces
the constant when billing needs price history (payments phase).

---

## 3. Content layer (`content`)

### `Concept`
The canonical "what is being explained".

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `key` | text, unique | `normalize(text)` — lower, strip punctuation, collapse ws |
| `text` | text | display form (first seen) |
| `kind_hint` | enum, null | `question` · `entity` · `phrase` · `term` |
| `created_at` | timestamptz | |

### `ContentVariant` (immutable, reused)
One generated body for a specific audience/context. This is the reusable unit.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `concept` | FK Concept | what it explains |
| `kind` | enum | `root` · `followup` · `dive` · `eli5` · `example` · `define` · `ask` · `visual` · `relevance` |
| `lens_bucket` | text | `fam:depth:style:goal` |
| `lens_vector` | float[] | fixed-order numeric lens encoding |
| `context_fingerprint` | text | hash of immediate parent concept (bounded); for `followup`, a hash of the thread trajectory |
| `prompt_version` | text | bump invalidates reuse |
| `title` | text | |
| `body` | text | markdown with `**anchor**` markers |
| `citations` | jsonb, default [] | `unverified` until real retrieval |
| `est_read_seconds` | int | computed server-side |
| `model` | text | producer model |
| `created_at` | timestamptz | |

**Uniqueness:** `(concept, kind, lens_bucket, context_fingerprint,
prompt_version)`. Exact lookup = this tuple. Broadened = drop
`context_fingerprint`. Never `UPDATE` a variant; ship a new one.

**Sharing boundary (v23).** `root` (no context) and the span-scoped actions
(`dive`/`eli5`/`example`/`define`/`ask`, grounded in shared content — a parent
frame and a bounded passage window) are **shared** across users. A **`followup`** is
grounded in per-user trajectory (root question + `Thread.summary` + a
server-derived action log), so its `context_fingerprint` is unique per thread and
it is **never reused across users** — it is effectively a per-user row even
though it lives in `ContentVariant`.

**Action log (derived, not stored).** For a follow-up prompt, the server builds
the user's action list on demand from the thread's `Node`/`Span`/`Note` rows,
mapping each `kind` to a verb (e.g. `dive` → "dived into '<anchor>'", `eli5` →
"asked for a simpler version of '<anchor>'", `note` → "saved a note"), ordered by
time and capped at the last ~25 actions. It is factual context for the model, not
a stored column.

Indexes: unique tuple above; btree on `(concept, kind, lens_bucket)`. The
`pgvector` extension, embedding columns and an HNSW index are added with the
deferred semantic layer (lookup layer 3), keyed to the chosen embedding model's
dimension — `lens_vector` is kept now because it is model-independent.

### `ConceptLink` (passive knowledge graph)
Records reachability discovered as users branch.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `parent` | FK Concept | |
| `child` | FK Concept | |
| `kind` | enum | the action kind that connected them |
| `weight` | int, default 1 | increment on recurrence |
| `unique_together` | `(parent, child, kind)` | |

Feeds prefetch now; retrieval/similar-branches later.

---

## 4. Thread layer (`learning`)

### `Thread`
A session / line of inquiry (the opening root plus its follow-ups).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `user` | FK User | owner |
| `title` | text | first question, editable |
| `lens` | jsonb | current default lens |
| `lens_bucket` | text | cached current bucket |
| `summary` | text | **rolling session summary**, updated as follow-ups are answered |
| `summary_updated_at` | timestamptz, null | when `summary` was last refreshed |
| `created_at`, `updated_at` | timestamptz | |

`summary` is per-user context for **follow-up** generation (see `Node.kind` below).
It is produced by the LLM, piggybacked on the answering generation, and is never
used for cross-user reuse.

### `Span`
The atomic anchor: a selected phrase inside some node's body.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `thread` | FK Thread | |
| `source_node` | FK Node | body the phrase lives in |
| `text` | text | semantic anchor (not a pixel range) |
| `concept` | FK Concept, null | resolved target concept |
| `start_offset`, `end_offset` | int, null | best-effort for highlighting |
| `created_at` | timestamptz | |

Spans are semantic (text-keyed) so they survive re-render/streaming; offsets are
advisory.

### `Node`
A branch/action or a root question; the traversal vertex.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `thread` | FK Thread | |
| `parent` | FK Node, null | null **only** for the thread's original root; a `followup` is a child of that root |
| `root` | FK Node, null | the root question of this subtree (self for roots; the thread root for follow-ups) |
| `kind` | enum | `root` · `followup` · `dive` · `eli5` · `example` · `define` · `ask` · `visual` · `relevance` |
| `gist` | text, null | one–two sentence summary of this node's answer; LLM-produced, piggybacked on generation |
| `span` | FK Span, null | the phrase this answers; null for `root` and `followup` |
| `content_variant` | FK ContentVariant, null | **shared ref**; null while streaming |
| `anchor_text` | text | denormalized from span for quick display |
| `title` | text | |
| `lens` | jsonb | lens snapshot at creation |
| `lens_bucket` | text | |
| `status` | enum | `queued` · `streaming` · `done` · `error` |
| `order` | int | sibling order |
| `depth` | int | for capped indentation / metrics |
| `collapsed` | bool | thread-local UI state |
| `reused` | bool | true if variant pre-existed |
| `created_at`, `updated_at` | timestamptz | |

Invariant: `root` is set for every node; a node's `thread` equals its parent's.
Removing a node removes its subtree (thread edges) only — never variants.

### `Note` (Notebook)
| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | |
| `thread` | FK Thread | |
| `span` | FK Span | the saved phrase |
| `text` | text | note text (defaults to span text) |
| `context` | text | source node title/paragraph |
| `tags` | text[] | |
| `created_at`, `updated_at` | timestamptz | |

Notes are session-scoped (`thread`), so a notebook is "everything saved in this
session" — there is no global across-session pile. A note is span-anchored: when
the user saves a phrase that was never branched, the service materializes the
`Span` on demand (`get_or_create_span`, reused per source node) rather than
adding a free-form note. Free-form / question-level notes are deferred.

---

## 5. Generation bookkeeping (`generation`)

### `GenerationJob`
Reconciles async streaming with idempotency and metering. Created by
`prepare_generation` for a miss and, in the MVP, **also for a cache hit** so
`GET /generate/{job_id}/stream` can replay the resolved variant without
re-resolving or re-charging. (Dropping hit jobs is a later optimization.)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID pk | the `job_id` streamed to the client |
| `request` | FK RequestLog, null | owning request |
| `wallet` | FK Wallet | |
| `thread` | FK Thread | |
| `node` | FK Node, null | the queued node this job fills |
| `concept` | FK Concept, null | |
| `kind`, `lens_bucket`, `context_fingerprint` | | lookup inputs |
| `prompt_version` | text | cache-key version used |
| `model` | text | e.g. `deepseek-flash` |
| `messages` | jsonb | the exact prompt sent (replay/debug) |
| `lens` | jsonb | lens snapshot used for this job |
| `cost` | bigint | price locked at prepare |
| `cache_hit` | bool | reused an existing variant |
| `lookup_layer` | enum | `exact` · `broadened` · `semantic` · `generated` |
| `idempotency_key` | text, unique | client-supplied |
| `status` | enum | `pending` · `streaming` · `done` · `error` |
| `error_code`, `error_message` | text, null | |
| `created_at`, `completed_at` | timestamptz | |

---

## 6. Lens encoding (shared)

```python
FAMILIARITY = {"new": 0, "basics": 1, "expert": 2}
DEPTH       = {"quick": 0, "solid": 1, "deep": 2}
STYLE       = {"plain": 0, "analogy": 1, "technical": 2}
GOAL        = {"curious": 0, "project": 1, "exam": 2}

DEFAULT_LENS = {"familiarity": "basics", "depth": "solid",
                "style": "plain", "goal": "curious"}

# bucket: "basics:solid:plain:curious"  (the index key)
# vector: [fam, depth, style, goal] normalized to [-1, 1] by inverse index,
#         used only for semantic distance weighting later.
```

A lens is stored on the `Thread` (default) and snapshotted on each `Node`
(so mid-session recalibration affects only subsequent branches).

---

## 7. Core queries

- **Exact/broadened reuse** — `ContentVariant.objects.filter(concept=…, kind=…,
  lens_bucket=…, context_fingerprint=…, prompt_version=…)` then drop
  `context_fingerprint`.
- **Thread snapshot** — load `Thread` + `Span`s + `Node`s + `Note`s; the frontend
  rebuilds the tree by `parent`/`order`.
- **Subtree removal** — recursive CTE over `Node.parent`.
- **Balance** — `Wallet.balance` under `select_for_update`; ledger sums for audit.
- **Cache-hit rate / cost** — aggregate `UsageEvent` by `cache_hit`, `kind`,
  `lens_bucket`.
- **Spend by query type** — aggregate `UsageEvent`/`RequestLog` by `kind`,
  `concept`, `lens_bucket`, `cache_hit`, summing `cost` (revenue) and
  `vendor_cost_micros` (our spend). This is the "what costs the most" query.
- **Margin** — `sum(cost) - sum(vendor_cost_micros)` per request/day/model.

## 8. Open model questions

1. Do `Span`s need disambiguation keys (same phrase twice in one body)?
   MVP: first occurrence, semantic match resolves to the same spirit as the
   prototype.
2. Should `ContentVariant` be anonymized/global, or scoped per tenant? MVP:
   global (this is what makes reuse pay off), with provenance retained.
3. Retention of `GenerationJob`/`UsageEvent`/`RequestLog` for observability vs
   privacy — decide a window before launch (`RequestLog` carries a hashed
   client fingerprint, not raw PII).
