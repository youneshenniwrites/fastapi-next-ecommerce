# Contributing

Start with the [README](README.md) and [roadmap](docs/plans/roadmap.md). The working
product is the backend; the frontend is a skeleton. Keep proposed features scoped
to the next usable behavior and separate tooling/documentation changes when useful.

## Local workflow

1. Create a task branch from current main. Inspect open PRs for overlapping changes.
2. Run `make setup`; use `make dev` when a live backend is needed.
3. Reproduce bugs before fixing them and add a behavior-level regression test.
4. Run `make check`. Use `make coverage`, `make audit`, and
   `make requirements-check` for relevant dependency or tooling changes.
5. Review the complete diff and open a focused PR with validation evidence.

`make hooks` installs optional local checks. CI still runs even when hooks are not
installed. Use separate Compose project names, ports, and databases for concurrent
worktrees. Never point test database overrides at customer data.

## Change contracts

- **Database:** add a new Alembic revision; do not edit an applied revision. Test
  empty-database upgrade, metadata consistency, and any affected existing data.
- **API:** document request/response changes, permissions, and error behavior.
  Product price is a decimal string in GBP; avoid introducing float arithmetic.
- **Dependencies:** edit pyproject.toml, regenerate uv.lock, and export requirements.txt.
  Run the audit and requirements check. Review upstream release notes for compatibility.
- **Frontend:** follow frontend/AGENTS.md. Add actual build/type/browser checks when
  the runnable app is introduced; a directory skeleton cannot pass a frontend build.
- **Docs/skills:** describe implemented behavior accurately. Validate links and skill
  frontmatter. Do not turn future plans into claims of production readiness.

See [tooling](docs/tooling.md) for exact checks and [development](docs/development.md)
for database and configuration details. Coding agents should also read [AGENTS.md](AGENTS.md).

## PR ownership

Repository ownership is recorded in .github/CODEOWNERS. Assign maintenance PRs to
@youneshenniwrites and apply relevant scope labels. Agents use the
ecommerce-pr-ownership skill and its checked helper after PR creation. Authorship
is the actual GitHub account that opens the PR; do not forge a different author.

## Review and merge

Explain the problem and resulting behavior, then give the commands/results and
material limitations. Include relevant screenshots for UI changes, or API/test
output for backend changes. Do not include tokens, passwords, or customer data.

Review the exact pushed revision. Address actionable findings and rerun affected
checks. A self-review must say it is a self-review; it is not independent approval.
All applicable CI jobs must pass before merge. No workflow in this repository
bypasses review to automatically merge dependency updates.

Merge permission does not authorize Azure provisioning. Cloud deployments need
an agreed environment, budget, secrets/identity design, and rollback plan.
Report vulnerabilities privately through [SECURITY.md](SECURITY.md).
