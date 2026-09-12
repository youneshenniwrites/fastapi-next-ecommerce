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

## Ticket hierarchy and review scope

Use an **epic** issue for a larger outcome and link its child **story** issues
with GitHub sub-issues when available, otherwise explicit parent/child links.
A story delivers one independently testable behavior, normally in one PR.
Implementation **subtasks** are a checklist inside that story; create a linked
issue only when separate ownership or delivery is useful. A **bug** issue records
reproduction, expected/observed behavior and regression evidence. These are work
categories, not additional board statuses or a requirement for custom labels.

Before coding, record the story's outcome, parent (if any), included behavior,
exclusions, acceptance criteria, dependencies and validation. Split substantial
architectural prerequisites before implementation; keep their interfaces stable
so later stories can build on merged work. Prefer a usable vertical slice over
separate tickets for arbitrary files or technical layers. A standalone foundation
is appropriate only with a bounded contract and meaningful verification.

Keep necessary authorization, data integrity, error recovery, tests and contract
documentation inside each viable slice. They are not optional later polish.
For example, an add-to-cart story includes ownership checks, stock rejection and
repeat-click behavior; quantity editing can follow as a separate tested story.
An epic is complete only when its required child outcomes are delivered; merging
one child PR does not close the parent.

Aim for roughly 200–400 meaningful changed lines per PR; above about 500, reassess
scope and record the split or explain why the coherent change should stay together.
Exclude generated outputs and lockfiles from this planning signal. This is not a
CI limit: do not omit tests, conceal changes or create broken intermediate slices
to satisfy a number. Small commits do not make an oversized PR easy to review.
If new findings substantially expand scope, update the issue and split independent
follow-ups before adding more work. Defects required for the active acceptance
criteria remain in scope; follow existing approval rules for any deferral.

## Starting without conversation history

1. Open the actual repository and read root AGENTS.md, this policy, and the assigned
   issue with its latest handoff. Inspect local changes, base/head and open PRs.
2. Read scoped AGENTS.md files and applicable skills. For framework changes use
   [framework guidance](framework-agent-guidance.md) to locate installed-version
   Next.js documentation or the official FastAPI skill; retain local architecture
   and security decisions rather than copying generic examples.
3. Verify ticket boundaries and dependencies before editing. Use
   [refine-tickets](../.agents/skills/refine-tickets/SKILL.md) for broad work.
   Missing permission or contradictory scope requires clarification; a missing
   history transcript does not require reconstructing earlier conversations.

AGENTS.md is the repository entry point, versioned docs own policy, skills own
repeatable procedures, and issues/PRs own current delivery evidence. The Wiki links
to these sources for explanation. Do not duplicate policy in every file or copy
moving upstream documentation into the repository. Some tools do not discover
AGENTS.md or skills automatically: configure their supported instruction entry
point to read AGENTS.md, or explicitly include that instruction when starting.
Never claim a fresh agent has loaded guidance without checking its discovery path.

## Board and PR lifecycle

- Backlog: planned work; start only when scoped and unblocked.
- In progress: implementation underway; keep one implementation ticket active by default.
  Explicit owner-authorized parallel work uses isolated worktrees, records each
  ticket's scope and overlaps, and isolates any running services.
- In review: a PR is open and review/checks are underway.
- Done: acceptance criteria are met and implementing PRs are merged.

Record blockers on the issue while retaining its current status. Do not mark work
Done merely because a PR exists or CI passes. Close rejected work as not planned
with a reason; do not represent it as delivered. A retrospective summary can
record previously delivered work, explicitly labelled as retrospective.

Each PR includes its GitHub issue, validation and review evidence. Use Closes #N
only when that PR completes the whole ticket; use Refs #N for partial work.
GitHub Issues are our ticket tracker. Preserve real authorship,
assign youneshenniwrites and apply scope labels. Self-review must be identified.

## Finish and resume

Before merge, review the full exact-head diff, resolve findings and require all
applicable checks and external tool review/approval for the current head.
Self-review alone does not authorize merging. Never bypass branch protection.
The informational `Codex review` status reports review evidence; enforcement is
deferred to #38. Inspect the actual current-head review before merging; follow [its evidence protocol](codex-review.md). A human Approve review is
not required. Unknown or missing evidence keeps the PR open unless the owner
explicitly authorizes a documented deferral. The #35/#37 deferral is not a blanket
exception for later PRs.
After merge, verify issue closure, update board status, record
evidence and identify the next unblocked Backlog ticket. Check README, design notes,
roadmap, Wiki and skills for changes relevant to the delivered behavior.

At handoff, update a compact section in the active issue (link PR evidence rather
than duplicating logs): implementing PR/branch, completed work, remaining work and
blockers, tested revision and results, and the next concrete action. Distinguish
local, pushed, merged and deployed states. Refresh it when pausing, transferring
work or changing scope; verify it against Git and GitHub when resuming. Do not
store secrets, transcripts or machine-specific temporary paths in the handoff.
Report merged/open PRs, remaining blockers, checks and the next ticket.
Inspect open maintenance PRs and either resolve them within authorized scope or
record their next action; do not silently leave failures unexplained. This is an
agent workflow, not a continuously running service. Scheduled dependency review
is not configured. Dependabot proposes updates weekly; it does not review or merge.

## Common PR description and reviewers

The [PR template](../.github/pull_request_template.md) defines Summary, Issue,
optional Before / After, Acceptance criteria, Testing, Review, and optional
Deployment notes. Lead with a short customer or contributor outcome; fill
acceptance criteria from the issue and testing with the tested commit and actual
results. Use a brief self-review disclosure plus linked current-head Codex review
and CI evidence. State pending or failed results honestly and refresh evidence
after changes. Keep owner assignment and labels in the sidebar, without duplicate
review checkboxes or owner/reviewer metadata in the body. Remove irrelevant
optional sections. No Jira placeholder.

Assign youneshenniwrites on every PR; do not request them as reviewer.
Codex is the sole requested reviewer. Request Codex through the review
integration and verify completion on the current commit. A named reviewer in the
body is not evidence of a request or approval. The ownership skill contains the
operational steps; AGENTS.md routes future sessions to it. External approval
remains required before merge, including maintenance PRs.

## Reusable skills

Use the [delivery skill reference](delivery-skills.md) for repeatable PR creation,
self-review, Codex follow-up, board reconciliation and documentation updates.
