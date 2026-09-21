# Delivery roadmap

Purpose: [senior SWE portfolio plan](portfolio.md).

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
purchase. See [ADR 0002](../decisions/0002-order-transactions.md); VIN-119 adds
atomic placement and VIN-120 adds the customer checkout/history UI.

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
#121 remains blocked: privacy handling and serialized-payload tests must pass
before activation, then configured projects and live telemetry evidence are
required. DSNs alone do not complete monitoring.
Operational runbooks and release/restore verification continue alongside hosted
development.

## Tracked delivery

The [board](https://github.com/users/youneshenniwrites/projects/1) owns live status.
Customer accounts are split into #24 secure sessions, #25 registration/login,
#26 profile/navigation and #27 journey verification/documentation. Cart implementation #28 is delivered. Checkout/orders #29 and sandbox payments
#30 remain outstanding; Azure #31 is deferred. Refine those
broader items into focused PR tickets before implementation. See
[session design](../design/customer-sessions.md) and [delivery rules](../delivery.md).

Hosting setup #44 and production workflow acceptance #46 are complete.
Development and production are live; #45 tracks the remaining frontend previews.
Account journey verification (#27) is complete; the persistent cart API (#71) and cart storefront (#72) are delivered (#80). Azure is deferred; no extra API billing is allowed.
