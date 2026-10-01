# Observability runbook (Sentry, issue #121)

**Earlier 1 October trace verification (VIN-223):** VIN-223 now has [joined hosted trace evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/223#issuecomment-5931310439): Next.js → FastAPI → database, with matching parent IDs and development environment tags. The backend release is recorded; that historical frontend sample lacks a release attribute, superseded by the VIN-230 hosted proof below. No propagation code change or privacy relaxation was needed. VIN-121 remains Done under the owner-approved 30 September scope split. VIN-223 is outside the revised 29-outcome baseline, and adds no checklist credit. The [canonical portfolio checklist](plans/portfolio-completion.md) now records **19/29 (66%)** after the VIN-146 deadline disposition; no cache speed improvement is claimed. See the [monitoring runbook](#hosted-trace-continuity--verified-1-october-2026) for evidence and limitations.

Both runtimes have SDK integration and serialized privacy tests. Missing DSNs keep
telemetry silent. VIN-121 development monitoring is verified under the revised scope.
VIN-223 verifies one joined hosted storefront/API/database trace. Code tests
do not establish hosted delivery; production activation is outside this rollout.

## Telemetry terms in VINDOR

These examples explain the monitoring model; example values are illustrative.
[VIN-121](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/121)
records completed foundation evidence; VIN-223 records joined trace proof. Optional browser measurements belong to
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
| `SENTRY_RELEASE` | API/frontend build/deployment revision | No; development deploy passes the commit SHA |
| `SENTRY_TRACES_SAMPLE_RATE` | API projects | No (defaults to `0.1`, validated 0–1) |
| `SENTRY_DSN` | Frontend projects (server-only) | Only to activate reporting |
| `SENTRY_ENVIRONMENT` | Frontend projects | No (defaults to `NODE_ENV`) |
| `NEXT_PUBLIC_SENTRY_DSN` | Frontend projects (browser key, public by design) | Only to activate reporting |
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | Frontend projects (build-time public label) | Set `development` for the development app |
| `SENTRY_DIAGNOSTICS_ENABLED` | API/frontend development projects (server-only) | Default false; temporary admin-only synthetic error exercise |

Store DSNs in Vercel project settings and GitHub environment secrets, never in
tracked files. Source-map upload stays disabled until the owner provides
`SENTRY_AUTH_TOKEN`; builds succeed without it.

Frontend release metadata is compiled from the trusted `SENTRY_RELEASE` build value
into `NEXT_PUBLIC_SENTRY_RELEASE` for both browser and server initialization. Only
that non-secret identifier is published; source-map credentials remain server-only.
A redeployment/build is required to change it. Local builds without a release or
Sentry credentials remain supported. VIN-230's normal development deployment and
controlled catalog trace verified these labels and release tags on 1 October;
the earlier VIN-223 trace below remains historical evidence of the previous limitation.

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
span data. Exception text and messages remain `[Filtered]`. Transaction/span labels
are derived from a closed operation vocabulary (for example `Storefront request`,
`API request`, `Next.js function`, `Database query`); unknown operations become
`Application operation`. Existing backend commerce route-template labels remain.
Raw names, URLs, SQL and identifiers never become labels. Unknown span operations
are normalized to `app.operation`. This covers OAuth `username` bodies, credential headers and nested
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

PR #219 merged on 30 September (`79d7923`) and delivers bounded handled-failure logs and commerce metrics. Hosted foundation evidence is recorded on VIN-121. VIN-223 records verified joined cross-service trace evidence. Ordinary validation/authentication failures are not incidents.
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
   acceptance stays incomplete until results are recorded on their owning issue:
   VIN-121 for the revised-scope foundation, VIN-223 for joined-trace evidence.

Counters are emitted without trace sampling, but SDK shutdown, transport failure
or provider quotas can still drop observations. They are not a durable accounting
ledger or proof of exact total traffic. Payment/release guards prevent duplicate
state-transition observations; they do not promise exactly-once telemetry delivery.

## Hosted trace continuity — verified 1 October 2026

Reopening the controlled 30 September request in Sentry across both projects
shows one joined trace: [`515c6e66035041dc8bca1c789e053707`](https://power-h-ltd.sentry.io/explore/traces/trace/515c6e66035041dc8bca1c789e053707/).
The earlier frontend-only inspection was incomplete; its cause is not established.

| Operation | Span ID | Verified parent |
| --- | --- | --- |
| Next.js outgoing HTTP call | `a00f25d4d400d731` | Frontend span `98e7f29cdc229094` |
| FastAPI request | `b64e3de6e4276b16` | `a00f25d4d400d731` |
| Database call | `806563315650c8bd` | `b64e3de6e4276b16` |

Both projects show `development`. The backend records release
`45a9499f732012b1b95c0715b75be951f10fa8a1`; the frontend sample has no displayed
release attribute, so it does not prove frontend release tagging. The root took
871 ms, FastAPI 12.86 ms and database 3.59 ms. One sample is not a p95/p99 baseline.

No propagation fix or privacy relaxation was needed for this historical VIN-223 sample. Its descriptions remain
`[Filtered]`; the later VIN-230 verification below proves readable labels for new traces.
No diagnostic flag, account, production setting or paid service was changed.
Fresh catalog probes on 1 October returned HTTP 200 but were not found under their
supplied trace IDs at inspection; this evidence does not promise every request
will be captured. Sampling and ingestion must be considered when repeating it.

To inspect continuity, select both projects (or All Projects), open the exact
trace, and compare parent IDs across the outgoing HTTP, API and database spans.
Do not infer a propagation defect from a partial waterfall alone. Keep release
coverage and sampling limitations explicit when assessing a particular sample.

## Readable labels and frontend release — verified 1 October 2026

[PR #231](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/231) merged as
`6109cf439e34d2fb0b9432f614f02937c15d7ac5`; required PR/main CI and
[development delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36879202076) passed.
[VIN-230 hosted evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/230#issuecomment-5934081107) verifies
trace `ce620be45d964b57a947b44aea0d0b2f` with **Storefront request → API request → Database query**,
Next.js function labels and Application operation for unknown operations.

| Operation | Span ID | Verified parent |
| --- | --- | --- |
| Frontend outgoing API request | `a71e7f4b9da471b2` | Frontend span `b54e1f39def54fb5` |
| FastAPI request | `9e2020e9cb8d006f` | `a71e7f4b9da471b2` |
| Database query | `9f43e5a874902673` | `9e2020e9cb8d006f` |

Both projects show `development` and release `6109cf439e34d2fb0b9432f614f02937c15d7ac5`.
The deployed public browser bundle and page trace metadata also contain that revision.
The initial read and eight bounded read-only catalog probes used sampled incoming
trace context; configured sampling was unchanged. A normal browser product-page
load also succeeded. Allow for ingestion delay before judging a missing trace.
No temporary diagnostic/admin account, paid feature or production telemetry activation
was needed. Historical traces and filtered exception messages are unchanged.
This proves a connected sample, not a p95/p99 baseline or capture of every request.

That VIN-230 sample predates HTTP method/status enrichment. It therefore has no
retained method or response-code fields; historical events are not rewritten.

## Safe HTTP method and response metadata (VIN-232)

[VIN-232](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/232) restores
bounded HTTP metadata in the privacy filter. Implementation merged in
[PR #235](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/235);
[hosted development acceptance](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/232#issuecomment-5935362557)
is verified and VIN-232 is Done.
The [OpenTelemetry HTTP conventions](https://opentelemetry.io/docs/specs/semconv/http/http-spans/)
identify the method and received/sent response status as useful diagnostic fields.
This change maps the installed Sentry SDK attributes rather than installing another
telemetry SDK or Collector.

- Retain exact standard methods: GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS,
  TRACE and PATCH. Syntactically valid unsupported method tokens become `_OTHER`;
  malformed or non-string values are discarded. No original unknown token is sent.
- Retain only integer HTTP response codes from 100 through 599. Missing status is
  left absent; it is not converted to success. A status code is separate from the
  SDK span status, such as `ok` or `internal_error`.
- Show the validated method alongside the bounded HTTP operation label, such as
  `GET · API request`. Preserve release, environment, duration and parent linkage.
- Continue removing raw URLs, query strings, headers, cookies, request/response
  bodies, identifiers, SQL and arbitrary span attributes. Route-template enrichment
  is outside this small change; do not substitute an actual path for a safe template.

The frontend SDK uses method aliases `http.request.method` and `http.method`, and
status aliases `http.response.status_code` and `http.status_code`. The backend SDK
uses `http.method` and `http.response.status_code`; incoming ASGI transaction
methods are obtained only from validated `request.method`, without retaining the
request object. Sampling, alerts, quotas and production activation are unchanged.

### Hosted development evidence — 1 October 2026

Reviewed PR #235 merged as `f4e630721184a8cfbb436cf5dd602971337c8002`.
[Main frontend CI](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36886781060)
passed, then [normal gated development delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/36887763871)
deployed that revision and passed public smoke checks.

The [fresh joined trace `07501badbea249b7bf8487bf718187d7`](https://power-h-ltd.sentry.io/explore/traces/trace/07501badbea249b7bf8487bf718187d7/)
shows `GET · Storefront request` → outgoing `GET · API request` → FastAPI
`GET · API request` → `Database query`. Frontend outgoing span
`915bfaa2789ffe3c` has parent `8c9379f68c9326af`; FastAPI span
`a526f71889b6b30e` has parent `915bfaa2789ffe3c`, matching the frontend outgoing
span. The outgoing frontend and backend spans both retain GET and HTTP response
status 200. Both projects show `development` and release
`f4e630721184a8cfbb436cf5dd602971337c8002`.

Seven bounded read-only catalog probes and one normal browser product-page load
were used, with unchanged sampling and allowance for Sentry ingestion delay.
This verifies one connected sample, not a latency baseline or universal capture;
historical traces are unchanged. The [issue evidence](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/232#issuecomment-5935362557)
records the proof. Wiki closeout was published as `391628a`; VIN-232 is closed and
Done. No production telemetry activation or paid feature was needed. This
follow-up adds no credit to the separate 29-outcome portfolio baseline.
