# CI and delivery pipeline

Every PR and main push runs backend and frontend verification. Job and step names
state the operation being performed, so a failed build, test or audit is identifiable
without reading shell commands. Workflows have read-only repository permissions,
pinned action SHAs, timeouts and cancellation of superseded runs.

| Workflow / job | Ordered work | Evidence |
| --- | --- | --- |
| Backend / Lint, contract and unit tests | Locked install → lint → format → export consistency → tests/coverage | Coverage summary, XML and HTML |
| Backend / PostgreSQL integration tests | Start disposable PostgreSQL → create separate migration DB → full tests | Test logs |
| Backend / Container build and migration smoke tests | Image build → migrations/startup → HTTP smoke → schema consistency → rollback/reapply | Failure logs |
| Frontend / Lint, types, contract and unit tests | npm ci → regenerate/check API contract → formatting → lint → types → unit coverage → audit | Scoped coverage summary, LCOV and HTML |
| Frontend / Browser shards and protected aggregate | Three isolated builds/APIs → partitioned desktop/mobile/axe and fault tests → require all shards → merge reports and publish package | Per-shard evidence, combined browser report and validated standalone build |
| Dependency audit / Python and frontend | Audit locked dependencies on PR/push, weekly, or manually | JSON reports |

The frontend quality job starts independently; three browser shards start after their
docs-only filter. The existing named browser check aggregates all three results and
fails for failed, cancelled or unexpectedly skipped shards. Both required checks must pass; delivery requires the
whole exact-main frontend workflow to succeed. Backend jobs also run independently
so failures do not hide other evidence. Frontend unit coverage measures maintained library TypeScript plus AccountForm, RetryCatalog, AddToCartButton and CartPrivateRegion;
route rendering, API integration and failure screens are covered by browser tests.
FastAPI's generated OpenAPI snapshot is checked in CI so API drift fails the PR.

See [coverage reports](coverage.md) for measured scope, unchanged thresholds, report
links and local reproduction. Missing reports are labelled unavailable, never 0%.

## Build versus deployment

A successful build is not a deployment. The frontend workflow produces a standalone
build artifact only after browser tests pass. Artifact presence alone is not
approval: quality may still be running or have failed. The workflow summary explicitly marks
that CI itself does not deploy. Production delivery is a separate workflow.

Production delivery (#46) waits for all four main verification workflows on the
same commit, skips stale or already deployed revisions, and serializes releases.
Its named steps run migrations → Vercel API deploy and database reads → storefront
deploy → public smoke checks. The production environment and job summary link to
the release. API/browser sessions are checked without exposing secrets. Frontend
[Reviewed manual PR previews](design/frontend-previews.md#verified-closeout--2-october-2026) are verified under VIN-45. Failed deployment does not automatically roll back schema.
See [the environment plan](../deploy/environments/README.md).

## Reading a failure

Open the failing named check, expand its failed step, then use its associated
artifact. Fix the root cause and rerun checks for the new head; do not skip tests
or suppress an audit to merge. Reports expire after 14 days. Fork PRs receive no
cloud secrets. Branch-protection required-check settings remain a separate admin
control; workflow definitions alone do not enforce repository rules.

## Frontend browser runtime (VIN-146)

The browser job uses the official Playwright Noble image, pinned by version and
immutable digest. It already contains Chromium and its operating-system dependencies;
there is no per-run browser download, browser-cache restore or apt installation.
The job still installs the locked npm packages, pinned Node/npm and Python tooling,
builds the production storefront on each of three isolated runners and runs one
file/project-level shard of the full suite. Tests within each shard remain serial.
A launch check rejects an SDK/image version mismatch before tests; update the image
tag, digest and expected SDK version together when upgrading Playwright. The cache
for npm and uv remains. Required check names, test projects, workers, retries, thresholds and
privacy settings are unchanged. Each shard uploads uniquely named reports; the
aggregate merges Playwright blob reports into `frontend-browser-evidence` and
publishes `storefront-build` only after all shards pass. The shard-1 candidate build
is intermediate evidence, not delivery authorization.

Quality and browser shards use separate runners; browser API fixtures use disposable
databases. Parallel jobs do not share mutable test fixtures. Browser tests remain single-worker
because payment stock, catalog and fault scenarios share state. Container pull time
and runner queue delay are included when comparing total workflow time. See
[VIN-146](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/146) for
measured evidence; the older cache-only observation did not prove a speedup.

References: [Playwright CI](https://playwright.dev/docs/ci#via-containers),
[container/version guidance](https://playwright.dev/docs/docker).

## Browser parallelism follow-up (VIN-280)

VIN-146 reduced setup/waiting, with an observed 40-second improvement on its
comparable main run. It did not accelerate browser tests. The 3 October main
baseline [37157077339](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37157077339)
took 476 seconds overall, including 369 seconds in browser execution.

Three shards preserve file/project ordering and fixture isolation; enabling several
workers against one shared fault/stock fixture would not. All 141 baseline cases
appear exactly once in shard discovery (54/43/44). Keep this partition check when
changing sharding or project selection. Runner provisioning and installs/builds
are duplicated, so lower elapsed time can cost more total runner minutes. Actual
hosted before/after measurements belong to [VIN-280](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/280);
no guaranteed runtime or speedup is claimed from discovery alone.

Reference: [Playwright sharding and report merging](https://playwright.dev/docs/test-sharding).
