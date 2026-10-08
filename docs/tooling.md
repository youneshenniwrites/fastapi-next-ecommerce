# Engineering checks

The repository checks both applications. See [CI pipeline](ci.md) for frontend
quality, build/browser checks and the named backend stages. Backend checks cover
lint/format, scoped service types, tests, PostgreSQL, containers/migrations and dependency auditing.
These checks support review; they do not certify production readiness.

| Command | Purpose |
| --- | --- |
| `make check` | Ruff lint/format, scoped service types and isolated tests |
| `make typecheck` | Check order/payment service boundaries and prove representative mistakes are rejected |
| `make coverage` | Tests plus branch-aware coverage, with an 85% minimum |
| `make audit` | Audit the installed locked Python environment for known vulnerabilities |
| `make requirements-check` | Detect drift between uv.lock and the pip compatibility export |
| `make restore-rehearsal` | Restore a freshly generated fictional database into a separate disposable local target; [runbook](restore-rehearsal.md) |
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

### Temporary VIN-269 tooling exception — expires 17 October 2026

On 3 October the owner approved accepting only
[GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
on the verified development-only `braces` dependency paths until 10 October.
On 8 October the owner extended that same exception once, to
**17 October 2026, 23:59 UTC**. This accepts the risk; it does not fix the package.
The current full audit reports seven dependent entries from this one advisory.
Runtime-only auditing is clean. The exposure is development glob processing in
Next ESLint/shadcn tooling; arbitrary untrusted patterns can exhaust its stack.
No published patched release was verified; unsafe downgrades/forks were rejected.

Run `python3 scripts/frontend_audit.py` from the repository root with the pinned
Node/npm on PATH. Both existing frontend audit jobs use this same gate. It retains
complete `frontend/audit.json` and `frontend/audit-runtime.json` reports and emits
an explicit accepted-risk summary. Other advisories, changed dependency files or
paths, runtime findings, malformed/unavailable audit evidence and expiry fail.
`frontend/audit-exception.json` pins the exact manifest/lockfile and reviewed graph.
Raw `npm audit` still fails while this upstream issue remains present.

PR #305 reassessment (5 October): the Next.js, ESLint plugin, Vitest and
Vitest coverage updates retain the same seven development-only advisory entries, exact
paths and zero runtime findings. shadcn remains at 4.21.0 because 4.21.1 adds
an affected `@shadcn/registry` path outside the accepted graph. The dependency-file
hashes were renewed after fresh full/runtime audits; the advisory, accepted graph
and 10 October expiry are unchanged. This is accepted risk, not remediation.

PR #306 reassessment (5 October): tailwind-merge 3.7.0 changes no accepted
advisory packages or dependency paths. Fresh full and runtime reports retain the
same seven development-only entries and zero runtime findings. The exact file
hashes were renewed after that comparison; the advisory, graph and 10 October
expiry are unchanged. This remains accepted risk, not remediation.

PR #309 reassessment (6 October): locked updates within existing ranges move
`sharp` to 0.35.5, `source-map-js` to 1.2.2, `@modelcontextprotocol/sdk` to
1.32.1 and `proxy-addr` to 2.0.8. Fresh audits then report zero runtime findings
and the same seven development-only `braces` entries, paths and advisory. Only
the lockfile hash was renewed. The 10 October expiry is unchanged. This removes
the new advisories; the `braces` exception remains accepted risk, not remediation.

Extension reassessment (8 October): the registry still publishes latest
`braces@3.0.3`, the advisory still lists no patched version, and upstream has
merged no fix. Current Next ESLint (16.4.0 and 16.5.0 canary) still pins
`fast-glob` 3.3.1. Only `expiresAt` changed; the advisory, the seven-entry graph,
the file hashes and every guard are unchanged. With Node's default stack, the
deepest pattern under `braces`' 10,000-character limit (4,999 levels) did not
crash `braces` or `micromatch`. A 400 KB stack failed at 3,500 levels and a
200 KB stack at 1,000 levels. The patterns here come only from our own tooling
configuration, so the residual risk is a crashed local lint run.

[VIN-269](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/269)
remains open for remediation. Install a verified compatible upstream fix when
available, confirm the complete audit is clean, then remove the exception and
its fixture/guard in the same reviewed change. Do not silently extend expiry or
refresh hashes to accommodate dependency changes. No branch protection is disabled.

Dependabot checks Python/uv, GitHub Actions, and backend Docker dependencies weekly.
Python patch updates are grouped; open PR counts are limited. Applicable CI and
verified clean current-head Codex review remain mandatory. The [dependency continuation](dependabot.md)
repairs eligible stale requirements exports using trusted, offline tooling. Unsafe
inputs and genuine test failures remain blocked for investigation.
Frontend npm dependency updates are enabled weekly, with at most two open PRs.

CI actions are pinned to reviewed commit SHAs, with version comments for readers.
Dependabot can propose updated pins. Jobs have time limits and read-only repository
permissions. The backend workflow cancels superseded runs for the same ref.

Scoped service typing is described below. Repository-wide typing, code scanning
and additional required-check rules remain further increments; this gate does not
establish those controls.

## Scoped backend service types (VIN-261)

Run `make typecheck` from the repository root after installing locked development
dependencies. `make check` and the backend quality CI job run the same checker.
Pinned mypy checks `app/services/orders.py`, `app/services/payments.py`,
`app/providers/stripe.py` and `app/providers/payment_types.py` with strict settings.
The service wrapper preserves provider argument and return types; payload types
retain absent and nullable fields. Runtime validation still establishes payment
binding, ownership, amount and state.

The runner also checks temporary examples: valid service/provider calls must
pass, while a wrong order identifier, an invalid terminal payment state, an
unchecked nullable checkout URL and an incorrect provider return assignment must
fail with the expected diagnostics.
It removes these examples afterward. This verifies that the scoped gate catches
representative mistakes; it does not prove runtime correctness.

Imported modules supply their annotations but their own diagnostics are outside
this bounded gate. Routes, other services, tests and the full backend are not
claimed strictly typed. The existing behavior tests, coverage, API-contract,
PostgreSQL and container checks remain separate requirements. SDK payload casts
stay at the provider/persisted transport boundary and do not authorize payment.

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
