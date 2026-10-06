---
name: update-delivery-board
description: Reconcile ecommerce GitHub project items with actual issue acceptance, implementation, review and merge state.
---

Read [delivery policy](../../../docs/delivery.md). Use gh/API for project https://github.com/users/youneshenniwrites/projects/1 and repository youneshenniwrites/fastapi-next-ecommerce. Discover current project, item, field and option IDs instead of assuming cached IDs remain valid. Paginate items and issues before deciding an item is missing.

Reuse the existing repository issue and board item; link bot maintenance PRs from their existing maintenance issue. Add missing items within the requested scope and assign the owner. Do not create draft cards to represent completed delivery or duplicate historical summaries from the Wiki.

When authorized work starts on an issue, move that issue card to In progress before any code, branch, or commit, and read the status back. Parent epics stay put.

Choose status from evidence:
- Backlog: not started, including explicitly deferred follow-ups.
- In progress: started and unfinished, including a parent epic that already has merged children. Keep one implementation ticket active unless the owner authorized parallel work.
- In review: a ready PR is open and waiting on review. Never open a draft PR.
- Done: acceptance, review, CI, and merge are finished.

Assignee youneshenniwrites, scope labels, milestone, and priority labels still apply.

Do not equate issue closure with delivery: not-planned, duplicate or superseded work needs its actual disposition recorded, not Done. Partial merges do not complete the parent issue. Record blockers without inventing a fifth status. Archive a redundant/historical card only within cleanup authorization and preserve useful context in a linked issue or Wiki page.

Run this post-merge closeout after every merged PR, without being asked:
1. If the merge completes the whole ticket (Closes) and all required
   implementing PRs are merged, confirm issue closure and set its board card
   Done. For partial merges retain the parent status and report the blocker;
   for issue-less maintenance PRs create or mark no issue card.
2. Archive any separate PR card; the board contains issue cards only.
3. Refresh the issue handoff (merged commit, verification state, next ticket).
4. Run an [update-docs](../update-docs/SKILL.md) check for behavior the merge changed.
5. Report the resulting board state; never leave a merged item In review.

Make only necessary changes. Read back each changed item's status, linkage and assignment. Report updates and discrepancies that require a decision. Updating the board does not authorize implementing backlog work or merging PRs.

Owner-approved issues-only board: never add PR cards, including Dependabot.
Archive existing PR cards when cleaning the board; retain links on source issues.
