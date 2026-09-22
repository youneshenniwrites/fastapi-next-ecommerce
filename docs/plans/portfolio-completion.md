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

## Recruiter-readiness feedback decision — 22 September 2026

Keep this plan as the single source of truth. After PR #187, prioritize VIN-120's
checkout submission, confirmation and history, then VIN-30 hosted sandbox Checkout.
Tests, coverage gates, `/api/v1/` contracts and backend admin authorization already
exist; do not recreate them or make an admin UI/coverage badge a checkout prerequisite.
VIN-121 still requires privacy tests before telemetry activation. Payment work must
preserve inventory already claimed at placement and release it exactly once for
expired/cancelled unpaid orders. Finish security headers and hosted evidence before
claiming demo completion. A concise scaling discussion belongs to the interview
package: distinguish measured limits from hypotheses; do not add Redis, replicas or
new services solely for demonstration. No additional plan or infrastructure is approved.

## Progress at a glance — 22 September 2026

**Active stage: 4 of 6, checkout; VIN-119 merged in PR #181; PR #187 merged; VIN-120 checkout journey active.** The existing catalog,
accounts and cart are the starting product; checkout and sandbox payments are
not yet complete. Stage counts are not an estimate of effort or time remaining.

| Stage | Status | What remains |
| --- | --- | --- |
| 1. Accurate baseline | ✅ Complete | Baseline evidence linked from #155 |
| 2. Reliable cart and rate limits | ⏸ Hosted proof pending | Finish VIN-158 hosted proof; VIN-89 hosted acceptance remains |
| 3. Security and monitoring | ⛔ Partly blocked | #121 privacy + configuration gates; #126 remains actionable |
| 4. Checkout | 🔵 Active | VIN-118 foundation delivered by PR #177; VIN-119 placement merged in PR #181; VIN-120 journey implemented locally; verification/review in progress |
| 5. Sandbox payments | ☐ Outstanding | #30 |
| 6. Hosted demo and evidence | ⛔ Partly blocked | #45 preview design gate; other evidence work remains actionable |

**Maintenance complete (21 September):** VIN-172 is closed and Done. All initial
Dependabot PRs #165–#171 are merged; PR #168 proved a live policy approval and
protected automatic merge. PR #175 merged the readable delivery conventions.

**Core reliability code merged:** PR #164 merged as `4d3bbd9` after passing required
CI and completed Codex/CodeRabbit review of `308824b`. Anonymous signed identity,
test-threshold separation and the form-focus correction are merged. This does not
prove hosted configuration, deployment synchronization or real visitor isolation.

**Merged progress:** `███████░░░░░░░░░░░░░` **10 / 29 outcomes (34%)**.
PR #177 is merged and VIN-118 is Done: the reviewed architecture decision and
tested order-draft foundation are delivered.
This counts acceptance outcomes, not effort or a delivery-date forecast.
Stage 1 is complete, stage 2 has 4/7 verified outcomes, and stage 4 has 3/5.
Atomic placement merged in PR #181 (`0f0b214`); hosted
verification remains pending. Checkout UI and sandbox payments remain unbuilt. VIN-155's
native bar counts whole workstreams: VIN-29 stays open until VIN-119 and VIN-120
are also accepted, so delivering VIN-118 alone does not advance that bar.

**Owner-approved sequence change (21 September):** VIN-118 order drafts are delivered. Continue feature delivery with
VIN-119 atomic placement, then VIN-120 checkout/history.
VIN-158 and VIN-89 remain open for hosted proof; VIN-147 CI optimization stays
Backlog. Security/monitoring and hosted acceptance remain finish-line requirements,
but do not block independent checkout development. One implementation story is active.

Development deployment and public smoke checks succeeded for `91daad7` in
[run 35642648695](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/35642648695).
The earlier revision was superseded before frontend CI completed; the deployment
gate required a fully tested current main. Signed visitor isolation is still
unverified; the Vercel connector currently lacks access to the project team.

**Current implementation:** VIN-119 atomic
placement, stock protection and customer-scoped idempotency. VIN-118 evidence:
166 PostgreSQL tests pass, including draft ownership, exact totals, rollback and
migration round trips; container smoke/schema checks and frontend types pass.
VIN-119 evidence: the full PostgreSQL suite passed 175 tests, and the final
placement suite passed 10 tests including concurrency, rollback and authorization.
Migration roundtrip and frontend type checks passed. PR #181 is merged and VIN-119
is Done; the browser checkout journey belongs to VIN-120.

**22 September handoff:** PR #187 merged (`b5ced34`) with account-fixture and
cart actionability regression corrections; 99 local browser tests passed with
2 existing device-specific skips, and required CI passed. VIN-89 retains broader
recovery/hosted acceptance in Backlog. VIN-120 checkout submission, confirmation
and history is now active. The Codex status-indicator follow-up remains deferred
under VIN-38; it does not displace feature delivery.

**Board convention:** issue cards only; PRs stay linked from their issue rather
than appearing as duplicate cards. This applies to dependency PRs as well.

**Issue priorities and targets:** High = core demo or active delivery; medium =
supporting delivery efficiency/evidence; low = post-demo. All issues carry one
priority label, a category, milestone and project link. Dependencies and blockers
still govern this plan's sequence. Milestones express outcomes, not promised dates.
Existing Customer accounts milestones are retained. Closed-ticket priorities are
retrospective classification; cancelled VIN-42 stays archived and not planned.
VIN-147 is medium, targeting CI strategy assessment after the queue and VIN-158.

**PR naming (owner-approved 21 September):** `[VIN-N] [type] Description`.
PR descriptions open with a linked Issue/title, Closes/Refs, and a separate
Problem line, without a duplicate Issue section. CONTRIBUTING.md owns types/examples; commits remain Conventional Commits and
Dependabot retains its documented upstream-title exception. The naming follow-up
to merged PR #174 persists this rule without creating a second portfolio plan.

**VIN-158 verification evidence (21 September 2026):** The sign-in focus failure
was reproduced twice in the full suite: React Hook Form's delayed second error
focus could interrupt field editing. PR #164 now focuses the first invalid field
once. The unchanged browser suite passes locally (99 passed, 2 skipped); frontend
unit checks/build/lint/types/format pass. Earlier backend evidence remains 141
passed, 2 PostgreSQL tests skipped locally. These are local results, not hosted proof.
PR #163 merged authenticated customer budgets as `b47be4a`; anonymous changes are
merged in PR #164 (`4d3bbd9`), deployed through `91daad7`; visitor-isolation
acceptance is still unverified. PR #162 merged review/naming policy as `aceea1d`.
VIN-158 awaits hosted verification; VIN-118 is Done following merged PR #177 and VIN-119 is Done following merged PR #181. PR #160's hosted acceptance remains separate.


### Blockers and unblock actions

Both tickets below remain required for the finish line. Blocked does not mean
abandoned or complete. Neither blocks unrelated checkout implementation.

| Ticket / board status | Verified dependency | Next unblock action | Who acts | Completion evidence |
| --- | --- | --- | --- | --- |
| [#121 Sentry](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/121) · **Blocked** | Privacy coverage is incomplete; free Sentry organization/project configuration and DSN availability are unverified. SDK scaffolding and docs have merged. | Agent extends error/transaction/log/nested-context scrubbing and tests serialized SDK payloads before activation. Owner creates or confirms the free organization/projects and configures the required environment values securely. Then agent verifies live telemetry. | **Agent:** privacy/configuration code and verification. **Owner:** account access and environment configuration. | Passing privacy tests, frontend/API trace, sanitized errors/logs/metrics, release/environment attribution, alert and quota evidence. DSNs alone do not finish it. |
| [#45 Safe PR previews](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/45) · **Blocked** | Reviewed-revision preview design, exact origins and credential/data isolation are not implemented. Existing development hosting and automatic main delivery are already delivered; no current external account blocker is established by the ticket. | Agent defines the preview trust boundary and implements a scoped workflow using isolated development data and server-only credentials. Identify any actual missing platform configuration before requesting owner action. | **Agent:** design, implementation, preview login/cart tests and retirement docs. **Owner:** only a demonstrated account/configuration dependency. | Reviewed preview revision/URL, exact allowed origin, isolated credentials/data, working login/cart, creation and retirement instructions. |

**Unblock order:** After the owner-approved checkout sequence, resume #121 privacy
work and outstanding hosted proof. Configuration can be
prepared independently, but telemetry activation waits for privacy checks. #45
remains in stage 6; its design work must not be mistaken for an owner-only wait.
Recheck each blocker at its story handoff and record evidence on the source issue.
If either remains unresolved at portfolio acceptance, report the demo as incomplete
for that outcome rather than ticking it off.

### Delivery checklist

Checked means the named outcome is verified. A merged code item is separate from
its hosted proof. Existing scaffolding does not complete an outstanding outcome.

#### 1 — Baseline

- [x] Save approved plan and align roadmap/Wiki — #157, merged `70f5efd`.
- [x] Reconcile disputed audit, skills/review and performance claims; mark unresolved evidence explicitly.
- [x] Verify baseline dev/prod deployment and smoke checks for `70f5efd`.

#### 2 — Reliability

- [x] Implement and merge readable 429/retry feedback — #156 / #159, `2cfc95f`.
- [ ] Verify the rate-limit implementation on the actual hosted revision — gated/unverified; do not equate a skipped deployment job with delivery.
- [x] Merge the cart read-timeout correction — #89 / #160, `b03d641`. Independent deadlines are limited to reads; general late-write ordering remains a documented limitation. Merge alone does not complete hosted acceptance.
- [ ] Verify merged recovery on hosted development using fictional data.
- [x] Merge authenticated customer write-budget isolation — VIN-158 / PR #163, `b47be4a`; tests and both reviews completed.
- [x] Merge anonymous identity and test-threshold separation — VIN-158 / PR #164, `4d3bbd9`. Required CI and both reviews passed on `308824b`; hosted acceptance remains separate.
- [ ] Configure the dedicated paired server-only signing key and verify actual Vercel identity/retry behavior — VIN-158. Configuration availability is unverified; missing keys preserve fallback limiting but do not prove visitor isolation.

#### 3 — Security and monitoring

- [ ] **#121 BLOCKED — agent action:** complete telemetry privacy coverage and pass serialized-payload tests before activation.
- [ ] **#121 BLOCKED — owner configuration, then agent proof:** confirm free Sentry projects/environment configuration; prove live errors, traces, releases/environments, logs/metrics and an alert. Missing configuration does not block checkout.
- [ ] Implement compatible security headers/CSP and verify deployed behavior — #126.

#### 4 — Checkout · CURRENT

- [x] Review architecture once and record transaction/state ADR — VIN-29, ADR 0002, delivered by merged PR #177.
- [x] Persist owned order drafts and immutable GBP price snapshots — VIN-118, delivered by merged PR #177.
- [x] Place orders atomically with stock protection, rollback and customer-scoped idempotency — VIN-119; merged in PR #181 (`0f0b214`).
- [ ] Deliver checkout, confirmation/detail and order history — #120.
- [ ] Prove PostgreSQL concurrency/ownership/totals and desktop/mobile non-payment journey — #118–#120.

#### 5 — Sandbox payment

- [ ] Confirm provider setup satisfies free/no-card constraint — #30.
- [ ] Deliver test-mode sessions, verified webhooks and payment lifecycle — #30.
- [ ] Prove deduplication, cancellation/expiry, races and exactly-once inventory release — #30.

#### 6 — Hosted portfolio finish

- [ ] **#45 BLOCKED — agent design/implementation:** deliver reviewed previews with isolated data, exact origins, safe credentials and verified login/cart; see unblock actions above.
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

The exact-head review instructions above have one exception: the owner-authorized
[pure-main-sync carry-forward procedure](../codex-review.md#review-carry-forward-for-a-pure-main-sync).
Apply every evidence and CI condition before omitting a repeat review; all other
changes require current-head review. This does not waive branch protection.

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
