---
name: ecommerce-feature
description: Prepare an isolated feature or fix in this ecommerce repository, accounting for worktrees, local ports, and PostgreSQL state.
---

Use ecommerce-naming before creating a branch or naming a PR.

Inspect the working tree and open PR scope. Use the current task's branch/worktree
when already isolated; create a fresh one from the intended base if needed. Preserve
uncommitted user work. Resolve routine non-overlapping changes without blocking.

Run `make setup`. For concurrent stacks, assign a unique `COMPOSE_PROJECT_NAME`,
`API_PORT`, and `DB_PORT`; set the host DATABASE_URL port consistently when running
migrations outside Docker. Separate worktrees still share host ports.

Choose one acceptance criterion from docs/plans/roadmap.md. Identify required
migrations and API contract changes before editing. Keep the PR reviewable and
follow the root AGENTS.md delivery checks. This skill does not authorize deployment.
