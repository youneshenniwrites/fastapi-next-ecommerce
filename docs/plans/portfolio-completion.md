# VINDOR: audit fixes to a complete portfolio demo

Approved by the owner on 19 September 2026. **This is the one canonical portfolio
completion plan**, including its progress checklist, priorities and acceptance
gates. Amend this file for tweaks; do not create replacement plans or copy its
checklist into issues, the Wiki or separate dashboards. Visuals are views of this
plan, not additional sources of truth.

[Tracking issue #155](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/155)
contains current handoffs, evidence and links to this plan and implementation
issues. The board owns workflow state. Record scope/sequence changes here and link
them from #155. Preserve historical evidence. Keep one implementation story active
at a time; external blockers must not prevent independent work.

## Progress at a glance — 20 September 2026

**We are in stage 2 of 6: customer-facing reliability.** The existing catalog,
accounts and cart are the starting product; checkout and sandbox payments are
still ahead. Stage counts are not an estimate of effort or time remaining.

| Stage | Status | What remains |
| --- | --- | --- |
| 1. Accurate baseline | ✅ Complete | Baseline evidence linked from #155 |
| 2. Reliable cart and rate limits | 🔵 Active | Verify #160 delivery, then #158 |
| 3. Security and monitoring | ☐ Outstanding | #121 privacy/live proof; #126 headers/CSP |
| 4. Checkout | ☐ Outstanding | #118 → #119 → #120 |
| 5. Sandbox payments | ☐ Outstanding | #30 |
| 6. Hosted demo and evidence | ☐ Outstanding | Previews, verification controls, restore, accessibility, demo |

**Next action:** verify actual deployment and acceptance after the owner merged
#160 as `b03d641` on 20 September. The merge is confirmed; hosted proof is pending.
After that, implement #158. Only one implementation story is active.

### Delivery checklist

Checked means the named outcome is verified. A merged code item is separate from
its hosted proof. Existing scaffolding does not complete an outstanding outcome.

#### 1 — Baseline

- [x] Save approved plan and align roadmap/Wiki — #157, merged `70f5efd`.
- [x] Reconcile disputed audit, skills/review and performance claims; mark unresolved evidence explicitly.
- [x] Verify baseline dev/prod deployment and smoke checks for `70f5efd`.

#### 2 — Reliability · CURRENT

- [x] Implement and merge readable 429/retry feedback — #156 / #159, `2cfc95f`.
- [ ] Verify the rate-limit implementation on the actual hosted revision — gated/unverified; do not equate a skipped deployment job with delivery.
- [x] Merge the cart read-timeout correction — #89 / #160, `b03d641`. Independent deadlines are limited to reads; general late-write ordering remains a documented limitation. Merge alone does not complete hosted acceptance.
- [ ] Verify merged recovery on hosted development using fictional data.
- [ ] Correct limiter identity/trust — #158 **next**. Investigation and test matrix prepared; no implementation yet.

#### 3 — Security and monitoring

- [ ] Pass telemetry privacy tests before activation — #121.
- [ ] Prove live errors, traces, releases/environments, logs/metrics and an alert — #121; configuration-dependent, must not block independent checkout work.
- [ ] Implement compatible security headers/CSP and verify deployed behavior — #126.

#### 4 — Checkout

- [ ] Review architecture once and record transaction/state ADR — #29.
- [ ] Persist owned order drafts and immutable GBP price snapshots — #118.
- [ ] Place orders atomically with stock protection, rollback and customer-scoped idempotency — #119.
- [ ] Deliver checkout, confirmation/detail and order history — #120.
- [ ] Prove PostgreSQL concurrency/ownership/totals and desktop/mobile non-payment journey — #118–#120.

#### 5 — Sandbox payment

- [ ] Confirm provider setup satisfies free/no-card constraint — #30.
- [ ] Deliver test-mode sessions, verified webhooks and payment lifecycle — #30.
- [ ] Prove deduplication, cancellation/expiry, races and exactly-once inventory release — #30.

#### 6 — Hosted portfolio finish

- [ ] Verify safe reviewed previews with isolated data and exact origins — #45.
- [ ] Expand cart coverage measurement and validate comparison gates before requiring them.
- [ ] Resolve exact-head review enforcement — #38; add types around new backend services.
- [ ] Prove browser-cache speed benefit or record unproven by **1 October** — #146; implementation is already merged, measurement is not proven.
- [ ] Run complete hosted sandbox purchase with fictional data.
- [ ] Perform disposable restore rehearsal and document recovery — scoped #130.
- [ ] Review full journey for keyboard/mobile/accessibility — scoped #131, not formal full conformance.
- [ ] Update architecture/setup/limits and deliver five-minute demo script.

**Finish line:** reproducible hosted sandbox purchase, correct money/inventory,
useful monitoring, restore evidence and an understandable demonstration.

Update this checklist in place when milestones land, linking evidence through
[issue #155](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/155).
The sections below define the detailed scope and acceptance for these same items.


## Goal

Deliver a polished fictional GBP shop with account → cart → checkout → sandbox
payment → confirmation/history, verified deployment/monitoring, and interview
evidence. Preserve Next.js, FastAPI, PostgreSQL and free Vercel/Neon hosting.
No real customer/payment data, paid services or card-required setup.

The first code change is [storefront rate-limit handling #156](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/156).
Brief planning/status reconciliation precedes it; wider documentation cleanup
does not block it. Follow [delivery policy](../delivery.md) throughout.

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
