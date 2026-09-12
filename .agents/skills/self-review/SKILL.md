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
