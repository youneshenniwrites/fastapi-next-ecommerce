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

## Delivered application and hosting

- Explicit admin bootstrap and empty-catalog demo seeding; see [demo guide](../demo.md).
- Next.js catalog/detail storefront, generated API contract, state handling and desktop/mobile browser checks.
- Server-mediated login/profile/logout with HttpOnly cookies and exact origin checks (#24 / #41).
- Isolated Vercel/Neon development and production configuration (#44 / #47).
- Both environments publicly deployed and smoke tested from reviewed main 4606e67; idle PostgreSQL connection recovery is merged (#48).
- Production delivery workflow in #49: exact-main CI checks, migration, API then frontend deployment and smoke verification. Keep #46 open until the first GitHub-triggered release is verified.

## Frontend design-system work

Tailwind v4 and shadcn Button, Badge and Skeleton establish the FORME component
foundation (#53). Catalog/navigation layouts now compose shared components and Lucide icons (#54);
account, cart and checkout components are added with their feature tickets.

## Next PRs, in dependency order

1. Finish frontend PR previews with safe development data and exact origins (#45).
2. Account registration/login/profile UI and full journey verification (#25–27).
   Keep authorization in FastAPI.
3. Persistent carts: ownership, quantity changes/removal, stock checks, API and UI.
4. Orders and checkout: price snapshots, authoritative totals, atomic inventory
   handling, idempotency, and concurrent last-item purchase tests.
5. Sandbox payments: verify webhooks, handle duplicate/failure/cancellation events,
   and connect confirmation/order history.
6. Optional Azure migration (#31), only if justified by the portfolio and budget.

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

Hosting setup #44 is complete. Development and production are live; #46 tracks
production workflow acceptance and #45 tracks the remaining frontend previews.
Then return to account UI. Azure is deferred; no extra API billing is allowed.
