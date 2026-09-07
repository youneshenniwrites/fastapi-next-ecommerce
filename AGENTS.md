# Working in this repository

The current product is a FastAPI backend. The frontend/ directory is a Next.js
skeleton; the runnable storefront and checkout flow are still planned. Read
docs/architecture.md and docs/plans/roadmap.md before choosing work; update their
factual status when a feature lands.

## Commands

- `make setup`: preserve or create local credentials and install locked dependencies.
- `make dev`: build and start PostgreSQL, run migrations, and start the API.
- `make check`: lint, format check, and isolated backend tests.
- `make down`: stop the local stack while preserving its database volume.
- `make migrate`: apply migrations to the configured local database.

Use Python 3.12 and uv. Change pyproject.toml, regenerate uv.lock and the
requirements.txt export together. Never hand-merge lockfiles. Docker and uv are
prerequisites. Do not claim checks passed if a missing prerequisite prevented them.

## Delivery

Use a task branch. Respect an existing agent-managed worktree; otherwise use a
separate worktree when concurrent changes require isolation. Inspect git status
and overlapping PRs before editing. Allocate separate ports, Compose project names,
and databases for concurrent runs; worktrees do not isolate running services.

For fixes, reproduce the behavior and add a regression check. Review the complete
diff after implementation. Record findings and test evidence in the PR, explicitly
identifying self-review when the same agent implemented the change. Follow the
user's authorization for pushing and merging; do not infer deployment permission
from merge permission. Merge only the reviewed commit after required CI succeeds.
Do not weaken or bypass checks to complete a task.

## Product rules

FastAPI owns permissions, product prices, stock, and future order totals. Browser
inputs cannot establish admin privileges or authoritative payment state. Schema
changes include reviewed Alembic migrations. Tests must use disposable databases.
Do not run downgrade, volume deletion, or seed experiments against customer data.
Azure is the chosen cloud provider. The AWS Terraform in backend/infra is legacy
reference and is not an approved deployment path.

Project skills in .agents/skills cover feature isolation, backend changes, and
verification, and Azure planning. Frontend-specific guidance lives under
frontend/.agents/skills and frontend/AGENTS.md. User instructions take precedence
over skill guidelines. Use only skills relevant to the task. No external reviewer service or public evidence host
is required; attach redacted logs/screenshots only within the authorized workflow.
