# Delivery roadmap

## Landed foundation

- Authentication repair, active-user/admin checks, bcrypt compatibility, and 22 regression tests (PR #1).
- Locked Python dependencies, Ruff checks, and root GitHub CI (PR #1).

## Current delivery

- Reproducible local credentials and Docker/PostgreSQL setup.
- Initial migrations and upgrade/downgrade/metadata checks.
- Agent instructions and three focused repository skills.

## Next PRs, in dependency order

1. Catalog correctness: replace Float money with a chosen explicit currency/minor-unit
   or decimal representation, preserve existing values through a reviewed migration,
   bound pagination, validate names/stock/prices, and add DB constraints. Prove
   invalid/null updates fail and valid CRUD works for admins.
2. Admin bootstrap: an explicit command to create/promote the first admin without
   hardcoded credentials; verify idempotence and prevent accidental password reset.
3. Next.js catalog: App Router, TypeScript, locked runtime, generated OpenAPI client,
   product list/detail, loading/empty/error states, and browser checks.
4. Customer frontend auth: login/register/profile, server-mediated secure session
   handling, logout and error states. Keep authorization in FastAPI.
5. Persistent carts: ownership, quantity changes/removal, stock checks, API and UI.
6. Orders and checkout: price snapshots, authoritative totals, atomic inventory
   handling, idempotency, and concurrent last-item purchase tests.
7. Sandbox payments: select the provider, verify webhooks, handle duplicates,
   failures/cancellations, and connect confirmation/order history.
8. Deployment: finish Terraform with explicit environment/cost decisions, staging,
   secrets, TLS, migrations, logs, backup/restore, and rollback evidence.

Each PR includes acceptance evidence, self-review findings, and passing CI before
merge under the user's authorization. Production/cloud deployment and paid external
services need their own authorization. Do not add caching/search infrastructure
until the working shopping journey has a measured need.
