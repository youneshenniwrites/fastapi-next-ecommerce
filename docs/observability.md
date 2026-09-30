# Observability runbook (Sentry, issue #121)

Both runtimes have SDK integration and serialized privacy tests. Missing DSNs keep
telemetry silent. VIN-121 remains incomplete until development configuration and
hosted trace, error, log, metric, alert and quota evidence are recorded. Code tests
do not establish hosted delivery; production activation is outside this rollout.

## Telemetry terms in VINDOR

These examples explain the planned monitoring model, not verified hosted results.
[VIN-121](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/121)
owns hosted acceptance; optional browser measurements belong to
[VIN-204](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/204).

| Term | What it answers | Checkout example |
| --- | --- | --- |
| Log | What happened at one moment? | A webhook processing attempt failed, with a safe reason code and trace correlation. |
| Metric | How often, how much, or how slow over a time window? | Payment-session request count, technical error ratio and duration distribution. |
| Trace | Where did one operation spend time? | A storefront request calls FastAPI, which calls the database and Stripe. |
| Span | What happened during one step of a trace? | The duration of the Stripe API call. Spans can overlap; their durations need not add up to the total. |
| APM (application performance monitoring) | Which application operation or dependency is slow or failing? | Compare checkout latency with its database and Stripe spans. APM is a capability, not another required vendor. |
| RUM (real user monitoring) | What did visitors experience in their browsers? | Observe page loading, responsiveness and layout stability; controlled demo runs are not representative real-user evidence. |
| RED (rate, errors, duration) | Is a service healthy? | Requests per minute, unexpected technical failures divided by completed requests, and p95 duration for the same operation/window. |

### Reading latency and browser measurements

- **p95/p99:** the 95th/99th percentile of the measured duration distribution.
  Roughly 95%/99% of observations are at or below that value. Always report the
  time window and sample count; a handful of demo requests cannot establish a
  reliable tail-latency baseline.
- **LCP (Largest Contentful Paint):** when the largest eligible visible content
  element renders, such as the main product image; measured in milliseconds.
- **INP (Interaction to Next Paint):** responsiveness across qualifying browser
  interactions, such as clicking Add to basket; measured in milliseconds. It is
  not the full API completion time. No qualifying interaction means no INP
  observation, not a zero.
- **CLS (Cumulative Layout Shift):** a unitless score for unexpected layout
  movement, such as content shifting when an image loads.

### Boundaries that keep the evidence honest

Stripe webhook delivery is a separate asynchronous request. Correlate it safely
with the payment workflow; do not assume hosted Stripe continues our trace.
Expected payment declines and validation failures are distinct from technical
outages. Sampled traces do not supply exact total request counts.

Use bounded operation/outcome labels and safe correlation fields; never put
customer/order identifiers into metric labels or personal data into logs.
Examples above do not bypass the privacy allowlists: new signals require
serialized-payload tests and hosted verification before claiming delivery.

An **OpenTelemetry Collector** receives, processes and exports telemetry. It is
not required for the current SDK-to-Sentry design; adding one or another vendor
would need a concrete requirement and separate scope.

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
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | Frontend projects (build-time public label) | Set `development` for the development app |
| `SENTRY_DIAGNOSTICS_ENABLED` | API/frontend development projects (server-only) | Default false; temporary admin-only synthetic error exercise |

Store DSNs in Vercel project settings and GitHub environment secrets, never in
tracked files. Source-map upload stays disabled until the owner provides
`SENTRY_AUTH_TOKEN`; builds succeed without it.

## Sampling and quota guardrails

The existing Developer account was inspected on 29 September 2026: no payment
method, 5k errors, 5M spans, 5GB logs and 5GB application metrics included, with
zero usage at inspection. Recheck limits before future activation; these are dated
account observations, not permanent vendor guarantees. Use signal-specific controls:

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

## Privacy boundary

Both error and transaction hooks keep a narrow structural allowlist: event and trace
identifiers, timestamps, severity, release/environment, exception type, line/column
numbers and simple static code identifiers. Local filenames lose directory roots;
Next bundle filenames retain only the artifact path. Valid source-map debug UUIDs
and matching sanitized artifact paths survive for symbolication. They discard complete request/user data,
URLs, arbitrary extras/contexts/tags, breadcrumbs, stack source/local variables and
span data. Exception text, messages, transaction names and span descriptions become
`[Filtered]`. This covers OAuth `username` bodies, credential headers and nested
arrays by removing their containing data, rather than guessing every sensitive key.
Backend exception local-variable capture is explicitly disabled.

Backend logs have their own hook: severity, timestamp and trace correlation survive;
free-text bodies and application attributes do not. Configured release/environment
attributes survive. Rate-limit metrics use server route templates rather than raw request paths.
Commerce metrics/logs retain only bounded operation, outcome and reason values
plus release/environment; customer/order IDs and arbitrary labels are dropped. Frontend logs remain disabled; a defensive
log hook removes message text and attributes if enabled later. Session replay,
attachments and profiling are not enabled. Enabling a new channel or adding custom
structural fields requires its own privacy review. Trusted release/environment and
code identifiers must never be populated with user data.

This deliberately loses request details, breadcrumb history and exception messages.
Use exception type, code identifiers/line numbers and trace IDs for diagnosis; do not
reintroduce raw payloads to recover convenience. These controls are not a claim that
arbitrary future SDK channels or application-supplied metadata are automatically safe.

## Verification before activation

In-memory transports exercise the pinned Python SDK and both Node/browser clients,
serialize actual error and transaction envelopes, and assert private fictional values
are absent while useful diagnostics survive. The Python suite also checks emitted
log and metric envelopes. No tests contact Sentry. The browser-default regression also exercises the installed SDK integrations with
fictional identity and navigation. `BrowserSession` is explicitly removed because
session envelopes bypass the event hooks and can contain identity/IP fields.
Error and trace capture remain enabled and positively asserted; Replay stays off. Option tests cover missing DSNs and conditional
source-map uploads, which require all of `SENTRY_AUTH_TOKEN`, `SENTRY_ORG` and
`SENTRY_PROJECT`. Never expose the upload token through a public environment variable.

PR #219 merged on 30 September (`79d7923`) and delivers bounded handled-failure logs and commerce metrics. Remaining
VIN-121 work: configured development evidence for errors, cross-service traces, release/environment,
logs/metrics and an alert. Ordinary validation/authentication failures are not incidents.
Do not mark the issue complete or activate telemetry from this prerequisite alone.

## When an alert fires

New-issue email alerts route to the owner. Read the trace from the storefront
span through the API span, reproduce locally with fictional data, fix on a task
branch with regression coverage, and record evidence in the PR. Never paste
customer data into tickets; this demo carries none.


## Development verification procedure

Use the two development Vercel projects only. They deploy with Vercel's
`production` target inside those separate development projects; the production
storefront/API projects remain untouched. Set their Sentry environment labels to
`development`, including the browser build-time label. Redeploy the reviewed
revision through the existing exact-main CI gate after configuring DSNs.

1. Confirm the account is still free with no payment method, project spike
   protection enabled, and low trace sampling. Keep Replay/profiling off.
2. Exercise fictional cart writes, order placement and sandbox payment-session
   creation. In Sentry inspect `commerce.requests` and `commerce.duration` by
   operation/outcome and the same release/environment/window. Calculate technical
   error ratio using completed attempts in that same window. Report p95 and sample
   count; a small smoke sample does not establish reliable p99 performance.
3. Follow the storefront/API trace IDs and span parents. Stripe webhook delivery
   is a separate incoming request, not an automatically connected parent span.
4. Inspect `payment.confirmation_delay` only for valid first-paid transitions.
   It measures the signed provider event's creation time to the persisted local
   payment-event timestamp, in milliseconds. Invalid or future timestamps produce
   timing-status observations instead of fabricated zero latency. Duplicate
   deliveries do not create a new paid-transition observation.
5. To prove a backend error/alert, temporarily set
   `SENTRY_DIAGNOSTICS_ENABLED=true` on the development API with
   `SENTRY_ENVIRONMENT=development`. An authenticated active administrator may
   POST `/api/v1/diagnostics/sentry` to trigger the fixed synthetic exception.
   It is absent from public OpenAPI, returns 404 while disabled/outside development,
   and denies non-admin users. Disable the flag after proof and confirm 404 again.
6. To prove Next.js browser and server error delivery, temporarily set the same
   server-only `SENTRY_DIAGNOSTICS_ENABLED=true` flag on the development storefront
   with `SENTRY_ENVIRONMENT=development`. Configure both runtime DSNs and the
   browser build-time environment first. Sign in as an active administrator and
   visit `/diagnostics/sentry`. Each button rechecks privileges through FastAPI;
   a disabled account or non-admin cannot trigger either test. The server action
   also validates the request origin. Both tests explicitly capture fixed errors
   and wait up to two seconds for delivery; they do not crash a worker or prove
   automatic unhandled-error capture. Confirm the two events in Sentry with
   `development` and the deployed release, rather than treating the flush message
   as evidence of ingestion. Disable the storefront flag, redeploy, confirm the
   page returns 404 and disable any temporary administrator immediately afterward.
   The page is unlinked, uncached and noindex; the flag and environment gates,
   not obscurity, control access. Never introduce a public browser toggle.
7. Record sanitized error/log/metric evidence, release/environment, trace linkage,
   alert receipt and resolution. Never paste credentials into tickets. Hosted
   acceptance stays incomplete until those results are recorded on VIN-121.

Counters are emitted without trace sampling, but SDK shutdown, transport failure
or provider quotas can still drop observations. They are not a durable accounting
ledger or proof of exact total traffic. Payment/release guards prevent duplicate
state-transition observations; they do not promise exactly-once telemetry delivery.
