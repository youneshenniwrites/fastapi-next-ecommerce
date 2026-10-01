# Delivery roadmap

**Earlier 1 October trace verification (VIN-223):** VIN-223 now has [joined hosted trace evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/223#issuecomment-5931310439): Next.js → FastAPI → database, with matching parent IDs and development environment tags. The backend release is recorded; that historical frontend sample lacks a release attribute, superseded by VIN-230 evidence below. No propagation code change or privacy relaxation was needed. VIN-121 remains Done under the owner-approved 30 September scope split. VIN-223 is outside the revised 29-outcome baseline and adds no checklist credit. The canonical plan now records **21/29 (72%)** after the VIN-146 deadline disposition and VIN-158 same-instance proof with verified diagnostics cleanup. See the [monitoring runbook](../observability.md#hosted-trace-continuity--verified-1-october-2026) for evidence and limitations.

Purpose: [senior SWE portfolio plan](portfolio.md).

**1 October monitoring and reliability closeout:** Frontend release tags and bounded readable trace labels merged in PR #231, deployed and have [connected hosted proof](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/230#issuecomment-5934081107). Privacy and sampling controls remain intact. VIN-232 safe HTTP method/status metadata merged in [PR #235](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/235) and has [joined hosted GET/HTTP 200 proof](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/232#issuecomment-5935362557) after normal gated development delivery; VIN-232 is Done. VIN-158 has [hosted throttling/retry evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378). VIN-237 password visibility merged in PR #239. VIN-158 same-instance visitor isolation and retry are now verified by the [bounded automated probe](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909932392) delivered in [merged PR #244](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/244), on deployed release `847092c`: A429 sequence 72 → runner B401 sequence 74 → A429 sequence 75, then A401 retry sequence 88, with one limiter witness and verified signed context. Resume VIN-89 hosted recovery proof next, then VIN-126 security headers and VIN-45 safe previews under the canonical plan. VIN-223, VIN-230 and VIN-232 add no checklist credit. The existing VIN-146 “prove or record unproven” deadline outcome is complete with [unproven-with-reasons evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/146#issuecomment-5934521461), previously giving 19/29 (66%); actual speed-improvement acceptance remains open/Backlog. VIN-158 now verifies its second existing reliability outcome, bringing progress to 21/29 (72%) with the denominator unchanged. Both development diagnostic flags are false; [gated cleanup redeployment](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909436876/attempts/2) succeeded, and direct API/storefront login probes returned 401 with no diagnostic headers at 19:00:05 UTC. [Closeout evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5938473213) links the proof and records cleanup. VIN-238 remains Backlog for future automation refinement; reuse PR #244’s bounded probe without separate checklist credit. Counters remain process-local; this proof does not establish a global distributed budget.

The owner-approved [portfolio completion plan](portfolio-completion.md) governs
current priorities and acceptance gates; [#155](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/155) owns live delivery evidence.

## Landed foundation

- Authentication repair, active-user/admin checks, bcrypt compatibility, and 22 regression tests (PR #1).
- Locked Python dependencies, Ruff checks, and root GitHub CI (PR #1).

## Additional foundation

- Reproducible local credentials and Docker/PostgreSQL setup.
- Initial migrations and upgrade/downgrade/metadata checks.
- Agent instructions and three focused repository skills (PR #2).
- Frontend directory skeleton with a scoped skill, and shared Azure planning guidance.

- Catalog correctness: precise GBP prices, bounded validation, and PostgreSQL tests (PR #4).
- Auditing, coverage gate, pinned CI actions, hooks, and dependency updates (PR #5).
- Expanded contributor/developer/security documentation and maintenance guidance.

## Delivered application and hosting

- Explicit admin bootstrap and empty-catalog demo seeding; see [demo guide](../demo.md).
- Next.js catalog/detail storefront, generated API contract, state handling and desktop/mobile browser checks.
- Private profile page, session-aware desktop/mobile navigation and sign-out (#26).
- Complete account UI journey verification and onboarding evidence (#27).
- Registration/login screens with same-origin registration and fixed safe navigation (#25).
- Server-mediated login/profile/logout with HttpOnly cookies and exact origin checks (#24 / #41).
- Isolated Vercel/Neon development and production configuration (#44 / #47).
- Both environments publicly deployed and smoke tested from reviewed main 4606e67; idle PostgreSQL connection recovery is merged (#48).
- Production delivery workflow in #49: exact-main CI checks, migration, API then frontend deployment and smoke verification. GitHub-triggered release acceptance is verified (#46).
- Persistent cart API and signed-in cart storefront: quantities, stock rules and concurrency covered by API and browser tests (#28 / #72 / #80).
- Development auto-delivery from verified main revisions, mirroring the production gate (#108, hostname fix #113).
- Public-demo abuse throttling: fixed-window 429s on auth/write endpoints with documented limits and headers (#109, eviction follow-up #115).

- Storefront rate-limit feedback is merged (#156 / #159, `2cfc95f`).
- Cart read-timeout correction is merged (#89 / #160, `b03d641`); merge does not establish hosted acceptance. See #89 for remaining verification.

## Frontend design-system work

Tailwind v4 and shadcn Button, Badge and Skeleton establish the VINDOR component
foundation (#53). Catalog/navigation layouts now compose shared components and Lucide icons (#54);
account, cart and checkout components are added with their feature tickets.

## Order foundation

VIN-118 implements authenticated draft creation/list/detail, immutable GBP
snapshots and server-owned totals. Drafts never reserve inventory or place a
purchase. See [ADR 0002](../decisions/0002-order-transactions.md); VIN-119 implements
atomic placement with stock/price/cart revalidation and customer-scoped retries;
PR #181 is merged. VIN-120 customer checkout/history merged in PR #188. VIN-30 sandbox implementation merged in PR #194; development activation and hosted purchase/cancellation/expiry proof were verified on 23 September (see the canonical plan).
PR #187 merged account-fixture/cart actionability test corrections; broader VIN-89
recovery and hosted acceptance remain outstanding.

## Current priorities

Use the [single portfolio completion plan and checklist](portfolio-completion.md)
for current work, dependencies, blockers and acceptance gates. This roadmap is an
index of delivered capabilities, not a second ordered plan. Issue #155 holds
handoffs and evidence; the board holds workflow state.

Azure (#31) and broader enterprise work remain deferred as specified in that plan.

Beyond the shopping journey, the [enterprise readiness epic](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/125)
sequences security hardening, reliability, and scale/compliance work, with scoped
tickets for security headers (#126), password reset (#127), refunds (#128), SLOs
(#129), restore drills (#130), and the WCAG audit (#131).

Each PR includes acceptance evidence, self-review findings, and passing CI before
merge under the user's authorization. Production/cloud deployment and paid external
services need their own authorization. Do not add caching/search infrastructure
until the working shopping journey has a measured need.

## Further engineering controls

Typed SQLAlchemy 2.0 models are delivered (#132) and the framework audit is
published with typed-model and revalidation changes merged (#132/#133). The
19 September correction distinguishes maintainability work from the invalid
refresh-import finding; the remaining #84
guidance slice (AGENTS.md/skills/docs boundaries) is tracked on the ticket.
Still open in separate PRs: static type checking, then code scanning and
remaining review/coverage required-check rules. Frontend lint/type/build and browser checks are now implemented.
Sentry SDK scaffolding is merged in the API and storefront (#122/#123).
#121’s revised-scope monitoring foundation is complete: PR #203 implements
error/transaction/log/metric privacy filtering and serialized-payload tests.
Merged PR #219 delivers browser-session protection and commerce signals.
VIN-223 records one joined hosted trace; release-coverage and sampling limitations
remain explicit in the observability runbook. Do not repeat completed configuration
or verification. DSNs alone do not complete monitoring.
Operational runbooks and release/restore verification continue alongside hosted
development.

## Tracked delivery

The [board](https://github.com/users/youneshenniwrites/projects/1) owns live status.
Customer accounts are split into #24 secure sessions, #25 registration/login,
#26 profile/navigation and #27 journey verification/documentation. Cart implementation #28 is delivered. Checkout/orders VIN-29 is complete: PR #188 delivered the final checkout/history slice.
Sandbox payments VIN-30 is complete on development; production payments remain disabled and Azure #31 is deferred. See
[session design](../design/customer-sessions.md) and [delivery rules](../delivery.md).

Hosting setup #44 and production workflow acceptance #46 are complete.
Development and production are live; #45 tracks the remaining frontend previews.
Account journey verification (#27) is complete; the persistent cart API (#71) and cart storefront (#72) are delivered (#80). Azure is deferred; no extra API billing is allowed.

### Telemetry refinement

VIN-121 owns privacy-safe logs, checkout RED and payment-health signals plus hosted trace/alert/quota evidence; see the [canonical acceptance refinement](portfolio-completion.md#telemetry-acceptance-refinement-vin-121). Merged PR #219 delivers these signal additions; hosted foundation acceptance is complete under the revised scope; one joined trace is verified in VIN-223. Optional browser RUM is deferred to [VIN-204](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/204) and does not block VIN-121. No additional monitoring vendor or Collector is planned.
