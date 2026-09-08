---
name: update-delivery-board
description: Reconcile ecommerce GitHub project items with actual issue acceptance, implementation, review and merge state.
---

Read [delivery policy](../../../docs/delivery.md). Use gh/API for project https://github.com/users/youneshenniwrites/projects/1 and repository youneshenniwrites/fastapi-next-ecommerce. Discover current project, item, field and option IDs instead of assuming cached IDs remain valid. Paginate items and issues before deciding an item is missing.

Reuse the existing repository issue and board item; bot maintenance PRs may be work items without duplicate issues. Add missing items within the requested scope and assign the owner. Do not create draft cards to represent completed delivery or duplicate historical summaries from the Wiki.

Choose status from evidence:
- Backlog: planned, not started work, including explicitly deferred follow-ups.
- In progress: implementation underway; retain the repository's one-active-implementation convention.
- In review: an implementing PR is open, including while checks fail or review is pending.
- Done: acceptance criteria are met and all required implementing PRs merged.

Do not equate issue closure with delivery: not-planned, duplicate or superseded work needs its actual disposition recorded, not Done. Partial merges do not complete the parent issue. Record blockers without inventing a fifth status. Archive a redundant/historical card only within cleanup authorization and preserve useful context in a linked issue or Wiki page.

Make only necessary changes. Read back each changed item's status, linkage and assignment. Report updates and discrepancies that require a decision. Updating the board does not authorize implementing backlog work or merging PRs.
