# API contract and interactive documentation

Opening the API domain root `/` redirects to `/docs` (Swagger UI), including
Vercel dashboard domain links. This is the API documentation entry point; the
storefront is a separate frontend domain. The redirect is not an OpenAPI operation.

FastAPI publishes an OpenAPI 3.1 contract for every implemented endpoint:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Machine-readable schema: http://localhost:8000/openapi.json

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

From the repository root:

```sh
docker compose --env-file backend/.env ps
docker compose --env-file backend/.env logs --tail=80 api migrate db
```

Do not delete database volumes to fix a startup error. Redact credentials and
personal data before sharing logs. Restart the stack after restarting your machine
if the services are no longer running.

The schema documents request/response models, bearer security requirements,
pagination bounds, and 400/401/403/404/409 errors where applicable. FastAPI documents
422 validation errors. Products return prices as exact two-place GBP strings;
PUT keeps omitted fields and allows null only for description. Health is liveness,
not database readiness.

Cart GET/PUT/DELETE operations require an active customer's bearer token. Cart PUT
sets an integer quantity from 1 to 99; new lines and increases beyond current stock
return 409. Reductions and removal remain allowed during shortages. Cart totals
use current backend prices, and adding a line does not reserve stock. Deleted
products are removed from saved carts. See [the cart contract](design/cart-api.md)
for persistence and concurrency semantics. The signed-in cart storefront is
implemented; checkout and payment endpoints remain planned.

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
