# PR coverage comparisons

The `PR coverage comparison` workflow tests the exact pull-request head and its
Git merge base with the event's target-base commit. Each backend/frontend job
creates a detached base worktree under the runner's temporary directory and uses
that revision's locked dependencies. It records all three full commit identities.
Backend XML and frontend LCOV reports feed `scripts/coverage_compare.py`; the job
summary shows compatible totals and coverage of changed measured executable lines.
Added lines outside the measured scope are disclosed, not counted as covered.

A failed or missing base report, a different measured file set, or changes to
`backend/pyproject.toml` / `frontend/vitest.config.ts` / `frontend/coverage-scope.json` make the baseline unavailable
or incompatible. Configuration comparison is deliberately conservative: even an
unrelated change to those files suppresses total comparison. No regression is
inferred without a compatible baseline. Failed head tests fail the job, even
though evidence collection runs afterward. Existing thresholds remain enforced;
the [regression policy](coverage.md#regression-policy) additionally limits line/branch decline to 0.5 percentage points and requires 90% coverage of changed measured executable lines. Missing baseline skips only total regression; no changed measured lines is N/A.

The workflow runs only on `pull_request`, with only `contents: read`, no secrets,
PR-comment publishing or credential persistence. All test execution stays in this
unprivileged job, including fork code. Reports, test logs, comparison Markdown and
revision identities are retained for 14 days in separate backend/frontend
`coverage-comparison-*` artifacts. Summaries are run-scoped supporting evidence;
reviewers must check their commit identities and the actual test result.
