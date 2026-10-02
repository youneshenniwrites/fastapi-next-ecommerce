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
| Backend SENTRY_DSN | Development Sentry DSN (server-only) | Production Sentry DSN (server-only) |
| Backend SENTRY_ENVIRONMENT | `development` | `production` |
| Frontend SENTRY_DSN | Development Sentry DSN (server-only) | Production Sentry DSN (server-only) |
| Frontend SENTRY_ENVIRONMENT | `development` | `production` |
| Frontend NEXT_PUBLIC_SENTRY_DSN | Development browser key (public by design) | Production browser key (public by design) |
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

## Development API access and preview protection

Vercel protection is deployment-specific; it is not database isolation. On
2 October, the stable fictional development API alias returned health/catalog
HTTP 200 and FastAPI's invalid-login HTTP 401 without a protection bypass.
The preview workflow verifies the health and invalid-login contracts before
upload; protection responses or unavailable API access stop preview creation.
Frontend previews still require Vercel Authentication and team membership.

The server-only API client can send `x-vercel-protection-bypass` from
`VERCEL_PROTECTION_BYPASS` when a protected API deployment is deliberately used.
It is optional for the current stable development alias, never `NEXT_PUBLIC_`,
and is not supplied to this minimal preview. If API protection changes, establish
an approved access path rather than copying a production or deployment-write key.
Only fictional data belongs in development; application authentication and account
ownership remain mandatory for private API data. No hosting protection was changed
by VIN-45.

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

PR: backend integration checks, frontend quality checks and production build/browser
tests run on isolated runners → all applicable checks and Codex review pass →
development preview when its separate policy is delivered. Frontend quality and
browser jobs run concurrently; the entire workflow must succeed before delivery.
Backend changes use disposable CI databases; promotion
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

## VINDOR identity

VINDOR is the public product name (formerly FORME). Vercel and Neon project display names use VINDOR.
Repository slug, project IDs, database names/roles and credentials remain stable.
The original FORME domains remain available during the migration. No database
migration or paid domain is needed. See the environment rollout below for URLs.

## VINDOR domain rollout

The free API aliases are `https://vindor-api-production.vercel.app` and
`https://vindor-api-development.vercel.app`; `/docs` opens Swagger UI.
The storefront aliases to activate after this change deploys are
`https://vindor-ecommerce.vercel.app` and
`https://vindor-ecommerce-development.vercel.app`.

Keep each environment's existing `APP_ORIGIN` and set `APP_ORIGIN_ALIASES` to a
JSON array containing only its new storefront origin. No wildcard or automatic
trust of request hosts is allowed. Aliases must be exact HTTPS origins, with at
most five entries; malformed configuration fails closed. Local HTTP sessions do
not support aliases. Both old and new origins then pass the same session checks.
Host-only cookies remain isolated: users sign in separately on each hostname.
Do not mix development and production origins.

Deploy the reviewed change before assigning storefront aliases to the current
production target in each Vercel project. Verify both domains, `/api/session/me`,
valid-origin logout, rejected untrusted-origin logout and image loading. Existing
API_BASE_URL and delivery smoke URLs remain valid through retained FORME aliases.

### Anonymous rate-limit identity (VIN-158)

Separate Vercel frontend/API ingress does not preserve the original visitor via
ordinary forwarded headers. Set `RATE_LIMIT_PROXY_SECRET` to the same dedicated
random value (at least 32 characters, no surrounding whitespace) on the paired
frontend and API. Use a different value for each environment, keep it server-only,
and never reuse `SECRET_KEY` or `VERCEL_PROTECTION_BYPASS`. Do not paste it into
issues/logs. Configure the verifier first, then the signer, and deploy reviewed
revisions; mismatched/missing keys fall back to ordinary network limits rather
than exempting traffic. Rotation requires coordinated configuration and resets
anonymous buckets, so account for the brief fallback window.

The frontend signs only login/register contexts in Vercel runtime. Direct API
requests remain limited by platform IP; local forwarding headers are untrusted.
The signing context expires after 60 seconds (five seconds of clock skew allowed).
No browser-visible configuration is required. Backend positive limit settings are
`RATE_LIMIT_AUTH_REGISTER` (60/minute), `RATE_LIMIT_AUTH_LOGIN` (60/minute) and
`RATE_LIMIT_WRITE` (300/minute per verified user). Disposable browser fixtures
set their own high limits; never raise production thresholds to make CI pass.

Historical partial hosted VIN-158 evidence is [recorded on 1 October 2026](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5936301378): paired development secrets and reviewed source are active, a persistent-connection invalid-login probe reached 429, an owner-observed mobile-data login attempt returned the expected incorrect-credentials message inside that window, and the original connection returned 401 after the retry deadline. A separate direct API probe also reached 429 on request 61 and returned 401 after its retry deadline. The mobile status was observed through the UI, not captured as an HTTP response. It could have reached a different FastAPI instance, so it does not prove hosted signed-identity separation. Existing signed-identity fixtures separately cover visitors behind one shared frontend egress and invalid assertions. At that checkpoint, same-instance proof remained outstanding; the verified closeout below supersedes that limitation.

Counters remain process-local: multiple instances, restarts/eviction and shared NAT constrain protection. This evidence is not a global/distributed-budget guarantee. VIN-238 is closed as delivered through the bounded probe in PR #244; reuse that probe for future regressions rather than duplicating it. Never publish raw IPs or signing context. Do not weaken production thresholds to obtain a passing probe.

Manual Vercel redeploys can omit `SENTRY_RELEASE` supplied by the normal delivery CLI. The configured development fallback at the 1 October checkpoint matches reviewed source `f4e630721184a8cfbb436cf5dd602971337c8002`; CI overrides it with each new release. Before manually redeploying different source, update that fallback to the verified source SHA and check the rendered frontend release. Prefer normal gated CI delivery.

**VIN-158 hosted closeout — 1 October 2026:** [PR #244](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/244) and [independent runner run 36909932392](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909932392) prove actual same-instance isolation on deployed release `847092c`: A429 sequence72 → runner B401 sequence74 → A429 sequence75, then deliberate A401 retry sequence88. All responses share one opaque limiter witness, verified signed context and unchanged limit60. Server order and the one-decision B→C gap exclude instance-separation and expiry/refill false positives; this is not a global distributed budget.

[Cleanup evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/158#issuecomment-5938473213) confirms both flags saved false, successful same-release redeployment in development delivery attempt2, and no diagnostic headers on direct API or storefront failed-login responses at 19:00:05 UTC. Reusable default-off hooks/tests remain for future regressions. No phone coordination, production activation or scheduled wakeups.

### VIN-158 same-instance verification

The default-off `RATE_LIMIT_DIAGNOSTICS_ENABLED` flag enables a bounded development
proof on failed login responses only. Both applications must run on Vercel with
`SENTRY_ENVIRONMENT=development` and the same exact lowercase 40-character
`SENTRY_RELEASE`. No production thresholds, secrets or permissions change.
The API emits an opaque limiter-object/process witness, an atomic decision
sequence, effective limit, signature-verification disposition and release; the storefront forwards
only this complete validated set on login 401/429. It never returns a visitor IP,
bucket, signing assertion, password or token.

After reviewed code is merged and normal development delivery succeeds, enable
the flag in the two dedicated development projects and redeploy that exact release.
A successful delivery status for that same SHA makes a new Development delivery
dispatch skip deployment, even after environment changes. In that case, rerun
the deployment job of its previously successful, exact-revision gated run, then
verify fresh deployment IDs and release metadata. VIN-158 cleanup used
[attempt 2 of run 36909436876](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36909436876/attempts/2);
a successful skipped dispatch is not evidence that new settings took effect.

Dispatch **Development limiter witness** on main. Once its capture step is running,
run `python3 scripts/limiter_probe.py --role throttle --release MERGED_SHA --output first.json`
on the workstation. The runner makes at most 24 fictional invalid login attempts;
the workstation makes at most 61 preparation attempts, eight rejection brackets
and one deliberate retry. Endpoints are fixed to development; redirects are never
followed and missing, mismatched or unverified evidence fails inconclusively.

Download that run's `limiter-observer` artifact and compare with
`python3 scripts/limiter_probe.py --role compare --release MERGED_SHA --first first.json --second observer.json --output proof.json`.
Accept only same-witness, verified-context, matching-release A429 → B401 → A429
with strictly increasing server sequences, followed by A401 deliberate retry.
Every sample must confirm the unchanged 60-request limit; C429 minus B401 must
span fewer than 60 decisions, excluding a shared-bucket expiry/refill false pass.
UTC timestamps are descriptive, not the source of cross-machine ordering.
The proof demonstrates this process-local behavior, not a distributed budget.

Disable the flag in **both** development apps afterward, read back both settings
and wait for Ready redeploys. Confirm all `X-Vindor-Limiter-*` headers are absent
on both the direct API `/api/v1/auth/login` and storefront `/api/session/login`
failed-login responses: storefront suppression alone cannot prove API cleanup.
Retain the gated hook and regression tests for
future repeatable checks. Record actual proof and cleanup before VIN-158 Done;
adding this mechanism alone earns no checklist credit. No schedule, paid service,
production activation or owner phone coordination is involved.

## Reviewed frontend previews (VIN-45)

The [bounded preview design and usage](../../docs/design/frontend-previews.md) uses
manual trusted-main orchestration, exact reviewed PR revisions and the development
frontend Preview target. Host-only sessions share fictional development data; no
production credentials or database clone are provided. The
[2 October hosted checkpoint](../../docs/design/frontend-previews.md#hosted-checkpoint--2-october-2026)
records protected preview creation, fictional login/cart ownership, host isolation
and exact retirement. Application headers/release identity and wrong-origin HTTP
rejection remain unverified on VIN-45; the ticket is not Done. Repeat the full
fictional login/cart/ownership/host journey alongside those checks on the completing
reviewed preview, then retire it; the first checkpoint alone is partial evidence.
