# Free demo environments

Approved 8 September 2026: GitHub for delivery, Vercel Hobby for both Next.js and
FastAPI, and Neon Free for PostgreSQL. Render was rejected after its Free service
creation required a payment card; the owner requested a no-card alternative and
fewer providers. Azure migration is optional future #31. No paid upgrades, payment
methods, purchased domain or separately billed AI API are authorized.

Track configuration #44, development/previews #45 and production CD #46. The two
Neon projects are created in Frankfurt on PostgreSQL 17, matching local/CI. Both
passed Alembic upgrade and metadata checks. Both development and production are verified over HTTPS. Production was first
released from reviewed main 4606e67; the workflow below automates subsequent releases.

## Verified production links

- [Storefront](https://forme-ecommerce.vercel.app)
- [Swagger API docs](https://forme-api-production.vercel.app/docs)
- [OpenAPI contract](https://forme-api-production.vercel.app/openapi.json)

## Verified development links

- [Storefront](https://forme-ecommerce-development.vercel.app)
- [Swagger API docs](https://forme-api-development.vercel.app/docs)
- [OpenAPI contract](https://forme-api-development.vercel.app/openapi.json)

Catalog, product detail, registration/login, secure cookies, profile, cross-origin
rejection and logout were exercised on hosting with fictional data.

## Isolation and configuration

| Setting | Development | Production demo |
| --- | --- | --- |
| Vercel API project | forme-api-development | forme-api-production |
| Vercel frontend project | forme-ecommerce-development | forme-ecommerce |
| Neon project | forme-development | forme-production |
| Database / role | forme_development / forme_development_owner | forme_production / forme_production_owner |
| DATABASE_URL | Development database only | Production database only |
| SECRET_KEY | Independent generated key | Independent generated key |
| Frontend API_BASE_URL | Development API HTTPS URL | Production API HTTPS URL |
| APP_ORIGIN | Exact trusted deployment HTTPS origin | Exact production HTTPS origin |
| ALLOW_LOCAL_HTTP_SESSIONS | Unset on hosting | Unset |
| GitHub environment | development | production |

Separate Vercel projects isolate the shared development deployment from the public
production demo. Vercel's `production` target means a project's stable URL: for the
development projects it still uses development data. PR previews belong to the
development frontend project only. Tests use disposable local databases; fork PRs
never receive deployment credentials. No real personal/customer data belongs here.

The links above were verified against the configured provider aliases. Never reuse signing keys or database credentials
between environments. The frontend receives no database password or API signing key.
Store credentials in provider/GitHub secret stores, never tracked files or logs.

Neon URLs must select psycopg explicitly for SQLAlchemy:
`postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require`.
Retain TLS parameters. Migrations use direct connections. Verify runtime connection
recovery and bounded connection use before public deployment; suspended Neon compute
or serverless process reuse must not result in permanently stale connections.

## Provisioning and verification

1. Keep Vercel on Hobby and Neon on Free; no card or upgrade. Free quotas may pause
   the demo. It is a personal, non-commercial interview showcase.
2. Create separate Neon projects/roles and independent signing keys. Run reviewed
   Alembic migrations before serving traffic; never auto-downgrade or reseed data.
3. Set each API project's root to backend, framework to FastAPI and Python to 3.12
   via .python-version. Vercel discovers app/main.py:app. It uses the native Python
   runtime rather than the Dockerfile. The lockfile remains authoritative.
4. Set each frontend root to frontend, framework to Next.js and Node to 24.
   vercel.json uses npm ci and npx next build. The local npm run build continues
   preparing the standalone server used by container/browser tests. next.config.ts
   disables standalone output only when VERCEL=1 because the Next.js 16.3 adapter
   otherwise fails on a missing trace file. Both cloud and local builds are tested.
   Vercel manages Node 24 patch releases (validated at 24.19.0); local/CI pin 24.20.0.
5. Configure environment-specific secrets and exact APP_ORIGIN values. Preview
   origin injection is #45; never trust request Host/forwarded headers or wildcard
   the Origin check. An invalid/missing origin must fail closed for session writes.
6. Keep direct Git deployments disabled in both vercel.json files. GitHub Actions
   will upload a clean, tested revision through the CLI; a GitHub App repository
   connection is optional (the owner connected the frontend repository). The .vercelignore files exclude local credentials
   and build caches from manual CLI uploads.
7. Verify /health, catalog DB reads, /docs, /redoc, /openapi.json and session behavior
   over HTTPS before advertising URLs. /health alone is liveness, not DB readiness.

GitHub environments currently restrict deployment workflow refs to main. A future
preview workflow must run trusted orchestration from main and validate the source
PR before using development credentials. Do not inject secrets into arbitrary PR
code, or add a write-enabled pull_request_target workflow that executes PR code.

## Delivery sequence

PR: lint/types/contract → unit/integration tests → build/browser tests → Codex
review → development preview. Backend changes use disposable CI databases; promotion
to the shared development API is explicit and serialized. A frontend preview does
not imply a dedicated backend/database for every PR.

Main: verify exact commit → serialize deployment → run backward-compatible migrations
once → deploy API and verify readiness → deploy frontend → smoke-test catalog and
session boundaries → publish GitHub deployment links. `production.yml` implements
this sequence after successful main CI. It requires Backend CI, Frontend CI,
Dependency audit and Review gate tests for the same main push; missing, failed or
running evidence prevents release. It skips already successful releases and
serializes production runs. The GitHub environment exposes the release URL. Do not deploy a newer unverified SHA
just because it became the current main while a previous run was executing.

Keep the last known-good deployment. Roll back application revisions only when
compatible with the current schema. Database recovery is an explicit operation,
not an automatic downgrade after failed deployment. A failed smoke check leaves
the run failed; a partial API/frontend release requires investigation and an
explicit compatible application rollback. Free retention limits are not
a backup guarantee; document a tested recovery procedure before relying on one.

## Runtime limits

Vercel Functions are request-scoped serverless processes, not persistent containers.
No local persistent writes or durable background jobs are assumed. Neon can suspend
compute. SQLAlchemy validates pooled connections at checkout (`pool_pre_ping`)
and replaces those closed while idle. PostgreSQL CI exercises this by terminating
only a test-owned idle connection and verifying the next checkout succeeds. This
does not replay interrupted transactions or retry mutations. Retain bounded
request timeouts and verify hosting recovery. The existing five-second
frontend timeout may show retry/temporary 503 while services initialize. Do not
retry login or other mutations automatically. Deployment smoke checks may retry
bounded read-only requests. Future carts/checkout must keep state and transactions
in PostgreSQL, not process memory.

References: [Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Python runtime](https://vercel.com/docs/functions/runtimes/python),
[Vercel Hobby](https://vercel.com/docs/plans/hobby), [Neon Free](https://neon.com/pricing).

## CI credentials and operations

GitHub's production environment contains `DATABASE_URL` and `VERCEL_TOKEN` secrets,
and `VERCEL_ORG_ID`, `VERCEL_API_PROJECT_ID`, `VERCEL_FRONTEND_PROJECT_ID` variables.
Runtime signing keys remain in Vercel. The same credential names are prepared in
development for #45, but frontend PR previews are not implemented by this workflow.
The team-scoped CI token expires **7 December 2026**; replace it in both GitHub
environments before expiry. Never store it in the repository or command examples.

Use Actions → Production delivery → Run workflow on main to retry after fixing
provider configuration. It still requires all successful exact-commit CI. The
workflow is triggered by CI completion, not by raw PR code; production secrets are
restricted to main. Direct Vercel Git deployments remain disabled.

For an application rollback, inspect the last known-good Vercel deployment and
confirm schema compatibility, then promote that deployment through Vercel. Record
both API and frontend revisions and rerun smoke checks. Do not downgrade the
database automatically. A manually rolled-back version is temporary: the next
eligible main release will advance production again.
