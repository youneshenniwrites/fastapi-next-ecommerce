# Delivery roadmap

Purpose: [senior SWE portfolio plan](portfolio.md).
The [canonical portfolio completion plan](portfolio-completion.md) owns progress,
priorities and acceptance gates; [VIN-155](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/155)
owns completed-demo handoffs and evidence; new catalog work lives in [VIN-288](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/288). This roadmap indexes capabilities.

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
- Cart read-timeout correction (#89 / #160, `b03d641`) and mutation cancellation/offline recovery correction (PR #252, `a03545d`) are merged. VIN-89 hosted development persistence, deliberate reconnect, independent carts and returned-tab account switching are [verified](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/89#issuecomment-5957737474); arbitrary late-commit ordering remains a documented limitation.

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
PR #187 merged account-fixture/cart actionability test corrections. VIN-89’s subsequent
bounded recovery and hosted acceptance are verified through PR #252; see the
canonical plan for evidence and retained limitations.

## Current priorities

Use the [single portfolio completion plan and checklist](portfolio-completion.md)
for current work, dependencies, blockers and acceptance gates. This roadmap is an
index of delivered capabilities, not a second ordered plan. Issue #155 retains completed-demo evidence; VIN-288 and its children hold the
new customer-release handoffs. The board holds workflow state in separate
Customer features and Technical improvements views.

Azure (#31) and broader enterprise work remain deferred as specified in that plan.

The next planned customer release expands catalog discovery and content up to
100 workspace/home-office products: server queries, pagination, categories,
product information and a safe curated import. VIN-287 is delivered in
[PR #309](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/309)
(`e163ee7`). Follow the canonical plan for the dependency order.

Catalog administration (VIN-295) is a separate deferred roadmap. VIN-300 groups
later sign-in continuity, account recovery and purchase support.

Beyond the shopping journey, the [technical readiness epic](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/125)
sequences security hardening, reliability, and scale/compliance work, with scoped
tickets for SLOs (#129), restore drills (#130), the WCAG audit (#131),
monitoring/CI improvements and feature-flag discovery (#294). Password reset
(#127) and refunds (#128) now sit under the separate customer follow-up epic
VIN-300. Security headers (#126) are delivered.
VIN-126’s portfolio header outcome is now verified on development and production;
see the canonical plan for its enforced-release evidence. Other enterprise scope
remains deferred.

Each PR includes acceptance evidence, self-review findings, and passing CI before
merge under the user's authorization. Production/cloud deployment and paid external
services need their own authorization. Do not add caching/search infrastructure
until the working shopping journey has a measured need.

## Further engineering controls

Typed SQLAlchemy 2.0 models are delivered (#132) and the framework audit is
published with typed-model and revalidation changes merged (#132/#133). The
19 September correction distinguishes maintainability work from the invalid
refresh-import finding; #84’s remaining guidance slice is now verified in
AGENTS.md, scoped skills and framework documentation, with closeout on the ticket.
Scoped static checking for order/payment services and their payment interfaces is
implemented under VIN-261; [tooling scope](../tooling.md#scoped-backend-service-types-vin-261) records its limits. Repository-wide typing, code scanning and remaining
review/coverage required-check rules are further controls. Consult their source
issues and the live queue before starting work. Frontend lint/type/build and
browser checks are implemented.
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
Development and production are live; VIN-45’s [reviewed manual frontend previews](../design/frontend-previews.md#verified-closeout--2-october-2026) are verified, including exact retirement.
Account journey verification (#27) is complete; the persistent cart API (#71) and cart storefront (#72) are delivered (#80). Azure is deferred; no extra API billing is allowed.

### Telemetry refinement

VIN-121 delivered privacy-safe logs, checkout RED, payment-health signals and hosted alert/quota evidence; VIN-223 owns joined-trace proof; see the [canonical acceptance refinement](portfolio-completion.md#telemetry-acceptance-refinement-vin-121). Merged PR #219 delivers these signal additions; hosted foundation acceptance is complete under the revised scope; one joined trace is verified in VIN-223. Optional browser RUM is deferred to [VIN-204](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/204) and does not block VIN-121. No additional monitoring vendor or Collector is planned.
