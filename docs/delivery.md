# Delivery workflow

The repository owns versioned commands, design notes and development rules. The
[Wiki](https://github.com/youneshenniwrites/fastapi-next-ecommerce/wiki) explains the
system; the [board](https://github.com/users/youneshenniwrites/projects/1) records
current delivery status. Link between them rather than copying live status tables.

## Before implementation

Find or create a repository issue with an outcome, scope, acceptance criteria,
dependencies and validation expectations. Reuse matching issues; existing bot PRs
can serve as maintenance work items without creating duplicate tickets. Refine
broad backlog items into focused tickets before implementation. Assign the owner.
Read the relevant agent guidance and skills, inspect working-tree and PR state,
and choose a Conventional Commit branch. Prefer gh/API and Git; use browser UI
only for capabilities unavailable through those interfaces.

## Board and PR lifecycle

- Backlog: work needs refinement or has unmet dependencies.
- Ready: scoped, unblocked and ready to begin.
- In progress: implementation underway; keep one implementation ticket active.
- In review: a PR is open and review/checks are underway.
- Done: acceptance criteria are met and implementing PRs are merged.

Record blockers on the issue while retaining its current status. Do not mark work
Done merely because a PR exists or CI passes. Close rejected work as not planned
with a reason; do not represent it as delivered. A retrospective summary can
record previously delivered work, explicitly labelled as retrospective.

Each PR includes its GitHub issue, validation and review evidence. Use Closes #N
only when that PR completes the whole ticket; use Refs #N for partial work. Keep
No Jira ticket. when no real Jira reference exists. Preserve real authorship,
assign youneshenniwrites and apply scope labels. Self-review must be identified.

## Finish and resume

Before merge, review the full exact-head diff, resolve findings and require all
applicable checks. After merge, verify issue closure, update board status, record
evidence and move newly unblocked work to Ready. Check README, design notes,
roadmap, Wiki and skills for changes relevant to the delivered behavior.

At handoff, report merged/open PRs, remaining blockers, checks and the next ticket.
Inspect open maintenance PRs and either resolve them within authorized scope or
record their next action; do not silently leave failures unexplained. This is an
agent workflow, not a continuously running service. Scheduled dependency review
is not configured. Dependabot proposes updates weekly; it does not review or merge.
