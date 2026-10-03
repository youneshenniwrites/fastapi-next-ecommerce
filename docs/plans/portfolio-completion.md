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

Keep this plan as the single source of truth. VIN-120 checkout submission,
confirmation and history are delivered in PR #188. VIN-30 implementation merged in PR #194 and its hosted sandbox journey was verified on 23 September. PR #203 implements VIN-121 error/transaction/log/metric privacy controls and serialized tests. PR #219 implements the browser-session privacy gate and commerce signals. PR #219 merged on 30 September as `79d7923`, after clean current-head Codex review and passing application CI. Development monitoring is now verified; joined trace proof is recorded in #223.
Tests, coverage gates, `/api/v1/` contracts and backend admin authorization already
exist; do not recreate them or make an admin UI/coverage badge a checkout prerequisite.
VIN-121 development activation and monitoring foundation are verified. Joined trace proof is verified in #223. Payment work must
preserve inventory already claimed at placement and release it exactly once for
expired/cancelled unpaid orders. Finish security headers and hosted evidence before
claiming demo completion. A concise scaling discussion belongs to the interview
package: distinguish measured limits from hypotheses; do not add Redis, replicas or
new services solely for demonstration. No additional plan or infrastructure is approved.

## Progress at a glance — 3 October 2026

**Current stage: 6 of 6, hosted verification and portfolio evidence.** Checkout and sandbox purchase are verified on development; remaining hosted acceptance stays explicit below. Stage counts are not effort estimates.

| Stage | Status | What remains |
| --- | --- | --- |
| 1. Accurate baseline | ✅ Complete | Baseline evidence linked from #155 |
| 2. Reliable cart and rate limits | ✅ Complete | VIN-158 same-instance visitor isolation and VIN-89 hosted recovery are verified |
| 3. Security and monitoring | ✅ Complete | #121 monitoring foundation and #126 hosted header enforcement are verified |
| 4. Checkout | ✅ Complete | Non-payment journey delivered by PR #188; hosted purchase verified in stage 6 |
| 5. Sandbox payment implementation | ✅ Complete | PR #194 merged; development activation and hosted proof verified in stage 6 |
| 6. Hosted demo and evidence | Incomplete | Three outcomes remain; scoped tickets and sequence below |

**Payment implementation merged (23 September):** PR #194 merged as `0e89efd` after clean Codex review, CodeRabbit approval and passing CI on `9adfff8`. Sandbox sessions, signed webhooks and inventory recovery are delivered. VIN-30 is complete: development revision `8685cc1` passed the real sandbox purchase, history, cancellation, expiry and duplicate-expiry replay on 23 September, 19:20–19:30 UTC, with paid-stock verification at 19:42–19:44 UTC. See [hosted evidence](../sandbox-payments.md#hosted-development-evidence--23-september-2026). Production sandbox payments remain disabled; no live payments are enabled.

**Initial maintenance delivered (21 September):** All initial
Dependabot PRs #165–#171 are merged; PR #168 proved a live policy approval and
protected automatic merge. PR #175 merged the readable delivery conventions.
VIN-172 reopened on 28 September for dependency continuation (PR #214).
PR #217 switched Dependabot review to CodeRabbit; PR #218 added bounded rate-limit
retries. Both are merged. Live unattended review → approval → protected merge proof
remains pending on a genuine eligible update; manual merges do not satisfy it.
VIN-38 and VIN-172 are deferred while portfolio delivery resumes. Their unfinished
acceptance does not mean active implementation and adds no portfolio completion credit.

**Current execution priority — 3 October:** VIN-158 hosted isolation, retry and
cleanup and VIN-248’s baseline MIME/referrer header slice are verified. VIN-146
frontend CI speed is verified and Done through PR #251. VIN-89 cart recovery is
merged in PR #252 and verified on hosted development; its evidence is linked below.
VIN-126 is verified through the staged policy, guarded nonce correction and
enforcement in PRs #254–#256. Its hosted release and evidence are recorded below.
VIN-45's reviewed manual preview is verified: PRs #264–#266 delivered trusted
orchestration and guidance; the completing preview passed fictional login/cart,
account/host isolation, exact source identity, enforced headers and actual wrong-origin
HTTP rejection. The temporary share link was revoked and the exact preview retired;
[complete evidence and limits](../design/frontend-previews.md#verified-closeout--2-october-2026)
are recorded. VIN-258's disposable restore is now merged in PR #268 and verified on
clean merged revision `0f547cb`: schema/data/sequence agreement, catalog/login/cart/order
ownership, corrupted-archive rejection and owned-resource cleanup all passed on
3 October at 20:59 UTC. The 0.083-second local restore and 1.481-second backup age
are observations on tiny fictional data, not hosted recovery guarantees;
[VIN-258](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/258)
holds complete evidence and review limits. VIN-260 is merged in PR #274, and its
coverage artifacts and preserved gates are verified as recorded below. Issue/board
closeout follows the reviewed documentation merge. VIN-259 is merged in PR #273;
actual deployment of `cd541ef` and twelve hosted guest checks are verified. Three
intermittent React #418 hydration errors still require disposition on
[VIN-259](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/259),
so its full accessibility outcome stays unchecked. Finish that acceptance next. The owner prioritized finishing this demo before
new customer features. VIN-270 email normalization is merged in PR #271.
VIN-147’s first bounded duplicate-trigger improvement merged in PR #272 as
`9d48342`; its broader
repeated-work strategy remains deferred. Prepared VIN-261 typing is paused in
Backlog while the existing closeout/review queue is completed, following the owner’s latest direction.
Keep one implementation story active; paused work stays Backlog. Monitoring
follow-ups VIN-223, VIN-230 and VIN-232 are complete; their [runbook evidence](../observability.md#hosted-trace-continuity--verified-1-october-2026)
adds no separate checklist credit. VIN-237 password visibility is delivered in
PR #239. Source issues and VIN-155 hold detailed daily handoffs.

**Core reliability code merged:** PR #164 merged as `4d3bbd9` after passing required
CI and completed Codex/CodeRabbit review of `308824b`. Anonymous signed identity,
test-threshold separation and the form-focus correction are merged. Merge alone did not
prove hosted configuration or visitor isolation. The earlier 1 October checkpoint records configuration and throttling/retry; the later PR #244 probe now establishes same-instance visitor isolation and retry.

**Verified progress:** `██████████████████░░` **26 / 29 outcomes (90%, revised scope)**.
This counts verified acceptance outcomes, not effort or time remaining.
Baseline is 3/3, reliability 7/7, checkout 5/5, payment implementation 3/3 and hosted finish 5/8. Security/monitoring is 3/3: privacy, hosted monitoring and deployed security headers are verified. The additional hosted-finish outcome records VIN-146’s cache-speed claim as unproven at its existing deadline; that historical item does not claim a speed improvement. VIN-146’s later implementation and delivery are verified separately without extra credit.
PR #188 merged as `765ee9b`: checkout, confirmation/detail and history are delivered.
Current-head CI passed 107 browser tests with 2 existing skips, plus 241 unit tests;
Codex completed a clean review and CodeRabbit approved. All review findings were resolved.
VIN-120 and its checkout parent VIN-29 are complete. Use one progress metric:
90% · 26/29 outcomes (revised scope). Hide Sub-issues progress in the saved board view;
retain the issue hierarchy for organization, not as a competing completion metric.
Payment implementation and hosted payment acceptance are complete; the remaining hosted-finish outcomes stay unchecked.

**Historical sequence change (21 September; current priority above supersedes this handoff):** VIN-118 order drafts are delivered. Continue feature delivery with
VIN-119 atomic placement and VIN-120 checkout/history, both now delivered. VIN-30 hosted payment verification is complete. The subsequent development monitoring foundation and joined-trace proof are now verified in VIN-121 and VIN-223; follow the current execution priority above.
At the earlier checkpoint, VIN-158 same-instance visitor isolation and VIN-89 hosted proof remained open; the later closeouts below supersede both gaps. VIN-147 CI optimization stays
Backlog. Security/monitoring and hosted acceptance remain finish-line requirements,
but do not block independent checkout development. Keep one implementation story active.

**Historical development deployment (superseded by the 1 October VIN-158 checkpoint below):**
Development deployment and public smoke checks succeeded for `91daad7` in
[run 35642648695](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/35642648695).
The earlier revision was superseded before frontend CI completed; the deployment
gate required a fully tested current main. At that checkpoint, signed visitor
isolation was unverified and the Vercel connector lacked project-team access.
The [1 October hosted evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378)
records the subsequently verified development configuration and throttling/retry outcomes. Same-instance visitor isolation was still unverified at that checkpoint and is now established by the later automated closeout below.

**Delivered implementation:** VIN-119 atomic
placement, stock protection and customer-scoped idempotency. VIN-118 evidence:
166 PostgreSQL tests pass, including draft ownership, exact totals, rollback and
migration round trips; container smoke/schema checks and frontend types pass.
VIN-119 evidence: the full PostgreSQL suite passed 175 tests, and the final
placement suite passed 10 tests including concurrency, rollback and authorization.
Migration roundtrip and frontend type checks passed. PR #181 is merged and VIN-119
is Done; the browser checkout journey belongs to VIN-120.

**22 September handoff:** PR #187 merged (`b5ced34`) with account-fixture and
cart actionability regression corrections; 99 local browser tests passed with
2 existing device-specific skips, and required CI passed. At that checkpoint VIN-89 retained broader
recovery/hosted acceptance in Backlog; the 2 October closeout below supersedes that state. VIN-120 checkout submission, confirmation
and history merged in PR #188; VIN-30 implementation merged in PR #194. Its hosted verification was completed on 23 September (see evidence above). VIN-38 now covers the owner-requested Dependabot reviewer-policy change above;
it does not add portfolio feature completion credit.

**Board convention:** issue cards only; PRs stay linked from their issue rather
than appearing as duplicate cards. This applies to dependency PRs as well.

**Issue priorities and targets:** High = core demo or active delivery; medium =
supporting delivery efficiency/evidence; low = post-demo. All issues carry one
priority label, a category, milestone and project link. Dependencies and blockers
still govern this plan's sequence. Milestones express outcomes, not promised dates.
Existing Customer accounts milestones are retained. Closed-ticket priorities are
retrospective classification; cancelled VIN-42 stays archived and not planned.
VIN-147 is medium; its start follows portfolio delivery unless it resolves a concrete blocker.

**PR naming (owner-approved 21 September):** `[VIN-N] [type] Description`.
PR descriptions open with a linked Issue/title, Closes/Refs, and a separate
Problem line, without a duplicate Issue section. CONTRIBUTING.md owns types/examples; commits remain Conventional Commits and
Dependabot retains its documented upstream-title exception. The naming follow-up
to merged PR #174 persists this rule without creating a second portfolio plan.

**Historical VIN-158 fixture evidence (21 September; superseded by the hosted checkpoints below):** The sign-in focus failure
was reproduced twice in the full suite: React Hook Form's delayed second error
focus could interrupt field editing. PR #164 now focuses the first invalid field
once. The unchanged browser suite passes locally (99 passed, 2 skipped); frontend
unit checks/build/lint/types/format pass. Earlier backend evidence remains 141
passed, 2 PostgreSQL tests skipped locally. These are local results, not hosted proof.
PR #163 merged authenticated customer budgets as `b47be4a`; anonymous changes are
merged in PR #164 (`4d3bbd9`), deployed through `91daad7`; visitor-isolation
acceptance was still unverified at that checkpoint. PR #162 merged review/naming policy as `aceea1d`.
At that checkpoint, VIN-158 awaited hosted verification; VIN-118 is Done following merged PR #177 and VIN-119 is Done following merged PR #181. PR #160's hosted acceptance remains separate.


**Earlier VIN-158 hosted checkpoint — 1 October 2026 (superseded for visitor isolation by the automated proof below):** Paired dedicated development secrets are active, verifier before signer. Final API deployment `27hgMwUV1uU1y1XBcDo4eShainHE` and storefront `4h5WD3mxTcRt6rchzYVXJdCZ5D5r` redeploy reviewed application source `f4e6307`; frontend release metadata matches. [Timestamped evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378) records request 61 returning 429 with a 43-second wait, the owner’s mobile-data incorrect-credentials report inside that window, and the original connection’s deliberate 401 retry after expiry. A separate direct API probe also returned 429 on request 61 and 401 after its retry deadline. Fresh focused fixtures passed (35 backend, 41 frontend). Earlier fresh-connection runs were inconclusive and included one 503; no global/same-instance budget claim is made. Counters remain process-local and shared NAT users share anonymous budgets. The mobile observation does not prove visitor isolation: a different FastAPI instance could explain its independent response. At that checkpoint, VIN-158 remained open pending proof against one limiter instance; VIN-238 was then proposed automation work, subsequently delivered by PR #244. PR #244 and the later probe below supersede that verification gap. Neither historical mobile testing nor VIN-238 tooling adds a separate checklist outcome.

**VIN-158 automated same-instance closeout — 1 October 2026:** [PR #244](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/244) merged as `847092c`; [normal gated development deployment](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909436876) succeeded for that release. The [bounded cross-network probe](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909932392) succeeded at 18:52–18:53 UTC using fictional invalid credentials and the unchanged 60-request limit. Visitor A received 429 at limiter sequence 72; the hosted runner's visitor B received 401 at sequence 74; A still received 429 at sequence 75. All three responses reported the same opaque limiter-instance witness, verified signed context and exact deployed release. A's deliberate retry received 401 at sequence 88 on that same instance after the retry deadline. Counter sequence order establishes the bracket without assuming synchronized clocks. This proves separate signed visitor budgets in one actual hosted limiter, not a global distributed budget; counters remain process-local and shared NAT visitors still share anonymous budgets. VIN-238 is closed as delivered through that bounded probe; reuse PR #244 instead of duplicating it, with no separate checklist credit.

**Diagnostics cleanup verified:** Both development diagnostic flags were saved false and [normal gated redeployment attempt 2](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909436876/attempts/2) succeeded. At 19:00:05 UTC, direct API and storefront login probes both returned deliberate 401 responses with no `X-Vindor-Limiter-*` headers; storefront HTML still advertised release `847092c`. The [VIN-158 evidence record](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5938473213) links same-instance proof and records cleanup. The existing identity outcome is verified, bringing progress to 21/29 (72%); no extra outcome is created for the probe tooling.

### Remaining delivery order — updated 3 October 2026

Refinement itself added no completed outcomes. Verified VIN-45, VIN-258 and VIN-260 acceptance
bring progress to 26/29 (90%), with three existing finish-line outcomes still open. Small stories link from VIN-155;
enterprise VIN-130/VIN-131 remain broader work under VIN-125. The issue hierarchy
is organization, not a replacement progress denominator.

| Order | Story | Bounded proving vehicle |
| --- | --- | --- |
| Done | VIN-258 disposable restore | Merged PR #268 and clean merged-revision rehearsal; local-only recovery limits and cleanup recorded |
| 2 | VIN-259 focused accessibility | Keyboard/mobile journey matrix and existing automated checks; fix in-scope blockers without claiming full WCAG conformance |
| Verified; documentation closeout | VIN-260 cart coverage | Merged PR #274; matching final-head/merged-main artifacts and preserved comparison guards, with expanded-scope baseline limits disclosed below |
| 4 | VIN-38 review enforcement, plus VIN-261 service types | Small adapter compatibility, policy-aware protection proof and scoped order/payment type checks; both required for one existing outcome |
| 5 | VIN-262 final interview package | Reconcile delivered VIN-198 script/setup/architecture/limits and record final fictional five-minute rehearsal after prerequisites |

All unstarted work stays Backlog; VIN-45, VIN-258 and VIN-260 acceptance are verified.
VIN-260 stays open until this documentation closeout lands. VIN-259 awaits
hydration-error disposition and final accessibility acceptance; VIN-261 is paused
pending queue clearance. VIN-38’s
trigger compatibility must be revalidated before its documented November policy
change; required-check settings need their reviewed design and explicit settings
authorization. This refinement itself added no protection, deployment or implementation
change; the later VIN-45 implementation is recorded above. VIN-147/VIN-172,
broader enterprise work and optional monitoring polish retain separate scopes and do not earn new baseline credit.

### Cart coverage acceptance — 3 October 2026

PR #274 merged the scoped cart-control measurements and comparison regressions.
The [final-head comparison artifact](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37153366241/artifacts/11285066989)
for `1f377d` and [merged-main LCOV artifact](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37154168383/artifacts/11285275946)
for `d67226d` agree: **436/437 lines, 521/532 branches and 90/90 functions**.
The recorded runs passed 421 unit tests and 137 browser tests. These figures cover
only the documented measured scope, not the whole frontend.

The expanded scope makes the old baseline incompatible, so the total comparison
is unavailable. The recorded changed measured-line result is also N/A; neither
is a green regression comparison. Absolute thresholds remain enforced, and the existing changed-line
and compatible-baseline guards remain intact with positive/negative regression
coverage. See [coverage scope and limits](../coverage.md).

The [post-merge Codex finding](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/274#discussion_r4174943042)
requests this canonical-plan correction. PR #276 records it; the source issue
retains the documentation review/merge status. VIN-260 is not marked Done until
that closeout lands. This verifies one existing outcome, with no extra credit for
supporting tests or documentation.

### Wider backlog disposition — refined 2 October 2026

The whole open backlog was checked against current code and issue/merge evidence.
Source tickets own their refined scope, first bounded deliverable, proving vehicle
and remaining decisions; this is a priority index, not another completion checklist.

- **Demo first:** the ordered stories above. VIN-178’s remaining branch-status
  activation coordinates with VIN-38; implemented validation is not enforced protection.
- **Supporting maintenance:** VIN-250 now also owns VIN-63’s stale-page HTTP 200
  cases; VIN-63 is consolidated, not delivered. VIN-172 live autonomous dependency
  proof, VIN-147 repeated-CI strategy and VIN-227 reviewer-routing races remain scoped
  supporting work. A demonstrated blocker may justify reprioritization.
- **Optional post-demo:** VIN-241 readable error alerts, VIN-242 reviewer visibility,
  VIN-204 browser RUM, VIN-243 provider widget assessment, VIN-186 component cleanup,
  VIN-184 discovery matching and VIN-154 skills-host policy are individually bounded.
- **Enterprise discovery:** VIN-125 retains broader account recovery (VIN-127),
  refund/void decisions (VIN-128), measured SLOs (VIN-129), full restore guarantees
  (VIN-130), full accessibility conformance (VIN-131) and optional Azure (VIN-31).
  Unresolved product/spend/provider decisions are recorded, not silently answered.
- **Stale backlog closed with proof:** VIN-84 framework guidance is present in
  current scoped instructions and the published reconciliation; VIN-225’s routine-doc
  workflow automatically requested PR #257’s actual current-head CodeRabbit approval
  without a Codex status; VIN-238’s cross-network probe was delivered under VIN-158.
  These housekeeping closures add no portfolio credit.

### Blockers and unblock actions

VIN-45's same-preview hosted proof and cleanup are verified. Development monitoring
(VIN-121) and joined-trace proof (VIN-223) are also complete. The next dependency is
VIN-259’s hydration-error disposition and final accessibility acceptance; keep actual access/configuration blockers
on the source issues. VIN-269 retains an explicitly approved, expiring development-only
audit exception through 10 October at 23:59 UTC; upstream remediation remains open. An unresolved outcome stays unchecked at portfolio acceptance.

### Delivery checklist

Checked means the named outcome is verified. A merged code item is separate from
its hosted proof. Existing scaffolding does not complete an outstanding outcome.

#### 1 — Baseline

- [x] Save approved plan and align roadmap/Wiki — #157, merged `70f5efd`.
- [x] Reconcile disputed audit, skills/review and performance claims; mark unresolved evidence explicitly.
- [x] Verify baseline dev/prod deployment and smoke checks for `70f5efd`.

#### 2 — Reliability

- [x] Implement and merge readable 429/retry feedback — #156 / #159, `2cfc95f`.
- [x] Verify the rate-limit implementation on the actual hosted revision — VIN-158, [1 October hosted evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378); reviewed application source `f4e6307`, active development deployments, HTTP 429 and deliberate retry.
- [x] Merge the cart read-timeout correction — #89 / #160, `b03d641`. Independent deadlines are limited to reads; general late-write ordering remains a documented limitation. Merge alone does not complete hosted acceptance.
- [x] Verify merged recovery on hosted development using fictional data — VIN-89 / PR #252, release `a03545d`; [hosted persistence, disconnected-write recovery, independent carts and returned-tab account switching](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/89#issuecomment-5957737474). Both tested carts were emptied and sessions signed out.
- [x] Merge authenticated customer write-budget isolation — VIN-158 / PR #163, `b47be4a`; tests and both reviews completed.
- [x] Merge anonymous identity and test-threshold separation — VIN-158 / PR #164, `4d3bbd9`. Required CI and both reviews passed on `308824b`; hosted acceptance remains separate.
- [x] Configure the dedicated paired server-only signing key and verify actual Vercel identity/retry behavior — VIN-158. Paired configuration and initial retry are [verified](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378); the [PR #244 automated probe](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909932392) proves A429 → B401 → A429 and A's later 401 retry with one limiter witness, ordered sequences and matching release `847092c`. Both development diagnostic flags were disabled, redeployed and verified absent from login responses; [closeout and cleanup evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5938473213) is recorded.

#### 3 — Security and monitoring · Complete

- [x] **#121 privacy gate:** PR #203 implements error/transaction/log/metric filtering with passing serialized-payload tests; PR #219 disables browser-session envelopes and tests actual default-integrations output. Merged as `79d7923` on 30 September after clean Codex review of `c454746` and passing application CI; hosted monitoring is recorded in the separate verified foundation outcome below.
- [x] **#121 development monitoring foundation:** hosted sanitized errors, logs/metrics, release/environment, email alert and quota controls verified. Owner-approved 30 September scope split transferred joined trace continuity to #223, outside this revised baseline; that trace is now verified separately.
- [x] Implement compatible security headers/CSP and verify deployed behavior — #126. PRs #254–#256 deliver the staged policy, guarded framework nonce transport and enforcement; exact release and hosted development/production evidence are recorded in the security-header closeout below.

#### 4 — Checkout · Complete

- [x] Review architecture once and record transaction/state ADR — VIN-29, ADR 0002, delivered by merged PR #177.
- [x] Persist owned order drafts and immutable GBP price snapshots — VIN-118, delivered by merged PR #177.
- [x] Place orders atomically with stock protection, rollback and customer-scoped idempotency — VIN-119; merged in PR #181 (`0f0b214`).
- [x] Deliver checkout, confirmation/detail and order history — VIN-120 / PR #188, `765ee9b`.
- [x] Prove PostgreSQL concurrency/ownership/totals and desktop/mobile non-payment journey — VIN-118–VIN-120; PR #181 PostgreSQL evidence and PR #188 CI run 35779631311.

#### 5 — Sandbox payment

- [x] Confirm provider setup satisfies free/no-card constraint — VIN-30; free Stripe sandbox account connected on 23 September, test mode verified through the Stripe connector. No live activation or real card was required.
- [x] Deliver test-mode sessions, verified webhooks and payment lifecycle — VIN-30 / PR #194, merged `0e89efd`; development activation and hosted evidence are recorded in stage 6.
- [x] Prove deduplication, cancellation/expiry, races and exactly-once inventory release — VIN-30 / PR #194; PostgreSQL CI run 35901974932 and desktop/mobile browser CI run 35901974785. These are automated fixture tests, not hosted Stripe proof.

#### 6 — Hosted portfolio finish

- [x] **VIN-45 — reviewed manual preview verified:** one reviewed deployment passed fictional login/cart/ownership, host isolation, exact source identity, enforced headers and application wrong-origin rejection; temporary access was revoked and exact retirement verified. See [complete hosted evidence](../design/frontend-previews.md#verified-closeout--2-october-2026).
- [x] Expand cart coverage measurement and validate comparison gates before requiring them — VIN-260 / PR #274, merged `d67226d`; final-head and merged-main coverage agree. See [scope limits and preserved gate evidence](#cart-coverage-acceptance--3-october-2026).
- [ ] Resolve exact-head review enforcement — VIN-38; add scoped order/payment service types — VIN-261. Both complete this one existing outcome.
- [x] Record browser-cache speed benefit as **unproven at the 1 October deadline** — #146; [expiry disposition and reasons](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/146#issuecomment-5934521461). Cache reuse is verified, but the 4m48s warm-cache observation versus the 5m25s cache-miss baseline changed test scope and included a retry. No controlled speedup was claimed at that deadline. VIN-146’s subsequent browser-runtime improvement is verified and Done through PR #251; its issue records the 2 October measurements and delivery evidence. This historical disposition earns no additional credit for that follow-up.
- [x] Run complete hosted sandbox purchase with fictional data — VIN-30, development `8685cc1`, 23 September; [success/history, cancellation, expiry and duplicate replay evidence](../sandbox-payments.md#hosted-development-evidence--23-september-2026).
- [x] Perform disposable restore rehearsal and document recovery — VIN-258 / PR #268, merged `0f547cb`; clean merged-revision verification and cleanup recorded on VIN-258. Local fictional PostgreSQL only; enterprise/hosted recovery remains #130.
- [ ] Review full journey for keyboard/mobile/accessibility — VIN-259, the scoped demo subset of #131, not formal full conformance.
- [ ] Update architecture/setup/limits and deliver the final five-minute demo package — VIN-262. The
  [walkthrough and script](../demo.md#five-minute-demonstration-script) are documented
  under VIN-198; final package reconciliation follows the still-unchecked
  prerequisite outcomes in this checklist. Security and monitoring stage 3 is
  already verified. This documentation alone adds no completion credit.

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

The original rollout began with [storefront rate-limit handling #156](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/156).
Brief planning/status reconciliation preceded it; wider documentation cleanup
did not block it. Follow [delivery policy](../delivery.md) throughout.
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

**Verified closeout — 2 October 2026:** PR #252 preserves mutation cancellation
through the installed Next.js fetch wrapper and keeps recovery available when the
browser reports an offline connection. Its current-head Codex review and required
CI passed. [Normal gated development delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37039903815)
deployed `a03545d`; release metadata matched before the [fictional-customer hosted check](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/89#issuecomment-5957737474).
Persistence, deliberate reconnect without write replay, independent desktop/mobile
carts and returned-tab account switching passed. Local committed-write/uncertain-write
fixtures retain the original assertions and deadlines; all 24 targeted repeats and
129 active full-suite cases passed without retries, with two existing skips.
This verifies the bounded recovery outcome, not arbitrary delayed-commit ordering
or a common root cause for every historical intermittent observation.

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

PR #203 supplies the error/transaction/log/metric privacy prerequisite below,
including serialized tests and conditional source-map configuration. PR #219
implements session-channel protection and bounded handled-failure/RED/payment
signals. The monitoring foundation is verified; joined trace proof is transferred
to #223 under the owner-approved scope revision.

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

### Telemetry acceptance refinement (VIN-121)

PR #203 is merged. PR #219 implements session-channel privacy protection and the bounded signals below under the [refined VIN-121 contract](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/121). PR #219 and #222 are merged; development monitoring foundation evidence is verified. One joined hosted trace is verified in #223; see the runbook for limitations.

- Safe structured logs cover checkout technical failures, webhook failures and inventory-release outcomes.
- RED covers cart writes, placement and payment-session creation: request count/rate, technical error ratio and p95 duration with sample counts. Expected declines/validation failures are separate; sampled trace counts are not total traffic.
- Payment evidence covers webhook processing failures and confirmation-to-local-paid delay, with explicit timestamp sources and duplicate handling.
- Trace evidence links storefront/API/dependencies; webhook processing is a separate asynchronous request, not assumed to share Stripe's trace context.
- New signals must survive the existing privacy allowlists with serialized-envelope positive/negative tests. Keep labels bounded and exclude personal data, raw URLs and order identifiers. Verify free account limits before activation; retain alert and quota acceptance.

[VIN-204](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/204) separately owns optional browser RUM (LCP/INP/CLS), after VIN-121. It does not block VIN-121 or add a portfolio completion outcome. No Collector, extra vendor, paid infrastructure or coding is authorized by this planning update. The single progress checklist remains unchanged.

### Security headers (#126)

Compatible framing, transport and nonce CSP enforcement is delivered through
PRs #254–#256, with sessions, Server Actions, images and Sentry verified. Actual
deployed responses and the controlled rejection probe are recorded below.

[VIN-248](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/248)
delivers the small baseline slice: `nosniff` and explicit referrer policy on the
API and storefront. Its issue retains CI/review and hosted verification evidence.
The full VIN-126 outcome is now checked after its CSP, framing, transport and
deployed acceptance; VIN-248 remains a baseline slice and adds no separate
portfolio outcome.

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

### Security-header closeout — 2 October 2026

PRs [#254](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/254),
[#255](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/255) and
[#256](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/256)
deliver staging, the guarded hosted nonce correction and enforcement. The owner
merged PR #256's reviewed head after green applicable CI; Codex's trusted unedited
clean result identifies `59a17db2ae`. Its new closing phrase was not recognized by
the informational adapter; the bounded format follow-up remains deferred in
[VIN-38](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/38#issuecomment-5960004944).
No success was fabricated or extra review requested.

Enforced release `cc115e093ad355882e7ce983bf35703f718a9609` passed main CI and
actual gated [development delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37056504486)
and [production delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37056504484).
Public hosted catalog/login (repeated)/registration/404 HTML passes framework-script
nonce equality and freshness, private/no-store caching, HSTS/MIME/referrer/framing,
full enforced CSP without report-only or production inline/eval script exceptions,
and caller-policy rejection. Assets remain immutable; product navigation, Swagger
health execution and ReDoc search work. Documentation nonces/caching and OAuth
redirect headers pass. The controlled isolated-browser response blocks an
unnonced script under the actual hosted policy; zero unexpected policy reports
were observed in normal public journeys. Existing development Sentry delivery
returned HTTP 200; production Sentry remains inactive.

The full production desktop Chrome/Pixel 7 fixture suite under standard-header
stripping passes 137 tests with two existing skips, including private account,
cart/checkout/recovery and framing cases; frontend 367 units, nonce patch 15
regressions and backend 319 tests (19 infrastructure skips), build/lint/types/format
pass. Public hosted observations do not claim private hosted commerce writes,
Safari coverage or continuous monitoring. The original failed nonce observation
and correction remain in the [policy runbook](../security-headers.md); bounded
style/documentation exceptions and rollback stay explicit. No new service,
collector, secret, account, paid upgrade or scheduled wakeup was added.

At that security-header checkpoint, the existing VIN-126 outcome brought progress to 23/29 (79%). VIN-248 remains
its baseline slice, and the correction/promotion add no extra outcomes. Next is
VIN-45's safe-preview design; its later verified closeout above supersedes this historical handoff.
