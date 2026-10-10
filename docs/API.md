# Qriously — API Contract (v1)

**Status:** Proposed. Implements the flows in `ARCHITECTURE.md` over the schema
in `DATA-MODEL.md`.
**Base URL:** `/api/v1` · **Format:** JSON (except SSE) · **Auth:** `Authorization: Bearer <device_token>`.
**Idempotency:** mutating generation/note writes accept an `Idempotency-Key`
header; replays return the original result and never double-charge.

---

## 1. Auth & identity (anonymous-first)

### `POST /auth/device`
Creates an anonymous user + wallet + device session. No body required.

```json
200 {
  "token": "dev_xxx",              // opaque; shown once
  "user": { "id": "uuid", "is_anonymous_device": true },
  "wallet": { "balance": 5000, "currency": "micro_credits" },
  "granted": 5000
}
```
The client persists `token` and sends it on every request. A `signup_grant` is
written to the ledger on first creation.

### `POST /auth/upgrade`
Attaches email/OAuth credentials to the current anonymous user (keeps threads +
credits). Body: provider payload + `{ provider: "email"|"google", ... }`.

### `GET /me`
```json
200 {
  "user": { "id": "uuid", "email": null, "is_anonymous_device": true },
  "wallet": { "balance": 4820, "lifetime_granted": 5000, "lifetime_spent": 180 },
  "plan": { "code": "free", "name": "Free" }
}
```

---

## 2. Threads & the graph

### `POST /threads`
Start a session; optionally creates the first root question immediately.

```json
{ "question": "Why is the sky blue?", "lens": { "familiarity": "basics", "depth": "solid", "style": "plain", "goal": "curious" } }
200 { "thread": { "id": "uuid", "title": "Why is the sky blue?", "lens": {...} },
      "question_node_id": "uuid" }
```
If `question` is present, a root node is created and generation is kicked off
(returned in the same shape as `POST /generate`).

### `GET /threads`
Lists the device user's sessions, newest activity (`updated_at`) first,
cursor-paginated (`?cursor=&limit=`). Returns `{ results, next }` where each
result is `{ id, title, lens, lens_bucket, created_at, updated_at }`. Owner-scoped;
never returns another user's threads. Powers the app's left session-history pane.

### `GET /threads/{id}`
Full snapshot for rendering/restoring a session.
```json
200 {
  "thread": { "id", "title", "lens", "created_at" },
  "nodes": [ { "id", "parent_id", "root_id", "kind", "anchor_text", "title",
               "lens_bucket", "status", "order", "depth", "collapsed",
               "reused", "content_variant_id", "body", "citations",
               "est_read_seconds" } ],
  "spans": [ { "id", "source_node_id", "text", "concept_id" } ],
  "notes": [ { "id", "span_id", "text", "context", "tags" } ]
}
```
`body` is included for `done` nodes (the index is the cache; no token replay).

### `PATCH /threads/{id}`
Update `title` or default `lens` (affects subsequent branches only).

### `DELETE /threads/{id}`

---

## 3. Nodes (branches & questions)

### `POST /threads/{id}/nodes`
Creates a branch from a selected span, or a **follow-up** question from the
composer. This is the single entry point for "act on a span" or "ask the thread".

```json
{
  "parent_node_id": "uuid|null",   // null only for the thread root
  "kind": "dive|eli5|example|define|ask|followup",
  "span": { "text": "Rayleigh scattering" },   // required unless kind=followup
  "question": "how is the target calculated?", // required for ask/followup
  "lens": { ... },                            // optional override for this node
  "idempotency_key": "uuid"
}
```
A **`followup`** is the composer case: `parent_node_id` is the thread's
**original root** (never null — a follow-up never starts a new root), `span` is
omitted, and `question` is required. It renders top-level but is parented to the
root for context. Response (`202`) returns a generation job descriptor (see §4).
Persistence and metering are driven by the stream.

### `PATCH /nodes/{id}`
Thread-local UI state: `{ "collapsed": true }`, `{ "title": "..." }`.

### `DELETE /nodes/{id}`
Removes the node **and its subtree** (thread edges only; variants persist).

---

## 4. Generation & streaming

### `POST /generate`
Low-level generation used internally by `POST /threads/{id}/nodes`. Resolves the
concept, checks the lens-indexed cache, authorizes spend, and returns a job.

```json
{
  "thread_id": "uuid",
  "parent_node_id": "uuid|null",
  "kind": "dive",
  "span": { "text": "Rayleigh scattering" },
  "lens": { ... },
  "idempotency_key": "uuid"
}
200 {
  "request_id": "uuid",
  "job_id": "uuid",
  "node_id": "uuid",
  "cache_hit": true,
  "lookup_layer": "exact",
  "cost": 30,
  "balance": 4790,
  "stream_url": "/api/v1/generate/{job_id}/stream"
}
```
On a cache **hit**, `cost` is the configured fraction of the generated price
(`CACHE_HIT_RATIO`, never 0) and `job_id` is a short-lived replay job. On a
**miss**, `cost` is the full price and a real generation job is created.

**Insufficient credits → `402`**:
```json
{ "error": "insufficient_credits", "required": 120, "balance": 40,
  "top_up_url": null }
```
**Blocked by screening → `422`**:
```json
{ "error": "content_blocked", "category": "unsafe", "request_id": "uuid" }
```
Nothing is generated or charged on either a `402` or a `422`; both requests are
recorded (`denied` / `blocked`) on the `RequestLog`.

### `GET /generate/{job_id}/stream`  (SSE, `text/event-stream`)
The client reads this with `fetch()` + a stream reader (POST bodies + auth header
make `EventSource` unsuitable). Event sequence:

```
event: meta
data: {"request_id":"...","node_id":"...","concept":{"id":"...","text":"Rayleigh scattering"},
       "kind":"dive","lens_bucket":"basics:solid:plain:curious",
       "cache_hit":false,"cost":120,"balance":4700}

event: token
data: {"text":"Rayleigh scattering is the scattering of light "}

event: token
data: {"text":"by particles much smaller than the wavelength."}

event: done
data: {"node_id":"...","content_variant_id":"...","title":"Rayleigh scattering, in detail",
       "est_read_seconds":54,"gist":"Explains why short wavelengths scatter more.",
       "summary":"User is exploring why the sky is blue; covered Rayleigh scattering."}

event: usage
data: {"request_id":"...","credits_charged":120,"balance":4700,"cache_hit":false,
       "lookup_layer":"generated","tokens_in":812,"tokens_out":337,
       "vendor_cost_micros":1840,"latency_ms":2410}

event: error
data: {"code":"upstream_timeout","message":"DeepSeek timed out","retryable":true}
```
**Cache hits replay the same sequence**: `meta` (with `cache_hit:true` and the
fractional `cost`) → one `token` carrying the full body → `done` → `usage` (with
`vendor_cost_micros:null`, since no LLM call was made). One client code path.

**`gist` / `summary` (v23).** Generated answers carry a short `gist` (part of the
variant, so a cache hit replays it) and — on **follow-up** generations, which are
always per-user and never cross-user cache hits — an **updated session summary**
written to `Thread.summary`. The model emits both after the body; the server
splits them off the stream (they never appear as `token` events). A cache hit has
no LLM call, so it does not refresh the summary; the next follow-up catches up.

`error` is terminal for the job; the hold is voided/refunded and the node is
marked `error` with an inline retry affordance. Retry reuses the same
`Idempotency-Key` to avoid a second charge.

---

## 5. Notebook

### `POST /threads/{id}/notes`
A note is span-anchored. Anchor it either to an existing span, or to a source
node plus the saved phrase — in which case the phrase is materialized as a
`Span` (reused if the same phrase was already saved from that node):
```json
{ "span_id": "uuid", "text": "optional override", "tags": ["light"] }
{ "source_node_id": "uuid", "text": "scattered blue light", "context": "Why is the sky blue?" }
```
`text` defaults to the span's text and `context` to its source node's title.
Missing both anchors → `400`.

### `GET /threads/{id}/notes`
Cursor-paginated (`?cursor=&limit=`); returns `{results, next}`.

### `PATCH /notes/{id}` · `DELETE /notes/{id}`
### `GET /threads/{id}/outline`
Returns markdown (trail headings + notes) for the "copy as outline" action.

The client is **session-scoped**: on boot it restores the last thread from
`GET /threads/{id}` (id kept in `localStorage`) and re-renders it **without
generating**, so a refresh never re-charges. Saving/removing a note calls these
endpoints; `?demo=1`/offline keeps notes in memory only.

---

## 6. Credits (read-side) & billing (later)

### `GET /credits/balance` → `{ "balance": 4820, "currency": "micro_credits" }`
### `GET /credits/ledger?limit=50` → paginated `CreditEntry`s with `reason`,
`delta`, `created_at`, and the linked `request_id` (so any charge can be traced
back to the question/action that caused it).

Reserved for the payments phase (interfaces only for now):
- `POST /billing/checkout` → provider session URL
- `POST /billing/webhook` → provider events → `CreditEntry(reason=purchase)`
- `GET /plans`, `POST /subscriptions`

Per-request analytics (cost by kind/lens, margin) are **not** a public endpoint
in the MVP — they are admin/DB queries over `RequestLog` + `UsageEvent`.

---

## 7. Conventions

- **Errors** are `{ "error": "snake_code", "message": "...", ...context }` with
  correct HTTP status: `400` validation, `401` auth, `402` credits,
  `404`, `409` idempotency conflict, `422` content blocked by screening,
  `429` rate limit, `5xx` upstream.
- **Pagination** is cursor-based (`?cursor=&limit=`) for ledger/notes.
- **IDs** are UUID strings.
- **`request_id`** is returned on generation and present in `meta`/`usage`, so
  the client (and support) can tie a charge or failure to one request.
- **Timestamps** are ISO-8601 UTC.
- **Lens** is always `{familiarity, depth, style, goal}`; omitted fields fall
  back to the thread's current lens, then `DEFAULT_LENS`.
- **Offline/demo:** when `/generate` is unreachable, the frontend falls back to
  the local mock adapter — no API contract change.

## 8. Open API questions

1. Should cached-hit `usage` still emit `latency_ms`/`tokens_*` as null or omit
   them? Proposal: null.
2. Do we expose `ContentVariant` text directly (for sharing) or only via nodes?
   MVP: nodes only.
3. SSE reconnection/resume for dropped streams? MVP: reconnect = re-fetch node
   snapshot; no token replay needed.
