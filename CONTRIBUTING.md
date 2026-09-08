# Contributing

Start with the [README](README.md) and [roadmap](docs/plans/roadmap.md). The working
product is the backend; the catalog frontend is runnable. Keep proposed features scoped
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
- **Frontend:** follow frontend/AGENTS.md. Run lint, formatting, type, unit, build
  and browser checks. Regenerate API types when the backend contract changes.
- **Docs/skills:** describe implemented behavior accurately. Validate links and skill
  frontmatter. Do not turn future plans into claims of production readiness.

See [tooling](docs/tooling.md) for exact checks and [development](docs/development.md)
for database and configuration details. Coding agents should also read [AGENTS.md](AGENTS.md).

## Naming conventions

Follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
for commit subjects and PR titles: `type(scope): description`. Scope is optional.
Use `feat` for features, `fix` for bugs; our other types are `docs`, `ci`, `build`,
`test`, `refactor`, `perf`, `style`, `chore`, and `revert`. Use lowercase types and
concise descriptions of the resulting change. Mark breaking changes with `!`
before the colon or a `BREAKING CHANGE:` footer, and explain migration effects.

The specification does not define branch names. Our local adaptation is
`type/short-kebab-description`, with an optional area in the description:

| Branch | PR title / commit subject |
| --- | --- |
| `feat/frontend-catalog` | `feat(frontend): add product catalog` |
| `fix/auth-token-expiry` | `fix(auth): reject expired tokens` |
| `docs/naming-conventions` | `docs: define repository naming conventions` |
| `ci/checkout-update` | `ci: update checkout action` |

Do not create `agent/` branches. Existing Dependabot-managed branches keep their
bot names; apply compliant PR titles and squash subjects when merging them.
Use the final PR title as the squash commit subject. Preserve breaking-change
information in the squash message. This policy applies to future work; do not
rewrite merged history. The ecommerce-naming skill guides agents through these
checks. This is a documented review policy, not an automated CI naming gate.

## PR ownership

Repository ownership is recorded in .github/CODEOWNERS. Assign maintenance PRs to
@youneshenniwrites and apply relevant scope labels. Agents use the
ecommerce-pr-ownership skill and its checked helper after PR creation. Authorship
is the actual GitHub account that opens the PR; do not forge a different author.

## Review and merge

Use the PR template headings and reference the GitHub issue. Use Closes #N
for completed tickets and Refs #N for partial work. Never invent a ticket reference.

Explain the problem and resulting behavior, then give the commands/results and
material limitations. Include relevant screenshots for UI changes, or API/test
output for backend changes. Do not include tokens, passwords, or customer data.

Review the exact pushed revision. Address actionable findings and rerun affected
checks. A self-review must say it is a self-review; it is not independent approval.
All applicable CI jobs must pass before merge. Follow the
[Codex review policy](docs/codex-review.md); the status is informational pending #38. A verified clean external review replaces a human approval; ticket
acceptance must still be checked. No workflow in this repository
bypasses review to automatically merge dependency updates.

Merge permission does not authorize cloud provisioning. Cloud deployments need
an agreed environment, budget, secrets/identity design, and rollback plan.
Report vulnerabilities privately through [SECURITY.md](SECURITY.md).

## Delivery tracking

Follow [delivery workflow](docs/delivery.md) for issue scope, board transitions,
PR linkage and completion evidence. The project board is the live work queue.
