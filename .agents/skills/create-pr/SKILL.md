---
name: create-pr
description: Create or refresh an ecommerce pull request with issue linkage, accurate testing, ownership and Codex review.
---

Read [delivery rules](../../../docs/delivery.md), the [PR template](../../../.github/pull_request_template.md), and the existing [naming](../ecommerce-naming/SKILL.md) and [ownership](../ecommerce-pr-ownership/SKILL.md) skills. Resolve paths relative to this file; run repository commands from the repository root.

Inspect the working tree, intended base, full diff, linked issue and existing PRs before writing. Reuse an existing PR for this branch instead of creating a duplicate. Preserve unrelated work and real contributor authorship. Reuse or create a scoped issue under the user's delivery authorization.

Check the issue against the canonical ticket boundaries in the delivery rules linked above. If the diff materially expands the outcome, refine its scope before opening the PR; retain necessary tests and safeguards in the same viable slice. Refresh the issue handoff with the PR and actual verification state.

Use [self-review](../self-review/SKILL.md) before requesting external review. Fill the canonical template from the final implementation: a short customer or contributor outcome, linked issue, factual acceptance criteria, tests actually run and relevant limitations. Keep self-review disclosure brief and link current-head external review and CI evidence with their actual state; pending or failed checks must not be described as passed. Keep assignment in the sidebar rather than repeating owner/reviewer metadata or review checkboxes. Use Closes only for a fully completed issue; otherwise Refs. Remove irrelevant optional sections and Jira placeholders.

Before requesting external review, complete [preflight-review](../preflight-review/SKILL.md)
and record actual evidence; it does not replace independent Codex review.

Within existing push/PR authorization, commit and push the intended changes, then create or refresh the PR using gh/API. Pass multiline text through a body file or structured JSON, never shell interpolation of PR content. Apply the ownership helper and read back title, base/head, body, owner assignment and labels. Request only Codex using the current-head protocol in [review documentation](../../../docs/codex-review.md); avoid duplicate requests for an unchanged head.

Use [update-delivery-board](../update-delivery-board/SKILL.md) to move the linked ticket to In review. Report the PR URL, checks and review state. Creating a PR does not itself authorize merging or deployment; continue a separately authorized delivery task under the repository merge policy.

Follow AGENTS.md for small coherent commits and regular verified pushes within
existing authorization. Keep code and its tests together; do not save all changes
for one final large commit. A push does not waive fresh current-head review.
