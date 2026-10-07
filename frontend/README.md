# VINDOR storefront

A fictional desk-accessories catalog for the senior SWE portfolio. Next.js App
Router and React render catalog and detail pages against FastAPI; the home page
is server-rendered and pages through the full catalog with URL-owned search, stock
filtering and sorting. Prices remain decimal strings from the API and are
formatted with integer pennies, without floating-point money math.

## Run locally

Install Node 24.20.0 (or use nvm install from this directory) and npm 11.19.1.
From the root, run make dev and make demo. Then from frontend/:

```sh
cp -n .env.example .env.local
# Existing file? Merge the session settings below before continuing.
npm ci
npm run dev
```

Open http://127.0.0.1:3000. The server defaults to http://127.0.0.1:8000 for FastAPI.
The example also sets `APP_ORIGIN=http://127.0.0.1:3000` and explicit loopback
HTTP session permission; these are required for local account actions. Preserve
an existing `.env.local`. If you change either port, update `API_BASE_URL` and
the exact browser `APP_ORIGIN` there. Never enable local HTTP sessions on a hosted
deployment. No CORS
configuration is necessary: only the Next.js server calls FastAPI. Fetches are
uncached. Reads have a five-second complete-response deadline; writes use a
five-second transport cancellation signal and are never automatically replayed.
An uncertain cart write stays read-only until a fresh authoritative snapshot.
Known offline route refreshes are deferred so the recovery control remains
available. See [recovery and its limitations](../docs/design/cart-storefront.md#request-deadlines-and-timeout-recovery).

For an older `.env.local` containing only `API_BASE_URL`, `cp -n` makes no change.
Before `npm run dev`, add or update `APP_ORIGIN=http://127.0.0.1:3000` and
`ALLOW_LOCAL_HTTP_SESSIONS=true` in that existing file, substituting your actual
browser port and preserving its other values. Missing session settings cause
account actions to return service-unavailable responses.

## Verification

| Command              | Check                                                                    |
| -------------------- | ------------------------------------------------------------------------ |
| npm run lint         | ESLint, TypeScript lint rules, React hooks and Next.js rules             |
| npm run format:check | Prettier formatting                                                      |
| npm run typecheck    | TypeScript and generated route types                                     |
| npm test             | Maintained library and selected interaction tests with enforced coverage |
| npm run build        | Production Next.js standalone build                                      |
| npm run test:e2e     | Desktop/mobile catalog and full account journey, axe and fault states    |
| npm audit            | Locked dependency vulnerability audit                                    |
| npm run api:check    | Generated schema/type drift against Git                                  |

Before browser tests, run make setup at the root, npm run build here, and
npx playwright install chromium (add --with-deps on Linux). Tests use ports
18300/18301 and 3300/3301, migrate a temporary SQLite database, and seed it. The
backend CI suite separately verifies PostgreSQL. Browser HTML reports are retained in GitHub artifacts for 14 days. Account/session
projects disable automatic screenshots and traces to avoid recording credentials;
explicit screenshots contain only empty forms or mocked fictional profiles. Other
browser projects retain traces on failure.

Regenerate the API contract from backend/ with uv run python -m scripts.export_openapi,
then npm run api:generate here. No running database is needed. Commit openapi.json
and src/lib/api/schema.d.ts together. Runtime calls use openapi-fetch and generated types.

## Scope and design

VINDOR uses locally stored, licensed WebP photography, system fonts and Lucide icons.
See [photo credits](PHOTO_CREDITS.md) for sources and licences. Photographs are
representative, not exact product specifications or brand endorsements. Unknown
products use a neutral Lucide placeholder.

The catalog reads FastAPI's [catalog search endpoint](../docs/api.md#catalog-search-and-pagination-vin-289)
on the server, so filtering, ordering and counts cover the whole catalog; see
[Collection URLs](#collection-urls-vin-287). Registration, login and the signed-in cart are implemented;
VIN-120 checkout submission, confirmation and order history merged in PR #188; VIN-30 sandbox payments merged in PR #194 and were verified on development on 23 September; production payments remain disabled. See the canonical completion plan for merge/deployment status. See the [cart architecture and manual
walkthrough](../docs/design/cart-storefront.md). Automated accessibility checks supplement manual keyboard/mobile
review; they do not constitute a full accessibility certification.

ESLint 10 uses the official Next plugin directly with typescript-eslint and React
hooks rules. This avoids incompatible legacy plugins in eslint-config-next.
npm run build assembles .next/standalone with static assets. Run npm start with
PORT and HOSTNAME environment variables to serve that package. CI archives the
contents; after extraction use node server.js with API_BASE_URL configured.

The [development demo](https://vindor-ecommerce-development.vercel.app) runs on Vercel; production CD runs through GitHub Actions. See ../docs/ci.md for the delivery pipeline.

## Customer session API

Copy `.env.example` to `.env.local` for loopback development and open
http://127.0.0.1:3000 (the origin must exactly match APP_ORIGIN). HTTPS deployments
set APP_ORIGIN to their public origin and omit ALLOW_LOCAL_HTTP_SESSIONS.

POST /api/session/login accepts JSON email/password; GET /api/session/me returns
the active profile; POST /api/session/logout clears the HttpOnly cookie. Browser
mutations require the configured APP_ORIGIN or an explicitly configured HTTPS
APP_ORIGIN_ALIASES entry (JSON array, at most five). Host-only cookies are not
shared between aliases. Invalid alias configuration fails closed. All responses are private/no-store,
return no bearer token in JSON and use bounded upstream requests. See
[session design](../docs/design/customer-sessions.md) for errors, expiry and
stateless logout limitations. Visit `/register` to create a demo account and
`/login` to sign in. Registration uses the same-origin `/api/session/register`
handler; a successful login always returns to the collection. Profile/navigation
and sign-out are implemented in `/account`. Desktop/mobile tests cover the complete
registration → login → profile → logout journey. See the [account verification
guide](../docs/account-journey.md) for a manual walkthrough, test evidence and limits.

## Collection URLs (VIN-287)

The URL owns the applied collection selection, so links, refresh, Back/Forward and
shared links reproduce the same controls and results.

| Parameter  | Meaning                                         | Accepted values                                                  |
| ---------- | ----------------------------------------------- | ---------------------------------------------------------------- |
| `category` | One workspace category                          | A stored slug such as `lighting`; omitted for All                |
| `q`        | Applied search, after an explicit Search submit | 1-100 characters after trimming; `%` and `_` are literal         |
| `in_stock` | Only products with stock                        | `1` (omitted otherwise)                                          |
| `sort`     | Ordering                                        | `featured` (default, omitted), `name`, `price-asc`, `price-desc` |
| `page`     | 24-product page                                 | Integer from 1 to 4167 (the API's maximum offset); 1 is omitted  |

Canonical links list recognised, non-default parameters in that order, for example
`/?category=lighting&q=lamp&in_stock=1&sort=price-asc&page=2#collection`. Changing
search, stock, sort or category resets to page 1. All is the omitted `category`
parameter, not a stored category. A well-formed unknown slug stays in the URL and
shows that the category does not exist. Unknown parameters are ignored. A
recognised parameter that is duplicated, oversized or invalid falls back to its
default and shows a short notice. Product links and the product page's "Back to
the collection" link carry only these parameters, never an external return URL.
The product page names the category embedded in the product response. It does not load the category list. A page past the end shows a
recovery state with a link to the last page. Share results copies the canonical
absolute URL, or reveals a selectable link when the clipboard is unavailable.
Offset pages are not a frozen snapshot: edits between requests can move products.

## UI components

Tailwind v4 and shadcn/ui provide shared actions, stock badges, loading skeletons,
search/stock/sort controls and mobile navigation. Lucide supplies the UI icons.
See [the design-system guide](design-system.md) for tokens, adding components,
server/client boundaries and the reset strategy. Product and hero images use the
licensed local photography described above.

## Demonstrate the shopping journey

Use the [hosted sandbox walkthrough and five-minute script](../docs/demo.md#try-the-hosted-sandbox-shop)
for a customer-facing demonstration. The [payment runbook](../docs/sandbox-payments.md)
owns setup, recovery and dated evidence; production payments remain disabled.

## Content security policy

VIN-126 promotes fresh request nonces to enforced CSP, with framing denial.
The root waits for request-time rendering; nonce-bearing HTML is private/no-store.
Production script policy excludes inline/eval exceptions; Zod uses its supported
CSP-compatible interpreter. The normal browser suite captures unexpected policy
violations, while controlled probes verify script rejection and framing behavior.
The guarded Next 16.3.8 render-policy transport patch addresses a hosted nonce
mismatch; it fails closed on unknown framework sources/versions.
See [policy exceptions, staging and rollback](../docs/security-headers.md).
[VIN-126](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/126)
records the actual merge, hosted verification and acceptance evidence.
