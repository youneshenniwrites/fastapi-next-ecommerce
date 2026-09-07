---
name: ecommerce-evidence
description: Verify an ecommerce change and prepare a PR review with reproducible backend or UI evidence.
---

Record the revision and a behavior-level acceptance criterion. Capture a failing
regression test or request before a fix when feasible. After the change, run
`make check` and inspect the GitHub checks for the exact pushed commit.

For API work, show status codes and state changes from isolated tests or probes.
Container CI runs backend/scripts/smoke.py against disposable PostgreSQL. For UI
work once a frontend exists, capture the affected flow at appropriate viewport
sizes and record loading/error states alongside the happy path. Screenshots
complement tests; they do not replace them.

Review the full diff for authorization, migration, and transaction regressions.
Fix actionable findings and rerun affected checks. Describe what was tested,
what was not, and any remaining limitations in the PR. Call the review self-review
when you also implemented the change. Public uploads and Greptile are optional
integrations requiring appropriate authorization, not prerequisites for finishing.
