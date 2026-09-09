# VINDOR storefront

A fictional desk-accessories catalog for the senior SWE portfolio. Next.js App
Router and React render catalog and detail pages against FastAPI; search, stock
filtering and price/name sorting work in the browser. Prices remain decimal strings
and are formatted/sorted with integer pennies, without floating-point money math.

## Run locally

Install Node 24.20.0 (or use nvm install from this directory) and npm 11.19.1.
From the root, run make dev and make demo. Then from frontend/:

```sh
npm ci
npm run dev
```

Open http://127.0.0.1:3000. The server defaults to http://127.0.0.1:8000 for FastAPI.
To change it, set API_BASE_URL in an ignored .env.local; see .env.example. No CORS
configuration is necessary: only the Next.js server calls FastAPI. Fetches are
uncached and have a five-second timeout. Failed requests show a retryable state.

## Verification

| Command              | Check                                                             |
| -------------------- | ----------------------------------------------------------------- |
| npm run lint         | ESLint, TypeScript lint rules, React hooks and Next.js rules      |
| npm run format:check | Prettier formatting                                               |
| npm run typecheck    | TypeScript and generated route types                              |
| npm test             | Catalog/money unit tests with enforced coverage                   |
| npm run build        | Production Next.js standalone build                               |
| npm run test:e2e     | Desktop/mobile real-API browsing, axe accessibility, fault states |
| npm audit            | Locked dependency vulnerability audit                             |
| npm run api:check    | Generated schema/type drift against Git                           |

Before browser tests, run make setup at the root, npm run build here, and
npx playwright install chromium (add --with-deps on Linux). Tests use ports
18300/18301 and 3300/3301, migrate a temporary SQLite database, and seed it. The
backend CI suite separately verifies PostgreSQL. Browser traces on failure and
HTML reports are retained in GitHub artifacts for 14 days.

Regenerate the API contract from backend/ with uv run python -m scripts.export_openapi,
then npm run api:generate here. No running database is needed. Commit openapi.json
and src/lib/api/schema.d.ts together. Runtime calls use openapi-fetch and generated types.

## Scope and design

VINDOR uses locally stored, licensed WebP photography, system fonts and Lucide icons.
See [photo credits](PHOTO_CREDITS.md) for sources and licences. Photographs are
representative, not exact product specifications or brand endorsements. Unknown
products use a neutral Lucide placeholder.

The catalog currently loads at most 100 products and filters those loaded items;
a notice appears at that limit. Server-side search/pagination is a future increment
before a larger catalog. Registration and login screens are implemented; there are no carts, payments or purchase
controls yet. Automated accessibility checks supplement manual keyboard/mobile
review; they do not constitute a full accessibility certification.

ESLint 10 uses the official Next plugin directly with typescript-eslint and React
hooks rules. This avoids incompatible legacy plugins in eslint-config-next.
npm run build assembles .next/standalone with static assets. Run npm start with
PORT and HOSTNAME environment variables to serve that package. CI archives the
contents; after extraction use node server.js with API_BASE_URL configured.

The [development demo](https://forme-ecommerce-development.vercel.app) runs on Vercel; production CD runs through GitHub Actions. See ../docs/ci.md for the delivery pipeline.

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
and broader journey verification remain #26–27.

## UI components

Tailwind v4 and shadcn/ui provide shared actions, stock badges, loading skeletons,
search/stock/sort controls and mobile navigation. Lucide supplies the UI icons.
See [the design-system guide](design-system.md) for tokens, adding components,
server/client boundaries and the reset strategy. Product and hero images use the
licensed local photography described above.
