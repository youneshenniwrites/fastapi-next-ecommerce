# VINDOR: audit fixes to a complete portfolio demo

Approved by the owner on 19 September 2026. [Tracking issue #155](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/155)
owns current status, linked stories, acceptance evidence and handoffs. This plan
owns priorities and acceptance gates; the board owns workflow state. Update this
plan and #155 before changing scope or sequence. Reuse existing tickets and
preserve historical evidence. Keep one implementation story active at a time;
external blockers must not prevent independent work.

## Goal

Deliver a polished fictional GBP shop with account → cart → checkout → sandbox
payment → confirmation/history, verified deployment/monitoring, and interview
evidence. Preserve Next.js, FastAPI, PostgreSQL and free Vercel/Neon hosting.
No real customer/payment data, paid services or card-required setup.

The first code change is [storefront rate-limit handling #156](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/156).
Brief planning/status reconciliation precedes it; wider documentation cleanup
does not block it. Follow [delivery policy](../delivery.md) throughout.
The owner's 20 September [bounded review and merge authorization](../delivery.md#bounded-review-cycles-and-standing-authorization) permits linked non-blocking deferrals
and prompt merges after required checks and completed reviews; it does not waive
blocking defects or authorize bypasses.

## 1. Establish an accurate baseline

Recheck current main, open PRs, deployment records and actual review evidence.
Reconcile #153/#136, separating merged implementation from verified acceptance.
Replace obsolete review-outage instructions without claiming running reviews are
clean. Correct the previous audit's refresh and AWS/Azure claims and align the
cart design with implemented revalidation. Record development synchronization
against a verified revision; distinguish access protection from PR previews.
Reconcile #146's performance proving vehicle and #154's deferred policy question.
Align the roadmap and Wiki with this plan.

Acceptance: every disputed handover/audit claim has a corrected statement or an
explicit unresolved status, evidence and next action.

## 2. Customer-facing reliability and abuse handling

### 2A. Preserve rate limits (#156)

Login/registration handlers preserve upstream HTTP 429 and validated Retry-After
information, with a safe generic wait message for missing/malformed guidance.
Cart actions return a typed rate-limit failure with optional timing, distinct
from uncertain writes. Account/cart feedback is accessible and supports deliberate
retry only: never automatically repeat a mutation. Preserve validation,
unauthorized, stock-conflict and actual outage behavior.

Acceptance: boundary tests prove 429 does not become 503 or uncertain registration;
cart tests distinguish known rejection from uncertain writes; desktop/mobile
browser tests prove readable feedback and successful deliberate retry.

### 2B. Cart recovery (#89)

Reproduce post-write timeouts using disposable fault fixtures. Capture mutation
completion, server snapshot publication and recovery UI sequencing. Fix the
proven cause without increasing timeouts or weakening assertions merely to pass.
Where necessary consolidate recovery transitions into explicit testable state
logic while preserving privacy and account isolation.

Acceptance: committed-but-unacknowledged writes reconcile; controls remain
read-only until a fresh authoritative read; account changes never expose or mutate
the previous cart. Keep documented last-writer-wins absolute quantities;
atomic multi-device increments are outside this release.

### 2C. Limiter trust

Trace browser → Next.js → FastAPI identity in development. Establish the trusted
platform identity and anonymous/authenticated boundaries. Test shared egress,
forged forwarded headers, process resets and legitimate retries. Separate test
traffic configuration from production thresholds. Implement the bounded correction
supported by evidence and explicitly retain best-effort limitations where
protection is not distributed.

Acceptance: limits match the actual topology, distinct customers are not
unintentionally grouped, and protection claims match demonstrated behavior.

## 3. Essential security and observability

### Sentry (#121)

Cover enabled errors, transactions, logs and nested context with privacy controls.
Include OAuth username emails, authorization/cookies, credential headers, URLs,
breadcrumbs, extras and exception context. Test serialized SDK envelopes with an
in-memory transport and fictional secrets. Report meaningful handled failures
with sanitized context, excluding ordinary validation/authentication failures.
Make source-map upload conditional on credentials and preserve secrets-free builds.
Keep activation blocked until privacy tests pass. Then prove frontend/API trace
continuity, errors, release/environment tags, logs/metrics and an alert.

Acceptance: privacy tests precede activation; every live criterion has evidence or
an explicit blocker. Missing credentials do not block checkout implementation.

### Security headers (#126)

Introduce compatible headers and a tested CSP rollout. Verify sessions, Server
Actions, images and Sentry. Inspect deployed responses rather than assuming
repository settings equal hosted behavior.

## 4. Correct checkout (#29: #118 → #119 → #120)

Run architecture-review once for the epic and record transaction/state decisions
in a new ADR. FastAPI owns money, permissions, stock and order state.

- **#118 foundation:** persist orders/lines with immutable product/price snapshots,
  GBP quantities/totals, reviewed migrations and regenerated contracts. Enforce
  ownership. Intermediate records are drafts, never unprotected placements.
- **#119 placement:** one domain service owns a transaction; participating CRUD
  helpers do not commit. Revalidate prices/stock, persist the order, decrement
  inventory and apply documented cart disposition atomically. Use deterministic
  locking or guarded updates. Customer-scoped idempotency returns the original
  equivalent result, rejects incompatible reuse and rolls back all failures.
- **#120 journey:** checkout submission, confirmation/detail and customer history
  use authoritative totals and explicit states. Handle stock conflicts, expiry,
  response loss and retries without duplicates; preserve mobile/keyboard access
  and accessible loading/error/empty states.

Acceptance: PostgreSQL tests cover last-item contention, concurrent same-key
requests, ownership, totals, rollback and response-loss recovery. Desktop/mobile
browser tests prove the complete non-payment journey.

## 5. Sandbox payments (#30)

Default to hosted Stripe Checkout test mode, subject to the no-card/no-paid-service
constraint. If setup cannot meet it, record the blocker before integration work.
Keep the provider behind a backend adapter. Implement pending-payment → paid /
failed / cancelled / expired states; sessions derive from persisted totals.
Verified webhooks, never redirects, establish paid state. Deduplicate events,
enforce valid transitions and prevent duplicate orders/payment sessions.
Define and test inventory release exactly once for expired/cancelled unpaid
orders. Paid orders remain immutable; refunds are later work.

Acceptance: sandbox success/cancel/expiry, duplicate/out-of-order events, invalid
signatures and webhook/redirect races work without real data or charges.

## 6. Hosted delivery and portfolio evidence

- **Previews #45:** reviewed revisions, isolated development data, exact origins,
  server-only credentials, no production secrets in PR code; verify session/cart
  behavior and document preview creation/retirement.
- **Controls:** measure cart state/action coverage and keep UI browser evidence.
  Require comparison checks only after relevant/docs-only behavior is validated.
  Resolve #38 exact-head review enforcement separately from CI. Add backend types
  incrementally around order/payment services. Measure #146 on a suitable run or
  record the claim as unproven at its existing deadline.
- **Evidence:** complete the hosted development journey with fictional data.
  Document deployment recovery and prove one disposable restore rehearsal before
  claiming recoverability. Perform focused keyboard/mobile/accessibility review;
  update architecture, decisions, setup, known limits and a five-minute demo.

Acceptance: a reviewer can reproduce the project, complete a sandbox purchase,
inspect correctness evidence and understand limitations.

## Working rules

Each story confirms scope/dependencies/acceptance/authorization; moves In progress
before implementation; includes focused tests and contract/docs updates; runs
relevant checks and required CI; discloses self-review; obtains current-head
external review. Follow existing push/merge/deployment authorization, never infer
standing authorization from this plan. Verify acceptance and update issue/board/
handoff, distinguishing implemented, merged, deployed and operationally verified.
Report completed work, evidence, blockers and next action briefly.

Every outcome awaiting live proof retains its exact proving vehicle and expiry
on its source/proving tickets under the acceptance-ledger rule. Do not mark a
parent Done because its implementation scaffolding merged.

## Boundaries

GBP, fictional products/users, sandbox payments. No real fulfilment, shipping
integrations, promotions or tax engine. Do not rewrite working architecture or
revert revalidation solely because the earlier audit was inaccurate. Defer Azure,
microservices, Redis/search, refunds, broad SLOs and formal full WCAG conformance.
Password recovery/email verification remain follow-ups unless demo acceptance
requires them. Pagination becomes required beyond 100 storefront products.
Deployment-script consolidation, placeholder cleanup and image-patch retirement
are maintenance, not checkout prerequisites. External configuration blockers stay
visible while the next independent story proceeds.

Finish line: a reproducible sandbox shopping demo with verified money/inventory,
useful monitoring, documented recovery and honest evidence—not completion of
every enterprise-readiness ticket.
