# Feedback — status

Triage of the live-session review. `[done]` items shipped on
`feat/http-api-and-app-wiring` (PR #16); `[discuss]` items still need a
decision before implementation.

## Done in this pass

1. **[done — partial, #4/#13]** Don't truncate questions/dive selections unless
   4+ lines; allow longer notes. Section headers now wrap to four lines instead
   of a one-line ellipsis, and the selection threshold admits up to four lines
   (was a hard 120-character cap). A dedicated any-length **note entry** path is
   still open (see #13 below).
2. **[done — #6]** Home eyebrow is now curiosity-first
   ("Follow your curiosity · one phrase at a time"), dropping the
   "Branch anywhere" product-feature framing.
3. **[done — #9]** The bottom composer starts empty instead of being prefilled
   with the root question, so you no longer have to clear it to ask again.
4. **[done — #10]** Clicking a result/backlink (`↩`, trail crumb, results menu)
   now expands collapsed ancestors before scrolling, so definitions (and any
   nested result) reveal their collapsed question.
5. **[done — #2]** Definitions are now concise and independent of depth: the
   `define` prompt no longer scales with the reader's depth or the original
   answer's length. This bumps `PROMPT_VERSION` to `v2` (re-run
   `python manage.py seed_content` for the demo cache).

## Still to discuss

1. **Streaming markdown + formatting (#1).** Streams as one paragraph and
   renders markdown poorly. Needs a plan: prompt-level formatting (real
   paragraphs/lists for >2 min answers) plus a renderer in `renderBody` /
   `startBodyStream`. Discussed separately, not done.
2. **Definition length, full fix (#2).** Prompt is fixed; verify against a real
   long-answer session and consider a hard length cap / separate short model
   budget.
3. **Follow-up context (#3, #5).** What gets sent on a follow-up? Today only
   `parent.title` is sent (`generation/services.py`), so there is effectively no
   context layer; the lens is in the system prompt. Open: a proper context layer
   (parent body excerpt, ancestor path) with a token budget. The "System 1"
   router (decide local/none/all branches via a small on-device model like Laya)
   is explicitly **not** being pursued — to be scoped for feasibility only.
4. **TypeScript (#7).** Would add type safety but breaks the no-build,
   `file://`-safe ethos. Decide whether to keep plain JS or introduce a build.
5. **Credit-meter pre-decrement (#8).** The meter drops before the answer
   arrives because `meta` optimistically debits. Options: reconcile only on
   `usage`, or show a distinct "pending" state. Left out of this pass on purpose.
6. **Question-history rail (#11).** Left side listing historical questions;
   clicking loads the whole thread (root first, then progressively).
7. **Custom notes (#12, #13).** A richer note affordance (arbitrary length,
   free-form placement) beyond selecting text; notebook UX needs a design pass.
