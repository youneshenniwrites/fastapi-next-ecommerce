# Engineering checks

The repository checks both applications. See [CI pipeline](ci.md) for frontend
quality, build/browser checks and the named backend stages. Backend checks cover
lint/format/tests, PostgreSQL, containers/migrations and dependency auditing.
These checks support review; they do not certify production readiness.

| Command | Purpose |
| --- | --- |
| `make check` | Ruff lint/format and isolated tests |
| `make coverage` | Tests plus branch-aware coverage, with an 85% minimum |
| `make audit` | Audit the installed locked Python environment for known vulnerabilities |
| `make requirements-check` | Detect drift between uv.lock and the pip compatibility export |
| `make hooks` | Install optional local pre-commit checks |
| `make hooks-check` | Run the hooks over tracked files |

Run make setup first. The hooks reuse the locked backend environment and require
uv on PATH. They check formatting rather than silently rewriting staged changes.
CI remains authoritative when hooks are not installed.

Coverage measures executable code under backend/app, excluding tests. Migration
subprocesses and browser behavior are verified separately; the report does not
measure a complete ecommerce product. See [coverage reports](coverage.md) for current run summaries, exact frontend
scope and thresholds. CI retains browsable HTML, raw coverage and dependency-audit
JSON artifacts for 14 days.

The dependency audit runs for PRs, main pushes, weekly, and on manual dispatch.
It audits development dependencies too. A failure must be investigated: dependency
vulnerabilities and an unavailable advisory service both produce unsuccessful runs.
Do not bypass or globally suppress failures to make CI green.

Dependabot checks Python/uv, GitHub Actions, and backend Docker dependencies weekly.
Python patch updates are grouped; open PR counts are limited. Changes still need
review and CI. An agent handling a uv update must regenerate requirements.txt if
Dependabot leaves it stale; the requirements check deliberately prevents drift.
Frontend npm dependency updates are enabled weekly, with at most two open PRs.

CI actions are pinned to reviewed commit SHAs, with version comments for readers.
Dependabot can propose updated pins. Jobs have time limits and read-only repository
permissions. The backend workflow cancels superseded runs for the same ref.

Next tooling increments should add static type checking as the SQLAlchemy models
are typed, code scanning, and repository rules for required checks. Those controls
are not enabled by this PR and should not be claimed as implemented.

## Dependency review decisions — 8 September 2026

- PR #21 was closed: Node 26 type declarations did not match the pinned Node 24
  runtime. Keep the types major aligned until a deliberate runtime migration.
- PR #22 was closed: Uvicorn 0.52.4 was already locked; the proposed lower-bound
  change added no runtime upgrade and left requirements.txt stale. Future Python
  updates must regenerate the pip export and pass consistency checks. This does
  not mean lower-bound changes are always inappropriate.
- PRs #19 and #20 upgraded SHA-pinned CI actions after upstream and CI review.

Dependabot's weekly proposals remain enabled. Scheduled agent review is **not
configured**, and passing checks do not automatically merge proposals. See
[delivery workflow](delivery.md) for maintenance handoff expectations.
