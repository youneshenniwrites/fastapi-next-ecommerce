# FastAPI + Next.js ecommerce

An ecommerce application under development. The backend currently supports
registration, login, profiles, and public product reads with admin-only writes.
Next.js, carts, orders, and payments are planned; they are not available yet.

## Local development

Install Docker with Compose, Python 3.12, and uv. From the repository root:

```sh
make dev
```

This generates backend/.env with random local credentials if it does not exist,
installs locked dependencies, builds the backend, starts PostgreSQL, applies
migrations, and starts the API. No AWS account or manual configuration is required.

API documentation: http://localhost:8000/docs
Health check: http://localhost:8000/health

```sh
make check  # lint, formatting, isolated tests; Docker not required
make down   # stop containers, preserve the database volume
```

If ports 8000 or 5432 are occupied, set API_PORT and DB_PORT for Compose. Match
the port in DATABASE_URL when using host-side database commands. Independent
worktrees should also set a unique COMPOSE_PROJECT_NAME.

To update code in the running container, rerun make dev. Container startup is
intended for local development, not a production deployment configuration.

## Repository map

- backend/app: API, database models, and tests
- backend/alembic: database migrations
- compose.yaml: local PostgreSQL, migration job, and API
- .github/workflows/ci.yml: backend checks and PostgreSQL/container smoke tests
- .agents/skills and AGENTS.md: coding-agent workflows and verification commands
- docs/plans/roadmap.md: ordered remaining work
- backend/infra: incomplete AWS Terraform, not deployed by this workflow

See backend/README.md for API and database details, docs/architecture.md for the
current design, and docs/skill-sources.md for the agent workflow's provenance.
