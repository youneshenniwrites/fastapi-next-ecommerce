# API contract and interactive documentation

FastAPI publishes an OpenAPI 3.1 contract for every implemented endpoint:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Machine-readable schema: http://localhost:8000/openapi.json

Run make dev at the root first. Swagger's Authorize uses the password flow: enter
the account email in username and its password. Public signup creates a customer;
use the explicit admin CLI from [demo setup](demo.md) for product writes. No public
endpoint promotes users. Do not share screenshots containing bearer tokens.

The schema documents request/response models, bearer security requirements,
pagination bounds, and 400/401/403/404 errors where applicable. FastAPI documents
422 validation errors. Products return prices as exact two-place GBP strings;
PUT keeps omitted fields and allows null only for description. Health is liveness,
not database readiness. No cart, checkout or payment endpoints are claimed yet.

## Contract workflow

The backend owns the contract. From backend/, run:

```sh
uv run python -m scripts.export_openapi
```

The exporter uses inert local configuration and does not connect to a database.
It writes a deterministic frontend/openapi.json snapshot. The next frontend PR
will generate TypeScript types from this snapshot and check contract drift in CI.

When changing an endpoint, update its models, summary/description, security and
error responses, add behavior tests, then regenerate the contract. The exported
schema includes only implemented routes; planned features belong in the roadmap.
