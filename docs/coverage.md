# Reading coverage evidence

Open the backend or frontend quality job's Actions summary. It shows line/branch
covered and measured counts, percentages, the tested revision, measured scope,
existing thresholds, test-step outcome and a link to its downloadable report.
A PR workflow normally tests GitHub's synthetic merge revision (`GITHUB_SHA`),
not the PR head alone. These summaries do not compare against a base revision.

| Measurement | Included scope | Existing enforced thresholds |
| --- | --- | --- |
| Backend | `backend/app`, excluding `app/tests` | coverage.py combined line/branch score ≥85% |
| Frontend | Maintained `src/lib/**/*.ts`, `AccountForm` and `RetryCatalog` | Vitest statements ≥95%, branches ≥90%, functions 100%, lines ≥95%, globally and separately for the original catalog/session group |

The frontend percentage is **not coverage of the entire frontend**. The shared
`frontend/coverage-scope.json` includes all maintained library TypeScript (even
files not imported by a test) and two interactive components. Unit tests exercise
credential validation/submission/error recovery, pre-hydration credential guards,
API origin/cache/timeout behavior, conditional utility classes and catalog retry.
Other components and route composition remain outside unit measurement: their
Next.js routing, navigation and layout integration is exercised by browser tests.
Generated API declarations are excluded because contract generation validates them;
shadcn primitives and third-party dependencies are not included as application logic.

Backend migration
subprocesses and frontend browser flows have separate tests; they do not increase
these coverage percentages. Generated API types and vendor code are outside the
current frontend include list.

A failed test/coverage step remains failed even when a valid report is available.
The summary is supporting evidence, not a replacement gate or proof of test quality.
Missing/malformed reports are explicitly unavailable and fail the reporting step;
zero measured branches display N/A, not 100%. Artifact-upload failures are visible
in their own step. Reports expire after 14 days.

Download and extract `backend-coverage` to open `htmlcov/index.html` or inspect
`coverage.xml`. Download `frontend-unit-coverage` to open `lcov-report/index.html`
or inspect `lcov.info`. Artifact links require access to the repository/run.

## Reproduce locally

Use the locked runtimes/dependencies described in the development guide:

```sh
make coverage
cd frontend
npm test
cd ..
python3 scripts/coverage_summary.py --kind backend --report backend/coverage.xml --outcome success
python3 scripts/coverage_summary.py --kind frontend --report frontend/coverage/lcov.info --outcome success
```

Pass the actual test outcome (`failure` when the preceding test command failed).
Local summaries label the revision `local` and have no artifact link. HTML reports
are generated in `backend/htmlcov` and `frontend/coverage/lcov-report`.

Reporting runs in existing read-only PR jobs, including forks. It writes only the
job summary and uploads reports; it posts no PR comment and runs no privileged
workflow against PR code or artifacts. See [base comparison](coverage-comparison.md) for exact-head and isolated-baseline evidence.

Scope labels describe the checked-in coverage configuration. Backend XML totals
are read from coverage.py; the renderer does not reconstruct the configured
source/omit rules from XML. Update the scope label/documentation whenever those
rules change. Frontend report filenames must exactly match the shared include/exclude scope expanded against the checkout; missing, duplicate and unexpected files fail validation.


## Regression policy

The comparison job enforces a maximum **0.5 percentage-point decrease** in line
and branch coverage against a valid compatible baseline, and **90% coverage of
changed measured executable lines**. Ratios are compared exactly before display
rounding. The half-point allowance bounds small denominator changes near 100%
without weakening the existing absolute gates. Backend remains at 85% combined;
frontend remains at 95% statements/lines, 90% branches and 100% functions both
globally and independently for the original catalog/session group.

An unavailable/incompatible baseline skips only the total-regression comparison;
the changed-line gate still applies. No changed measured executable lines means
N/A, not invented coverage. Source scope changes are disclosed as incompatible,
and generated/unmeasured lines never count as covered. Include/exclude patterns
in `frontend/coverage-scope.json` are shared by collection and report validation.
