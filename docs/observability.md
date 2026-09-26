# Observability runbook (Sentry, issue #121)

Both runtimes have SDK integration, but **hosted activation remains blocked** until
privacy checks pass and the owner supplies configuration. This privacy prerequisite
does not establish live trace continuity, alert delivery or a verified dashboard.
Missing DSNs keep telemetry silent; no telemetry configuration is changed by this PR.

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
attributes survive. Rate-limit metrics use matched server route templates rather
than raw request paths; their hook permits only the fixed rejection counter and
its route/release/environment attributes. Frontend logs remain disabled; a defensive
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
log and metric envelopes. No tests contact Sentry. Browser session envelopes emitted by default integrations
are outside these error/transaction callback tests; assess those channels before
hosted activation, especially before introducing SDK user identity. Option tests cover missing DSNs and conditional
source-map uploads, which require all of `SENTRY_AUTH_TOKEN`, `SENTRY_ORG` and
`SENTRY_PROJECT`. Never expose the upload token through a public environment variable.

Remaining VIN-121 work: sanitized reporting of meaningful handled failures, then
configured development evidence for errors, cross-service traces, release/environment,
logs/metrics and an alert. Ordinary validation/authentication failures are not incidents.
Do not mark the issue complete or activate telemetry from this prerequisite alone.

## When an alert fires

New-issue email alerts route to the owner. Read the trace from the storefront
span through the API span, reproduce locally with fictional data, fix on a task
branch with regression coverage, and record evidence in the PR. Never paste
customer data into tickets; this demo carries none.
