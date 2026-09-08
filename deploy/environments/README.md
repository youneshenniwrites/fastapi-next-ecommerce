# Free demo environments

Approved 8 September 2026: Vercel Hobby (Next.js), Render Free (FastAPI), and
Neon Free (PostgreSQL). This replaces Azure as the immediate deployment target;
Azure migration is optional future issue #31. Nothing is provisioned by committing
these files. Track setup #44, development previews #45, production CD #46.

## Isolation and configuration

| Setting | Development / PR previews | Production demo |
| --- | --- | --- |
| Render service | forme-api-development | forme-api-production |
| Neon project | Dedicated development project | Separate production project |
| DATABASE_URL | Development credentials only | Production credentials only |
| SECRET_KEY | Independent generated key | Independent generated key |
| Vercel API_BASE_URL | Development API HTTPS URL | Production API HTTPS URL |
| APP_ORIGIN | Exact trusted preview/development HTTPS origin | Exact production HTTPS origin |
| ALLOW_LOCAL_HTTP_SESSIONS | Unset on hosted deployments | Unset |
| GitHub environment | development | production |

Names are proposed resource names, not verified public URLs. Actual provider
subdomains are recorded only after provisioning. Do not purchase a domain.
Never reuse signing keys or database roles between environments. Tests use local
throwaway databases; PR code never receives production secrets. Do not copy real
user data to previews. Hosted data is fictional demo data only.

Neon connection strings must select psycopg explicitly for SQLAlchemy:
`postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require`.
Use independently generated credentials in each project and retain TLS options.
Keep a direct connection string for migrations; runtime pooling is configured only
with tested driver-compatible settings. Store actual values in provider/GitHub
secret stores, never in tracked files or shared logs.

## Provisioning order

1. Sign in to Vercel, Render and Neon. Select Hobby/Free throughout; no paid
   trial, add-on or payment method. Render overages without a payment method pause
   service/builds; two API services share the workspace's free instance hours.
2. Create two separate Neon Free projects in a compatible nearby region. Obtain
   distinct connection strings; run reviewed Alembic migrations before serving
   application traffic. No automatic downgrade or destructive demo reseed.
3. Connect render.yaml only after the databases are ready. Its two services use
   plan: free, independent generated signing keys and user-supplied DATABASE_URL.
   Render may deploy initially on creation; autoDeployTrigger: off prevents later
   commit-triggered deployments. The existing Docker image listens on 0.0.0.0:8000.
4. Configure Vercel with frontend as the root, Next.js framework, Node 24 and the
   locked dependency install. Use `npx next build` on Vercel; the local `npm run
   build` also prepares a standalone server for container/browser testing.
5. Connect preview variables to development and production variables to production.
   Exact preview APP_ORIGIN injection belongs to #45; never wildcard Origin checks
   or derive trust from request Host/forwarded headers. Keep provider auto-production
   deployment disabled until GitHub CD owns promotion in #46.
6. Verify schema, health, catalog and session behavior before publishing demo links.
   /health is liveness, not proof of database readiness: a product request exercises
   the DB. Swagger /docs, /redoc and /openapi.json remain available on each API.

## Delivery sequence

PR: lint/types/contract → unit/integration tests → build/browser tests → Codex
review → development preview. Backend branch changes are tested in disposable CI;
shared development deployment is serialized when explicitly promoted. Frontend
previews do not imply an isolated backend for each PR.

Main: verify exact commit → serialize production deployment → run backward-compatible
migrations once → deploy API and await readiness → deploy website → smoke-test
catalog/session boundaries → publish GitHub deployment links. Disable independent
provider production triggers to prevent bypassing this sequence. #46 implements
these steps; no deployment workflow exists yet.

Keep the previous known-good deploy available. Roll back application revisions
only when compatible with the current database; database rollback/restoration is
an explicit recovery operation. Never auto-downgrade migrations after a failed deploy.

## Free-tier behavior

Render sleeps after inactivity and waking can take about a minute. The current
five-second API timeout deliberately remains bounded; the storefront shows retry
and sessions return a temporary 503 without clearing a valid cookie. #45 must
exercise this on hosting and provide a clear warm-up/retry experience. Do not
retry login/register mutations automatically or keep services awake artificially.
Deployment smoke tests may retry bounded read-only requests while the API warms.

Neon may also suspend compute. Free-tier quota exhaustion can suspend the demo;
this is not an always-on availability guarantee. Monitor provider usage and avoid
payment methods or paid upgrades. The GitHub repository is public: do not expose
secrets or credentials in build artifacts. No separately billed AI API is used.

References: [Render free limits](https://render.com/docs/free),
[Render Blueprint specification](https://render.com/docs/blueprint-spec),
[Vercel Hobby](https://vercel.com/docs/plans/hobby), [Neon Free](https://neon.com/pricing).
