# Working in this repository

The product has a FastAPI backend and a runnable Next.js catalog storefront.
Server-mediated customer sessions are implemented; account UI and checkout are planned. Read
docs/plans/portfolio.md, docs/architecture.md, and docs/plans/roadmap.md before choosing work; update their
factual status when a feature lands.

## Commands

- `make setup`: preserve or create local credentials and install locked dependencies.
- `make dev`: build and start PostgreSQL, run migrations, and start the API.
- `make check`: lint, format check, and isolated backend tests.
- `make down`: stop the local stack while preserving its database volume.
- `make migrate`: apply migrations to the configured local database.
- `make coverage`: test with branch-aware coverage and the 85% minimum.
- `make audit`: check installed locked dependencies for known vulnerabilities.
- `make requirements-check`: verify the pip export agrees with uv.lock.
- `make hooks-check`: run optional pre-commit checks over tracked files.

Use Python 3.12 and uv. Change pyproject.toml, regenerate uv.lock and the
requirements.txt export together. Never hand-merge lockfiles. Docker and uv are
prerequisites. Do not claim checks passed if a missing prerequisite prevented them.

## Delivery

Use the ecommerce-naming skill for branch names, commits, PR titles, and squash
subjects. Follow CONTRIBUTING.md: type/short-kebab-description branches, never
agent/, and Conventional Commits subjects. Use a task branch. Respect an existing agent-managed worktree; otherwise use a
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
Vercel Hobby, Render Free and Neon Free are the approved demo hosts. Azure is
optional future work; read deploy/environments/README.md. No paid upgrades. The AWS Terraform in backend/infra is legacy
reference and is not an approved deployment path.

Project skills in .agents/skills cover feature isolation, backend changes,
verification, Azure planning, maintenance, and PR ownership. Frontend-specific
guidance lives under frontend/.agents/skills and frontend/AGENTS.md. User
instructions take precedence over skill guidelines. Use only skills relevant to
the task. Codex external review is required before merge; no public evidence host is required. Attach
redacted logs/screenshots only within the authorized workflow.

See CONTRIBUTING.md for PR expectations, docs/tooling.md for check scope, and
SECURITY.md for private vulnerability reporting.

For every PR created in this repository, use the ecommerce-pr-ownership skill to
assign youneshenniwrites and apply relevant labels. Verify the authenticated author
before creation and read back metadata afterward. Preserve real bot/contributor
authorship when maintaining their PRs.

## Delivery tracking

Follow docs/delivery.md before implementation and at handoff. Use repository issues
and the linked board for current work, the repository for versioned rules, and the
Wiki for explanations. Every implementation PR needs an issue reference; use
Closes #N only for a completed ticket. Update board status and verify acceptance,
CI, PR disposition and relevant documentation before reporting completion.
For customer sessions (#24), read docs/design/customer-sessions.md; it documents the implemented handlers and remaining account UI work.

## External review requirement

The owner accepts a completed clean Codex review of the latest commit, with all
findings addressed and threads resolved, as external approval. Explicit owner-approved deferrals
are permitted only when recorded with a linked issue; do not call them clean reviews. Follow
[the review gate protocol](docs/codex-review.md); treat the `Codex review` status as informational until #38 is resolved,
require all applicable CI, and independently verify ticket acceptance criteria.
Self-review is disclosed and cannot replace external review. Request a new review
after changes. No human reviewer is required. Never bypass protection or invent a
clean result. Missing, stale or unrecognized evidence keeps the PR open.

The canonical PR format is .github/pull_request_template.md. Use the
ecommerce-pr-ownership skill to fill it, assign the owner, and request/verify
Codex review. Keep the owner as assignee, not a requested reviewer. Read these repository files each time
you resume PR work; conversation memory is not the source of truth.

## Invokable delivery skills

Use create-pr for PR creation or description refresh, self-review for a complete
implementation review, address-codex-comments for review follow-up,
update-delivery-board for issue/project reconciliation, and update-docs for
README, Wiki and contract documentation. Read the selected SKILL.md under
.agents/skills before using it. These reuse the policies above; they do not
replace external review or expand authorization. See docs/delivery-skills.md
for invocation and discovery, including tasks started outside the repository.
