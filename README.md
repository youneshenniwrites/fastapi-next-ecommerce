# FastAPI + Next.js ecommerce

[Delivery board](https://github.com/users/youneshenniwrites/projects/1) · [Engineering Wiki](https://github.com/youneshenniwrites/fastapi-next-ecommerce/wiki) · [Delivery workflow](docs/delivery.md)


[![Backend CI](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/workflows/ci.yml/badge.svg)](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/workflows/ci.yml)
[![Dependency audit](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/workflows/dependency-audit.yml/badge.svg)](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/workflows/dependency-audit.yml)

A storefront project built around a FastAPI API and PostgreSQL, with a
Next.js frontend. **The launch currency is GBP and the chosen cloud is Azure.**
The backend and catalog storefront run locally; checkout is still planned.

[Quick start](#quick-start) · [API](#api-overview) · [Checks](#testing-and-quality) ·
[Architecture](docs/architecture.md) · [Roadmap](docs/plans/roadmap.md) ·
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

## What works today

| Area | Status |
| --- | --- |
| Accounts | Registration, password login, bearer-token profile, disabled-user rejection |
| Product catalog | Public reads; creation, partial updates, deletion restricted to active admins |
| Money and validation | Fixed-precision GBP prices, database constraints, bounded pagination |
| Persistence | PostgreSQL, Alembic migrations, legacy-data validation |
| Development | Generated local credentials, Docker Compose, locked Python dependencies |
| Verification | SQLite/PostgreSQL tests, container smoke tests, coverage gate, dependency audits |
| Agent workflows | Root/backend/frontend instructions and scoped repository skills |
| Frontend | Responsive Next.js catalog/detail pages, filters, generated API types and browser checks |
| Shopping | Cart, orders, payment processing, and order history are planned |
| Hosting | Azure is planned; no Azure deployment is provisioned |

This repository is a development foundation, not a production-ready shop. Tests
cover implemented behavior; placeholder files do not represent finished features.

## Quick start

Prerequisites: Git, Python 3.12, uv, and a running Docker installation with Compose.
No cloud account is needed for local development.

```sh
git clone https://github.com/youneshenniwrites/fastapi-next-ecommerce.git
cd fastapi-next-ecommerce
make dev
```

`make dev` generates `backend/.env` if missing, preserves existing credentials,
installs the locked Python environment, builds the API image, starts PostgreSQL,
applies migrations, and waits for the API health check. Credentials are local-only
and excluded from Git and the Docker build context.

**These links open services on your own computer, not a hosted GitHub demo.**
Wait for `make dev` to succeed before opening them. If Docker or the API is stopped,
the links will be unavailable.

- API documentation: [localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [localhost:8000/redoc](http://localhost:8000/redoc)
- OpenAPI contract: [localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- Health: [localhost:8000/health](http://localhost:8000/health)

For a first API request, authentication, and Postman import, follow the
[API onboarding guide](docs/api.md). The [checked-in OpenAPI contract](frontend/openapi.json)
can be downloaded even while the API is offline; executing requests requires the stack.

For the storefront, run `make demo`, then `cd frontend && npm ci && npm run dev`
with Node 24.20.0 and npm 11.19.1. Open [127.0.0.1:3000](http://127.0.0.1:3000).
See [frontend setup](frontend/README.md). Re-run `make dev` after changing containerized code.

```sh
make down  # stops the stack and preserves PostgreSQL data
```

## Development commands

Run these from the repository root after `make setup`:

| Command | What it does |
| --- | --- |
| `make setup` | Generate local configuration and install dependencies from uv.lock |
| `make dev` | Build/start the PostgreSQL, migration, and API containers |
| `make down` | Stop containers without deleting the database volume |
| `make check` | Ruff lint, format check, and isolated backend tests |
| `make coverage` | Run tests with branch-aware coverage and an 85% minimum |
| `make audit` | Audit the locked Python environment for known vulnerabilities |
| `make requirements-check` | Verify the pip export matches uv.lock |
| `make hooks` | Install optional pre-commit checks |
| `make hooks-check` | Run those checks over tracked files |
| `make migrate` | Apply migrations through the host DATABASE_URL |

For a host API with reload, start only the database, apply migrations, and run uvicorn:

```sh
make setup
docker compose --env-file backend/.env up -d --wait db
make migrate
cd backend
uv run uvicorn app.main:app --reload
```

Stop the containerized API first if it already occupies port 8000. See the
[development guide](docs/development.md) for configuration, port isolation,
logging, and troubleshooting.

## Architecture

The working request path is:

```text
HTTP client → FastAPI routes/dependencies → CRUD helpers → SQLAlchemy → PostgreSQL
                       │
                       └─ Pydantic validation, JWT checks, admin permissions
```

The Next.js App Router frontend consumes generated types from FastAPI's OpenAPI contract.
FastAPI remains authoritative for permissions, product prices, inventory, and
future order totals. Domain services will own checkout transactions when that flow
is implemented; payment/email files currently contain placeholders.

The local stack starts PostgreSQL, runs a one-shot Alembic migration container,
then starts the non-root API container. Database and API host ports bind to loopback.
See [architecture](docs/architecture.md) for the current design and Azure direction.

## API overview

See [OpenAPI contract and Swagger workflow](docs/api.md) for interactive documentation
and generated frontend types.

All resource routes use `/api/v1`. Authentication uses an OAuth2-style password
form and bearer access tokens. Registration never grants admin privileges.

| Method | Path | Access |
| --- | --- | --- |
| GET | `/health` | Public process-liveness check |
| POST | `/api/v1/auth/register` | Public; returns 201 |
| POST | `/api/v1/auth/login` | Public form fields `username` (email), `password` |
| GET | `/api/v1/auth/me` | Active authenticated user |
| GET | `/api/v1/products/` | Public; `skip` and `limit` pagination |
| GET | `/api/v1/products/{id}` | Public |
| POST | `/api/v1/products/` | Active admin |
| PUT | `/api/v1/products/{id}` | Active admin; partial update semantics |
| DELETE | `/api/v1/products/{id}` | Active admin; returns 204 |

Product JSON includes an exact decimal string and explicit currency:

```json
{
  "id": 1,
  "name": "Tea",
  "description": "Box of tea",
  "price": "19.90",
  "currency": "GBP",
  "stock": 12
}
```

Prices have at most two decimal places and range from 0.00 to 9999999999.99.
Stock must be a nonnegative integer. Lists use a stable id order, a limit of 1–100
(default 10), and skip of 0–100000. Omitted PUT fields retain their values; only
description may explicitly be null. Unsupported currencies and unknown fields
are rejected. See [backend documentation](backend/README.md) for full constraints.

Run `make demo` to populate an empty catalog, then `make admin EMAIL=admin@example.com`
to create an admin with a hidden password prompt. See the [demo guide](docs/demo.md)
for rerun and promotion behavior. There is no default admin password or public promotion route.

## Database migrations

Alembic owns schema changes. Applied revisions are immutable; changes use a new
revision. Migration 0001 creates users/products. Migration 0002 stores GBP prices
as NUMERIC(12, 2), adds validation constraints, and checks legacy records first.
It refuses values that require rounding or correction.

Existing unversioned databases need a backup and schema comparison before baseline
adoption. Do not stamp or delete existing data to bypass migration failures.
Downgrades are tested against disposable databases; they are not a production
rollback plan. See [development guide](docs/development.md#database-work).

## Testing and quality

Backend CI runs three jobs, with dependency auditing in a separate workflow:

- **backend:** locked installation, Ruff, requirements consistency, tests, and coverage.
- **postgres:** the full test suite against separate disposable PostgreSQL databases.
- **container:** image build, startup, authentication smoke flow, migration checks and rollback.
- **dependency-audit:** known-vulnerability checks, also run weekly and on demand.

Frontend CI also checks formatting, lint, types, API contract drift, unit coverage,
a production build, and desktop/mobile browser and accessibility behavior. It
archives browser evidence and the validated standalone build.
See [CI and deployment status](docs/ci.md) for the full pipeline.

Coverage and audit artifacts remain available for 14 days. Dependabot proposes
weekly Python, CI action, and Docker updates; updates still need review and checks.
CI actions are pinned to commit SHAs. [Tooling details](docs/tooling.md) explain
coverage scope, local hooks, and how to handle dependency-update failures.

Static type checking, code scanning, and repository-level required-check rules are
future tooling increments. We do not claim those controls are enabled today.

## Working with coding agents

Start with [AGENTS.md](AGENTS.md). It records commands, review expectations, and
product invariants. Backend and frontend folders have additional instructions.
Shared skills cover isolated tasks, backend changes, evidence, Azure planning, and
maintenance, and PR ownership. The frontend has its own scoped development skill.

Every change should have a focused PR, review findings, and evidence for the exact
commit being merged. Self-review must be labelled as such. See
[contributing](CONTRIBUTING.md) and [skill provenance](docs/skill-sources.md).

## Azure roadmap

The proposed target is Azure Container Apps for FastAPI and the future Next.js
server, with Azure Database for PostgreSQL Flexible Server. The infrastructure PR
will define region, costs, identities/secrets, registry, networking, logs,
backup/restore, and rollback before provisioning. The old AWS Terraform in
`backend/infra` is legacy reference, not the deployment path.

This is a [senior SWE portfolio project](docs/plans/portfolio.md).
The next product steps are customer
account screens, carts, orders, and sandbox payments. Follow the
[ordered roadmap](docs/plans/roadmap.md) for the remaining work.

## Repository map

```text
backend/app/          API, models, schemas, CRUD helpers, tests
backend/alembic/      Versioned database migrations
backend/scripts/      Local setup, smoke tests, requirements check
frontend/             Next.js storefront, generated API types and browser tests
.agents/skills/       Shared agent workflows
.github/              CI, dependency updates, contribution templates
compose.yaml          Local PostgreSQL/migration/API stack
docs/                 Architecture, development, tooling, decisions, roadmap
```

Report security issues privately using the route in [SECURITY.md](SECURITY.md).

## Delivery commands

The [delivery skills reference](docs/delivery-skills.md) explains the five reusable
Codex workflows for PR creation, self-review, review comments, board updates and
documentation, including invocation examples and discovery.
