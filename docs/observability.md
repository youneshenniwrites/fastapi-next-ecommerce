# Observability runbook (Sentry, issue #121)

Both runtimes report to Sentry on the free Developer plan (no card, no paid
upgrade): the FastAPI API via `sentry-sdk` (#122) and the Next.js storefront
via `@sentry/nextjs` (#123). Telemetry stays completely silent until a DSN is
configured, so local development and secrets-free CI are unaffected.

## Environment variables

| Variable | Where | Required |
| --- | --- | --- |
| `SENTRY_DSN` | API projects (server-only) | Only to activate reporting |
| `SENTRY_ENVIRONMENT` | API projects | No (defaults to `local`) |
| `SENTRY_RELEASE` | API projects | No |
| `SENTRY_TRACES_SAMPLE_RATE` | API projects | No (defaults to `0.1`, validated 0–1) |
| `SENTRY_DSN` | Frontend projects (server-only) | Only to activate reporting |
| `SENTRY_ENVIRONMENT` | Frontend projects | No (defaults to `NODE_ENV`) |
| `NEXT_PUBLIC_SENTRY_DSN` | Frontend projects (browser key, public by design) | Only to activate reporting |

Store DSNs in Vercel project settings and GitHub environment secrets, never in
tracked files. Source-map upload stays disabled until the owner provides
`SENTRY_AUTH_TOKEN`; builds succeed without it.

## Sampling and quota guardrails

Free quotas (5k errors, 5M spans, 5GB logs, 5GB metrics per month) are protected
by signal-specific controls:

- **Traces and spans** — low `SENTRY_TRACES_SAMPLE_RATE` (0.1 in production, 1.0
  in local dev). If span quota is at risk, reduce this value first; never add
  payment.
- **Errors** — spike protection in the Sentry project settings (inbound data
  filters, rate limits per DSN). The existing auth/write throttling
  ([abuse protection](api.md#abuse-protection-rate-limits)) limits abusive
  error-generating traffic at the application layer.
- **Logs** — structured log emission is guarded by severity level (INFO in
  production). Reduce log verbosity in Sentry project settings if quota is at
  risk.

## Privacy scrubbing

`send_default_pii` is off everywhere. The backend `before_send` additionally
filters authorization headers, cookies, nonstandard credential headers
(`x-api-key`, `x-auth-token`, `x-vercel-protection-bypass`), sensitive body and
query keys, and all user PII except the id. The browser key is public by design;
no other credentials belong in client variables.

## Verifying without a DSN

Unit suites cover init gating, option builders, scrubbing, and the 429 counter
without contacting Sentry. The production build compiles the instrumentation
with no secrets. Live trace/error screenshots from development require the owner
prerequisite (Sentry org + DSNs) and remain the outstanding verification step.

## When an alert fires

New-issue email alerts route to the owner. Read the trace from the storefront
span through the API span, reproduce locally with fictional data, fix on a task
branch with regression coverage, and record evidence in the PR. Never paste
customer data into tickets; this demo carries none.
