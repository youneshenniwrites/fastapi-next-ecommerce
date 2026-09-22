---
name: self-review
description: Review an ecommerce PR or local changes against issue acceptance criteria and identify or fix defects before external review.
---

Read root AGENTS.md and guidance for the changed components. Establish the intended base and head (or uncommitted changes) and read the linked issue. Review the whole diff, relevant callers, tests and configuration, not only the latest patch.

Trace the changed behavior through success and failure paths. Examine permissions and untrusted inputs, data integrity, API compatibility, migrations and CI trust boundaries when relevant to the change. Match acceptance criteria to implementation and tests. Keep the review scoped; record unrelated improvements separately rather than turning the task into a redesign.

For each concrete finding, record severity, location, trigger and consequence. In a review-only request report findings without editing. During an authorized implementation/fix task, reproduce and fix findings, add meaningful regression coverage, and rerun relevant checks. Review the final diff after fixes. Do not add tests that merely repeat implementation wording.

Report reviewed base/head, findings and their disposition, checks actually run and remaining limitations. “No findings” means none found in this review, not proof of correctness. Identify this as self-review when the same agent implemented the change. It never substitutes for the external current-head review required by [delivery policy](../../../docs/delivery.md).

Before concluding, apply [preflight-review’s historical lessons](../preflight-review/references/lessons.md)
to the changed behavior and check interacting regressions.

The exact-head review instructions above have one exception: the owner-authorized
[pure-main-sync carry-forward procedure](../../../docs/codex-review.md#review-carry-forward-for-a-pure-main-sync).
Apply every evidence and CI condition before omitting a repeat review; all other
changes require current-head review. This does not waive branch protection.

## Required documentation status check

Before pushing or requesting review for a feature/status change, run from the repo:

```sh
python3 scripts/doc_references.py ISSUE_NUMBER "feature phrase" "related term"
```

Use the actual issue number and meaningful terms, not these placeholders. Read
surrounding context for every relevant result, including API guides, README,
AGENTS, architecture, roadmap, ADRs and the canonical plan. Inspect the complete
PR, not only the latest patch. Broaden terms when results omit expected docs.
The script searches tracked text only; inspect affected Wiki pages and issue
handoffs separately. Matches are candidates, not proof; no matches is not a pass.

Reconcile statements as implemented, merged, deployed or operationally verified
using actual evidence. Preserve historical statements with explicit context.
Keep daily handoffs in the tracking issue. In the PR Review section record the
terms, documents checked and corrections (or why no updates are needed). This is
a required agent review step, not an automated correctness guarantee or CI gate.
