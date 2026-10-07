# API contract and interactive documentation

Opening the API domain root `/` redirects to `/docs` (Swagger UI), including
Vercel dashboard domain links. This is the API documentation entry point; the
storefront is a separate frontend domain. The redirect is not an OpenAPI operation.

FastAPI publishes an OpenAPI 3.1 contract for every implemented endpoint:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Machine-readable schema: http://localhost:8000/openapi.json

## Baseline response headers

The API and storefront explicitly send `X-Content-Type-Options: nosniff` and
`Referrer-Policy: strict-origin-when-cross-origin`. MIME types remain unchanged;
cross-origin HTTPS requests disclose the referring origin rather than its path
or query string. These headers cover API docs, redirects, handled errors and the
API's default unexpected-error response, plus storefront pages and static assets.
Unexpected API exceptions still propagate to the server and error monitoring.
Normal development delivery verifies these values on the API and storefront
smoke responses, including deliberate 401s. A protection bypass is sent only
when explicitly configured for a protected deployment; the current stable
development alias responds without it (see the environment runbook).
Next.js's automatic trailing-slash normalization runs before configured headers;
its empty same-origin 308 responses are excluded. Tests retain their canonical
URL and query behavior. Hosting-provider responses outside either application
(for example deployment-protection errors) are also outside this header policy.

[VIN-248](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/248)
records testing and hosted verification. This is a baseline slice of
[VIN-126](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/126).
The [CSP/framing/transport runbook](security-headers.md) records nonce-backed
policy enforcement, documentation exceptions and rollback. VIN-126 records
actual merge, hosted verification and acceptance evidence.

## Start and verify the local API

These URLs refer to **your computer**. GitHub displays the source and contract;
it does not run the API. The [hosted development API docs](https://vindor-api-development.vercel.app/docs) are also available.

Start Docker Desktop (or your Docker engine), then from the repository root:

```sh
make dev
make demo
curl --fail http://localhost:8000/health
curl --fail 'http://localhost:8000/api/v1/products/?skip=0&limit=10'
```

Expect `{"status":"ok"}` and a JSON product list. Demo seeding only populates an
empty catalog. The catalog request also checks database access; health alone is
process liveness. `make down` stops the services and preserves the database.

## Explore with Swagger

Open [Swagger UI](http://localhost:8000/docs). Expand a product GET operation,
choose **Try it out**, then **Execute** to inspect its URL, status and JSON body.
To explore customer authentication:

1. Execute `POST /api/v1/auth/register` with a unique demo email and a password
   of 8–128 characters. Use fictional data and a password you do not reuse.
2. Click **Authorize**. Enter that email in `username` and the password in
   `password`; leave client credentials empty. Swagger obtains a bearer token.
3. Execute `GET /api/v1/auth/me` to inspect the authenticated profile.
4. Choose an in-stock product ID from the catalog. Execute
   `PUT /api/v1/cart/items/{product_id}` with `{"quantity": 1}`.
5. Execute `GET /api/v1/cart/` to see the saved line, current GBP price, exact
   subtotal and availability. Repeat the PUT: the absolute quantity stays 1.
6. Execute `DELETE /api/v1/cart/items/{product_id}` to remove the line (204).
   GET the cart again to confirm it is empty.

Public signup creates a customer. Product writes require an active admin created
through the explicit CLI in [demo setup](demo.md); no public endpoint promotes
users. Do not share screenshots or exports containing passwords or bearer tokens.

## Import into Postman

Postman supports this OpenAPI 3.1 contract; see its
[official import guide](https://learning.postman.com/docs/integrations/available-integrations/working-with-openAPI/).

1. With the API running, select **Import** in Postman and enter
   `http://localhost:8000/openapi.json`. Alternatively, download the repository's
   [OpenAPI snapshot](../frontend/openapi.json) and import that file. It contains
   the same contract checked by CI and is available without a running API.
2. Generate a collection from the specification. Set its base URL variable to
   `http://localhost:8000` (the importer may call it `baseUrl`). Check that the
   resolved request URL begins with this address before sending.
3. Send the health and product-list requests first. Then register a fictional
   customer using the JSON request schema.
4. Send `POST /api/v1/auth/login` with **Body → x-www-form-urlencoded**:
   `username` is the registered email and `password` is its password. This
   endpoint accepts form fields, not a JSON login body.
5. Copy `access_token` from the response into a local, unshared Postman variable
   named `accessToken`. On the profile request, select **Authorization → Bearer
   Token** and use `{{accessToken}}`. Send `GET /api/v1/auth/me`; expect HTTP 200.

Use the Postman desktop application or its Desktop Agent for localhost requests;
a cloud agent cannot reach a server on your laptop. Keep token/password values
local and out of Git or shared collection exports. An expired token requires login
again. Swagger is an equivalent interactive client and needs no Postman account.

## Browser sessions and the direct API

The [customer account walkthrough](account-journey.md) uses the Next.js storefront.
Swagger and imported Postman requests call FastAPI directly. These are separate
clients; signing in through Swagger does not sign the storefront in.

| Client boundary | Sign-in request | Credential used for profile reads |
| --- | --- | --- |
| FastAPI / Swagger / Postman | `POST /api/v1/auth/login`, form-encoded `username` and `password` | `Authorization: Bearer <access_token>` on `/api/v1/auth/me` |
| Storefront browser | `POST /api/session/login`, JSON `email` and `password` | Browser-managed HttpOnly cookie on `/api/session/me`; no token returned in JSON |

The storefront also provides JSON registration at `/api/session/register` and
POST sign-out at `/api/session/logout`. State-changing session requests require
the exact configured Origin; cookie and no-store rules are documented in the
[session design](design/customer-sessions.md). The FastAPI OpenAPI snapshot covers
FastAPI endpoints; these Next.js session handlers are documented separately.

Storefront sign-out clears its browser cookie, not tokens held by Postman or
Swagger. Clearing Swagger authorization likewise removes that client's stored
credentials without server-side JWT revocation. Use fictional accounts and keep
bearer tokens out of shared exports. Expired or disabled-user tokens are rejected
by FastAPI. Password reset, email verification and global sign-out are not
implemented.

## Troubleshooting

| Symptom | Check / recovery |
| --- | --- |
| Connection refused / browser cannot connect | Start Docker, run `make dev`, and wait for success. |
| Docker daemon unavailable | Open Docker Desktop and wait for its engine to start; retry `make dev`. |
| Port already allocated | Check which local process owns port 8000 or 5432; do not stop unrelated services blindly. Compose supports `API_PORT` / `DB_PORT` overrides; update client URLs and the host database configuration accordingly. |
| API starts but catalog fails | Inspect service status and logs below; health does not verify the database. |
| Login returns 422 | Use form-encoded `username` and `password`, not JSON. |
| Profile returns 401 | Log in again and send the returned bearer token. |
| Product write returns 403 | A customer token cannot perform admin operations. |
| Auth or write returns 429 | Abusive rate tripped throttling; wait for `Retry-After` seconds, then retry. |

From the repository root:

```sh
docker compose --env-file backend/.env ps
docker compose --env-file backend/.env logs --tail=80 api migrate db
```

Do not delete database volumes to fix a startup error. Redact credentials and
personal data before sharing logs. Restart the stack after restarting your machine
if the services are no longer running.

## Catalog search and pagination (VIN-289)

`GET /api/v1/products/search` is a public, additive endpoint for querying the
complete catalog. Existing `GET /api/v1/products/` consumers still receive a list.
VIN-290 adds `category` to every product read: that list, each search item, and
`GET /api/v1/products/{id}`. The value is an object with `slug` and `name`.

Admin create requires `category`. Omitting it, or sending `all`, null, a
malformed slug, or an unknown slug, returns 422 and stores nothing. Admin update
may omit `category` and keep the current one. A stored slug moves the product.
Null, `all`, a malformed slug, or an unknown slug returns 422 and leaves the
product unchanged. Search returns 404 for an unknown slug; create and update
return 422 for the same slug.

| Parameter | Default | Accepted values |
| --- | --- | --- |
| `q` | No search | Product-name substring, at most 100 characters before trimming |
| `in_stock` | `false` | Boolean; `true` requires available stock greater than zero |
| `category` | Every category | One stored slug, such as `lighting`. Omit it for All. `all` is not a stored category |
| `sort` | `featured` | `featured`, `name`, `price-asc`, `price-desc` |
| `limit` | `24` | Integer from 1 to 100 |
| `skip` | `0` | Integer from 0 to 100000 |

```sh
curl --fail 'http://localhost:8000/api/v1/products/search?q=desk&in_stock=true&sort=price-asc&limit=24&skip=0'
```

The response contains `items`, the matching `total`, and the applied `limit` and
`skip`. Search, stock selection and ordering apply before pagination. A page
beyond the final result has empty `items` while retaining the matching total.
Invalid bounds, unknown sorts, overlong searches, NUL characters and invalid
booleans return 422. An unknown `category` slug returns 404. A malformed slug,
including an empty value, returns 422. All is the omitted parameter, not the
slug `all`.
An empty or whitespace-only search applies no name filter. Percent, underscore
and backslash are literal search characters, rather than SQL wildcards.

PostgreSQL performs case-insensitive matching using its database locale; name
ordering uses `lower(name)` and the database collation. SQLite's local test
fixtures fold ASCII case only. Featured order is ascending product ID, preserving
the existing catalog sequence; it does not imply merchandising scores. Every
sort ends with ascending product ID to make ties deterministic. Prices remain
exact, two-place GBP strings; reserved inventory is not exposed.

The page and count share a single database snapshot. With unchanged data, repeated
pages retain their order. Inserts, deletes, stock changes or edits between requests
can move results and change totals; offset pagination is not a frozen browsing
session. VIN-289 search adds no index or migration. Categories use Alembic
revision 0008.

The storefront home page is the collection. It calls this endpoint on the server
for every page (24 products per page) using the URL-owned selection described in
the [frontend README](../frontend/README.md#collection-urls-vin-287); the browser
no longer filters a preloaded list. FastAPI and PostgreSQL stay authoritative for
matching, ordering, totals, prices and stock.

`GET /api/v1/categories/` lists the public categories in display order (VIN-290).
Each count uses the same `q` and `in_stock` filters as the catalog and is not
limited to one category. Uncategorized is the stored fallback for products the
migration could not match. That same home page loads this list for category
navigation and breadcrumbs, and passes the selected slug to search. The product
page does not call this list. It loads `GET /api/v1/products/{id}` and shows the
embedded `product.category`. The photograph comes from `product.image`, an
allowlisted local key and plain-text alternative text. The product page does not
derive the file from the product name, so a rename keeps the photograph. Absent
`material`, `width_mm`, `depth_mm` and `height_mm` values are omitted on the page.
Create and update reject remote URLs, unknown keys and markup with 422. A customer
cannot change them.

## Other response contracts

The schema documents request/response models, bearer security requirements,
pagination bounds, and 400/401/403/404/409 errors where applicable. FastAPI documents
422 validation errors. Products return prices as exact two-place GBP strings.
PUT keeps omitted fields. Description, image, material and dimensions may be null
to clear them; name, price, currency, stock and category may not. Health is liveness,
not database readiness.

Cart GET/PUT/DELETE operations require an active customer's bearer token. Cart PUT
sets an integer quantity from 1 to 99; new lines and increases beyond current stock
return 409. Reductions and removal remain allowed during shortages. Cart totals
use current backend prices, and adding a line does not reserve stock. Deleted
products are removed from saved carts. See [the cart contract](design/cart-api.md)
for persistence and concurrency semantics. The signed-in cart storefront is
implemented; order placement is implemented as documented below. Sandbox payment endpoints are implemented; see the
[payment lifecycle and contract](sandbox-payments.md). Production payments remain disabled.

## Abuse protection (rate limits)

The public demo throttles in application code so registration spam, credential
stuffing, and write floods are rejected with `429 Too Many Requests` while
normal use is unaffected. No paid WAF or extra service is involved.

| Scope | Limit (60-second fixed window) |
| --- | --- |
| `POST /api/v1/auth/register` | 60 requests per anonymous identity |
| `POST /api/v1/auth/login` | 60 requests per anonymous identity |
| Cart writes (`PUT`/`DELETE /api/v1/cart/items/{id}`) and product writes, order drafts (`POST /api/v1/orders/drafts`) and placement (`POST /api/v1/orders/{order_id}/place`) | 300 requests shared per verified active customer |

A 429 body is the standard `{"detail": ...}` error shape with no client data,
plus `Retry-After` (seconds until the window resets), `X-RateLimit-Limit`, and
`X-RateLimit-Remaining: 0` headers. Throttling also applies to failed attempts
(wrong passwords, duplicate registrations), which is what makes stuffing
expensive. Public catalog reads are intentionally unthrottled so legitimate
visitors are never harmed.

Authenticated write budgets use the active user returned by the existing JWT and
database authentication dependency. Different customers behind the same frontend
egress have separate budgets; changing forwarded headers or renewing a token does
not create a new budget for the same user. Cart, order draft/placement and authorized admin product writes
share that user's budget. Missing/invalid/disabled identities return 401 before
consuming it; non-admin product requests retain 403. This is throttling after
authentication, not protection against the cost of authentication itself.

Counters remain process-local and ephemeral. Restarts, multiple instances and
bounded-table eviction can reset or split allowances; this is not distributed
abuse protection. Anonymous login/registration use a verified short-lived storefront context when
configured, otherwise the platform-provided IP on Vercel or the peer locally.
Local caller-supplied forwarded headers are ignored. The default registration and
login limits remain 60 per minute; validated positive environment settings
control them independently of disposable browser fixture thresholds (10,000).

The frontend signs only login/register requests, only in Vercel runtime, using a
dedicated `RATE_LIMIT_PROXY_SECRET` shared with its paired API. The opaque bucket
is an HMAC of the platform IP; the assertion binds its timestamp, bucket, method
and exact API path. Backend accepts a maximum age of 60 seconds and up to five
seconds of forward clock skew. Malformed, expired, wrong-route or forged claims
receive ordinary direct-ingress limiting, never an exemption. A new timestamp
does not create a fresh bucket. Requests sharing a real public NAT IP still share
an anonymous allowance; a captured valid assertion can be replayed during its
short validity window against that same bucket. Per-instance resets still apply.

Configure the same dedicated random key (at least 32 characters) on each paired
frontend/API environment. Never reuse JWT or deployment-bypass credentials. The
key is server-only; the assertion header is scrubbed by the backend's existing
telemetry filter. VIN-121's wider privacy gates still precede telemetry activation.
Missing frontend configuration omits the assertion; missing backend configuration
ignores it. Limiting continues, but shared frontend egress can still group visitors.
Do not claim hosted visitor isolation until paired configuration and actual
platform topology have been verified. See [Vercel request headers](https://vercel.com/docs/headers/request-headers).

## Contract workflow

The backend owns the contract. From backend/, run:

```sh
uv run python -m scripts.export_openapi
```

Then from frontend/:

```sh
npm run api:generate
```

The exporter uses inert local configuration and does not connect to a database.
It writes a deterministic frontend/openapi.json snapshot; openapi-typescript
produces src/lib/api/schema.d.ts. The Next.js server uses openapi-fetch with these
types. CI regenerates both files and rejects uncommitted drift. Generated types
provide compile-time checking; they are not runtime payload validation.

When changing an endpoint, update its models, summary/description, security and
error responses, add behavior tests, then regenerate the contract. The exported
schema includes only implemented routes; planned features belong in the roadmap.

## Order drafts (VIN-118)

Authenticated `POST /api/v1/orders/drafts` accepts `lines` containing distinct
`product_id` and `quantity` values (1–100 lines, quantity 1–99). The API copies
current catalog names/prices and calculates exact GBP totals. Extra fields such
as owner, status or money are rejected. A missing product returns 404 without
creating a partial draft. Stock and carts are unchanged, including for shortages.

`GET /api/v1/orders/` lists only the caller's orders, ascending by ID, with
`limit` (1–100, default 20) and `after_id` (default 0). `GET /api/v1/orders/{id}`
returns an owned snapshot or 404. Successful responses are private/no-store;
missing/disabled authentication returns 401. Draft creation shares the existing
per-customer write budget and can return 429 with Retry-After.

Draft creation is not idempotent and never places an order or charges money.
There is no draft update endpoint. Product changes/deletion do not alter saved
snapshots. Placement is a separate operation described below.

## Order placement (VIN-119)

Authenticated `POST /api/v1/orders/{order_id}/place` requires an `Idempotency-Key`
header (1–128 ASCII letters, digits, underscores or hyphens). It returns 200 with
the owned placed order. Retrying the same draft and key returns the original result;
reusing a key for another draft or a new key for an already placed order returns 409.

The service revalidates current prices, stock and exact purchased cart quantities
in one transaction. Conflicts return 409 without changing inventory or the cart;
price/cart changes require a fresh draft and deliberate customer confirmation.
Successful placement decrements inventory and removes purchased cart lines while
preserving unrelated items. Missing or foreign orders return 404; missing/disabled
sessions return 401, malformed headers return 422, and write limits can return 429.
`placed` means inventory claimed, not paid. The optional VIN-30 sandbox lifecycle adds
`payment_status` and `payment_expires_at`; historical orders retain null payment state.
Owned POST operations `/api/v1/orders/{id}/payment`, `/cancel` and `/reconcile`
create/reuse Checkout, cancel safely and reconcile respectively. Signed provider
events use `/api/v1/payments/webhook`. Only verified success webhooks establish
`paid`. See [sandbox configuration and recovery](sandbox-payments.md); hosted
verification status remains in the canonical plan.
