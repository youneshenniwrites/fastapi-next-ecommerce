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
Python patch updates are grouped; open PR counts are limited. Applicable CI and
current-head CodeRabbit approval remain mandatory. The [dependency continuation](dependabot.md)
repairs eligible stale requirements exports using trusted, offline tooling. Unsafe
inputs and genuine test failures remain blocked for investigation.
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
configured**. Eligible updates can merge through the event-driven
[dependency policy](dependabot.md) after protected CI; other proposals remain manual. See
[delivery workflow](delivery.md) for maintenance handoff expectations.

`python3 scripts/check_branch_name.py` validates PR event metadata and its issue
using a read-only GitHub token. The trusted `branch-naming.yml` workflow checks
all PRs, including docs-only changes, through `publish_branch_name.py`. It checks
out main only, never executes PR code, and publishes a status on the PR head.
Because GitHub statuses belong to commits, every open PR sharing a commit must
pass together. Repository-wide serialization prevents competing runs from
publishing different answers; a second paginated read checks group membership
and policy metadata before success. Opening, updating, editing or closing a PR
reconciles all open groups. These are API snapshots, not an atomic merge lock;
API errors or concurrent changes require a successful fresh run before merge.
After merge, manually dispatch it and verify results before requiring the new
status alongside existing protections. Until that rollout, the status is not required. See CONTRIBUTING.md for naming/exemptions.

## Documentation reference discovery

Before feature/status PRs, create-pr and self-review require
`python3 scripts/doc_references.py 119 "placement" "checkout"` with the actual
issue and feature terms. This lists tracked documentation references with file/line
locations for human inspection. It does not validate their truth, inspect remote
Wiki/issues, or replace current-head review. Record the inspection in the PR Review
section; no new CI gate or custom command is introduced.

## Review-trigger efficiency (VIN-147)

The review gate refreshes once when the permissionless review-event relay completes,
rather than both when it is requested and when it completes. PR/comment events,
the five-minute recovery schedule, manual refresh and trusted execution remain.
Completion is not filtered by success: the gate still reads authoritative GitHub
review evidence after failed or cancelled relay runs. This removes a duplicate
refresh and its downstream continuation opportunity per new relay lifecycle;
it does not make the application/browser tests faster or remove security checks.

Five completed workflow samples and timestamps are linked from VIN-147. Expected
reduction: one early gate refresh and its downstream continuation opportunity per
new relay lifecycle. No repository-wide percentage or hosted runtime improvement
is claimed before merge and comparable observation. Reverting this slice restores
`[requested, completed]`; merge queue/grouping and empty-queue setup remain separate.
