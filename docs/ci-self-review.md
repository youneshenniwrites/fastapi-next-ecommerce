# CI self-review — 8 September 2026

Implementation self-review for #37, covering all six workflow files, the review
adapter, publication code, regression tests and the main-protection configuration.
This does not replace external Codex review.

## Findings fixed in the consolidated revision

| Finding | Reproduction and correction |
| --- | --- |
| An evidence API failure abandoned later PRs, leaving their old status untouched | A regression failed against the previous publisher. Processing now isolates errors per PR and continues through all commit groups; the overall run fails if any refresh fails. |
| Two PRs sharing a SHA could overwrite a pending result with success | A regression reproduced the incorrect final success. Publication now aggregates every open PR sharing the SHA, including scoped refreshes. |
| Every poll consumed new commit statuses, eventually hitting GitHub's limit | The publisher now compares the last state and reason. A test runs 1,001 identical refreshes and requires one status write. |

Additional checks cover head/draft changes during inspection, REST and GraphQL
pagination, partial responses, repeated cursors, status-write failures, untrusted
review requests, stale/forged results and dismissed findings. Existing Codex
findings on commenter authorization, review events and dismissal remain covered.
The final external finding on edited older reviews is covered using GraphQL
updatedAt and inline comment timestamps. All 42 regression tests pass locally.

## Workflow inspection

- Write-enabled review refresh checks out only default-branch code, persists no
  credentials, and consumes no relay artifacts, PR dependencies or shell content.
- The review-event relay has no token permissions or checkout. Its receiver uses
  default-branch workflow_run events and fetches evidence independently.
- Backend/frontend/audit/test workflows use read permissions and pinned actions.
  Test databases and Compose teardown are confined to disposable hosted runners.
- All six YAML files parse; all action references are full commit SHAs, and every
  job has a timeout. Runtime checks continue in GitHub CI.
- Head pushes, reopening, draft transitions, base edits and closure refresh the
  gate. Review events use the relay; reactions/thread resolution also have polling.
- Main's current CI/admin/conversation requirements were inspected. Human approval
  replacement and first default-branch activation still require final verification.

## Explicit limits

An Actions inspection result is a snapshot, not Codex's internal execution log.
GitHub scheduling and API outages can delay it. If listing PRs or writing statuses
fails, code cannot guarantee that GitHub has removed an old green status; merging
requires a fresh successful refresh and current evidence. Protection coverage and
merge-button behaviour on other targets remain deferred in #38. No deployment or
claim of production readiness is included.

Sources: [GitHub status semantics and limits](https://docs.github.com/en/rest/commits/statuses),
[workflow event trust and lifecycle](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).
