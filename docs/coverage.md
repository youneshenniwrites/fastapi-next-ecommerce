# Reading coverage evidence

Open the backend or frontend quality job's Actions summary. It shows line/branch
covered and measured counts, percentages, the tested revision, measured scope,
existing thresholds, test-step outcome and a link to its downloadable report.
A PR workflow normally tests GitHub's synthetic merge revision (`GITHUB_SHA`),
not the PR head alone. These summaries do not compare against a base revision.

| Measurement | Included scope | Existing enforced thresholds |
| --- | --- | --- |
| Backend | `backend/app`, excluding `app/tests` | coverage.py combined line/branch score ≥85% |
| Frontend | Only `src/lib/catalog.ts` and `src/lib/session.ts` | Vitest statements ≥95%, branches ≥90%, functions 100%, lines ≥95% |

The frontend percentage is **not coverage of the entire frontend**. Components,
routes and other utilities are outside this measurement. Backend migration
subprocesses and frontend browser flows have separate tests; they do not increase
these coverage percentages. Generated API types and vendor code are outside the
current frontend include list. Broader meaningful measurement and regression
comparison are follow-up stories #96 and #97 under #57.

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
workflow against PR code or artifacts. Coverage comparison/publishing needs its
own reviewed trust boundary in #96.

Scope labels describe the checked-in coverage configuration. Backend XML totals
are read from coverage.py; the renderer does not reconstruct the configured
source/omit rules from XML. Update the scope label/documentation whenever those
rules change. Frontend report filenames must match its two-file documented scope.
