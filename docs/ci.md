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
| Frontend / Production build and browser tests | Production build → disposable real API → desktop/mobile/axe and fault tests → package | Browser report, traces, screenshots, standalone build |
| Dependency audit / Python and frontend | Audit locked dependencies on PR/push, weekly, or manually | JSON reports |

The frontend browser job depends on its quality job. Backend jobs run independently
so failures do not hide other evidence. Frontend unit coverage measures maintained library TypeScript plus AccountForm and RetryCatalog;
route rendering, API integration and failure screens are covered by browser tests.
FastAPI's generated OpenAPI snapshot is checked in CI so API drift fails the PR.

See [coverage reports](coverage.md) for measured scope, unchanged thresholds, report
links and local reproduction. Missing reports are labelled unavailable, never 0%.

## Build versus deployment

A successful build is not a deployment. The frontend workflow produces a standalone
build artifact only after browser tests pass. The workflow summary explicitly marks
that CI itself does not deploy. Production delivery is a separate workflow.

Production delivery (#46) waits for all four main verification workflows on the
same commit, skips stale or already deployed revisions, and serializes releases.
Its named steps run migrations → Vercel API deploy and database reads → storefront
deploy → public smoke checks. The production environment and job summary link to
the release. API/browser sessions are checked without exposing secrets. Frontend
PR previews remain #45. Failed deployment does not automatically roll back schema.
See [the environment plan](../deploy/environments/README.md).

## Reading a failure

Open the failing named check, expand its failed step, then use its associated
artifact. Fix the root cause and rerun checks for the new head; do not skip tests
or suppress an audit to merge. Reports expire after 14 days. Fork PRs receive no
cloud secrets. Branch-protection required-check settings remain a separate admin
control; workflow definitions alone do not enforce repository rules.
