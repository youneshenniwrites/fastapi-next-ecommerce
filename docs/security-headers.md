# HTTP security headers — VIN-126

VIN-248's MIME/referrer baseline is delivered. VIN-126 adds framing denial,
transport guidance and a staged content security policy (CSP). The first stage
is **report-only**, not completed script-injection protection; source acceptance
stays open until the tested candidate is enforced and hosted in both environments.

## Policy boundaries

Storefront application pages use a fresh 128-bit nonce per HTML request. Proxy replaces
caller-supplied CSP, private render-policy and nonce headers before Next.js renders, and the root layout
waits for a request. Pages are private/no-store; immutable static assets retain
normal caching. Vercel’s hosted stage-one HTML omitted framework nonces even
though the response policy carried them; standalone output did not. A guarded
Next.js 16.3.6 compatibility patch lets the renderer read the same policy from
`x-vindor-render-csp`, using Next’s existing validated nonce parser. Proxy
overwrites this private transport on application routes and strips all caller
policy/nonce headers on framework/tunnel exceptions. It is not an additional
browser permission. The patch validates exact original or completely patched
CommonJS/ESM and stable webpack/Turbopack development/production bundles before
writing any file and rejects upgrades/unknown
sources until explicitly reviewed. Remove it when an upstream supported nonce
transport is available, then reverify hosted nonces and spoofing defenses.

The renderer receives the candidate CSP so framework scripts
receive matching nonces. Browsers receive the candidate in
`Content-Security-Policy-Report-Only` and enforced `frame-ancestors 'none'` plus
`X-Frame-Options: DENY` during this first stage.

The production candidate allows only nonce-bearing trusted scripts and their loaders,
without `unsafe-inline` or `unsafe-eval`. Development eval is a Next.js debugging
exception. Zod's optional JIT is disabled using its supported `jitless` option;
validation schemas and messages stay unchanged. Sentry sends through the existing
same-origin `/sentry-tunnel`; CSP grants no additional ingestion origin. Sandbox
Checkout uses a validated top-level navigation after a same-origin Server Action,
so no Stripe script, iframe or connection permission is needed.

The storefront retains `style-src 'self' 'unsafe-inline'`: Next.js image/streaming
and Radix components, including privacy boundaries, use inline styles. This
permits styling, not inline JavaScript. Images are local plus data/blob sources;
fonts and browser connections stay same-origin. Objects are disabled, base URLs
and form submissions are same-origin, and framing is denied.

The API's JSON/error candidate denies content by default. Swagger/ReDoc/OAuth
redirect HTML uses fresh nonce-bearing scripts and private/no-store responses.
Documentation loads nonce-bearing jsDelivr UI scripts without allowing arbitrary
CDN scripts, and permits the FastAPI favicon.
Swagger styles permit its existing CDN stylesheet; documentation style attributes
are an explicit UI exception. ReDoc's nonce reaches its generated style elements.
Its pinned 2.5.4 bundle
creates an empty style node before inserting the perfect-scrollbar stylesheet;
only those two exact stylesheet hashes are additionally allowed, alongside the
ReDoc logo image origin. Updating that bundle requires rechecking its hashes.
Google Fonts are disabled in favor of system fonts. Its search needs a blob worker.
These exceptions are restricted to documentation, not API JSON responses.

Application HSTS is host-only `max-age=31536000`, without adding subdomain or
preload commitments. The API sends it on authoritative HTTPS ASGI scopes and does
not trust caller-supplied forwarded protocol headers. Next.js config sends it on
responses; browsers ignore it over HTTP, keeping the disposable local HTTP stack
usable. Vercel already advertised a stronger edge HSTS header before this work;
inspect the actual hosted value rather than assuming an application override.

Framework static/optimized-image resources and the exact Sentry tunnel route
do not need a renderer nonce, but still cross Proxy to strip caller render-policy
headers without changing their caching. API and photo paths pass through Proxy so
unknown paths returning HTML errors receive the candidate; valid public photos
retain their normal cache policy.
Next's automatic trailing-slash redirects and provider-generated responses remain
outside the application policy, as documented in [the baseline](api.md#baseline-response-headers).
A CSP does not replace session ownership, origin checks, output escaping or
provider URL validation.

## Rollout and verification

1. Deliver the report-only candidate and framing/HSTS stage through a reviewed PR.
2. Observe `securitypolicyviolation` events during local and hosted catalog,
   account, cart, checkout/order, image and Sentry checks; triage before enforcement.
3. Promote the verified candidate in a second focused PR. Repeat compatibility,
   deliberate script rejection, nonce freshness/spoofing and hostile-frame checks.
4. Verify actual development and production releases/headers, then close VIN-126.

The browser suite records directive/disposition only across its normal journeys.
Separate controlled probes demonstrate report-only script execution/reporting and
enforced framing. It stores no raw CSP report body, private URL or script sample,
and introduces no reporting endpoint or paid service. This is bounded verification,
not continuous observation of all visitors. Private-account failure artifacts
remain disabled by the existing test configuration.

Rollback uses the reviewed prior deployment or restores the candidate to
report-only while retaining baseline headers and framing denial. Do not relax
production scripts to `unsafe-eval` to silence a compatibility finding.

Sources: installed Next.js 16.3.6 CSP guide and [official nonce guidance](https://nextjs.org/docs/app/guides/content-security-policy),
[HSTS behavior](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security),
and installed FastAPI documentation generators.

## Hosted rollout checkpoint — 2 October 2026

PR #254 deployed as `ec29964c41a0793e753a2406ddda96f053bd2d1a` through
[development](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37049058759)
and [production](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37049058661).
Development’s public catalog response had a fresh policy nonce and private/no-store
caching, but its actual bootstrap scripts had no nonce attribute. This prevents
promotion: enforcing that policy would break hydration. The compatibility change
remains report-only until actual hosted nonce equality and zero unexpected reports
are verified. Local enforcement tests passed 137 with two existing skips; that
local proof does not replace this failed hosted check. The compatibility regression
uses a disposable browser-server preload that removes both standard CSP request
headers, including internal forwarding: it fails the same nonce equality/report
assertions with the stock production renderer. The preload is activated only by
Playwright fixtures, never by deployment scripts or app startup. Hosted API docs
passed nonce equality, Swagger health execution and ReDoc search with zero policy
reports in both environments; storefront/Sentry observation remains unfinished.

The [upstream discussion](https://github.com/vercel/next.js/discussions/95259)
reports production request-CSP stripping. It is corroborating reporter evidence,
not proof of our edge’s internal cause; the raw HTML mismatch above is observed.
