# Delivery roadmap

Purpose and priorities: [senior SWE portfolio plan](portfolio.md).

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

## Next PRs, in dependency order

1. Demo foundation implemented: explicit admin bootstrap and empty-catalog seeding.
   See [demo guide](../demo.md); the catalog storefront is also implemented.
2. Next.js catalog implemented: App Router, TypeScript, generated API contract,
   product list/detail, filtering, state handling and desktop/mobile browser checks.
3. Server-mediated session handlers implemented: login/profile/logout, HttpOnly
   cookies and origin checks. Account login/register/profile UI remains in #25–27.
   Keep authorization in FastAPI.
4. Persistent carts: ownership, quantity changes/removal, stock checks, API and UI.
5. Orders and checkout: price snapshots, authoritative totals, atomic inventory
   handling, idempotency, and concurrent last-item purchase tests.
6. Sandbox payments: select the provider, verify webhooks, handle duplicates,
   failures/cancellations, and connect confirmation/order history.
7. Free demo deployment (#44–46): Vercel/Neon, isolated dev/prod,
   with explicit free-tier limits, staging, secrets, TLS, migrations, logs,
   recovery limitations and rollback evidence. Azure migration remains future #31.

Each PR includes acceptance evidence, self-review findings, and passing CI before
merge under the user's authorization. Production/cloud deployment and paid external
services need their own authorization. Do not add caching/search infrastructure
until the working shopping journey has a measured need.

## Further engineering controls

Add typed SQLAlchemy models and static type checking, then code scanning and
repository required-check rules in separate PRs. Frontend lint/type/build and browser checks are now implemented. Add observability, operational
runbooks, and release/restore verification alongside hosted development. These are
planned controls, not features already enabled by the documentation.

## Tracked delivery

The [board](https://github.com/users/youneshenniwrites/projects/1) owns live status.
Customer accounts are split into #24 secure sessions, #25 registration/login,
#26 profile/navigation and #27 journey verification/documentation. Future work is
#28 carts, #29 checkout/orders, #30 sandbox payments and #31 future Azure migration. Refine those
broader items into focused PR tickets before implementation. See
[session proposal](../design/customer-sessions.md) and [delivery rules](../delivery.md).

Hosting setup #44 is prioritized before further account UI, followed by #45
previews and #46 production CD. Azure is deferred; no extra API billing is allowed.
