# Delivery workflow

The repository owns versioned commands, design notes and development rules. The
[Wiki](https://github.com/youneshenniwrites/fastapi-next-ecommerce/wiki) explains the
system; the [board](https://github.com/users/youneshenniwrites/projects/1) records
current delivery status. Link between them rather than copying live status tables.

## Before implementation

Find or create a repository issue with an outcome, scope, acceptance criteria,
dependencies and validation expectations. Reuse matching issues; existing bot PRs
can link the existing maintenance issue without creating duplicate tickets or PR cards. Refine
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

Use issue cards only; link PRs from the issue rather than adding duplicate PR
cards, including Dependabot PRs. Archive redundant PR cards without deleting PRs.
New human branches use `type/vin-N-short-description`; see CONTRIBUTING.md.

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
is not configured. Dependabot proposes updates weekly; eligible updates use the bounded automation policy below.

## Common PR description and reviewers

Use `VIN-N` for issues, where N is the actual GitHub issue number; use `PR #N`
for pull requests. PR titles start `[VIN-N] [type] Description`. Open with a linked
**Issue:** line containing the issue key and title, a Closes/Refs reference, then
a separate **Problem:** line. Follow CONTRIBUTING.md for separate
Conventional Commits commit/squash subjects; never copy the PR title into squash.

The [PR template](../.github/pull_request_template.md) defines the Issue/Problem opening, Summary,
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

## Bounded review cycles and standing authorization

On 20 September 2026 the owner requested cost-efficient review cycles and
explicitly authorized deferring new non-critical findings to follow-up tickets
and merging the current PR promptly. This applies to VINDOR delivery work,
including #160, until superseded by a later owner instruction.

Consolidate fixes and local verification before one fresh full review request for
the new head. Do not request repeat reviews on an unchanged head. Complete both
Codex and CodeRabbit reviews when both are requested. Required CI must pass for
the exact head; branch protection remains enforced. Completed current-head review
with only documented owner-authorized non-blocking deferrals is eligible to merge;
pending reviews or unresolved blocking defects are not. Do not represent deferrals
as a clean review or fabricate a successful review status.

Use impact to classify findings: security/privacy failures, data corruption,
money/inventory errors, broken core behavior and unmet in-scope acceptance criteria
block delivery regardless of priority label. Optional polish, maintenance and
other demonstrated non-blocking findings can move to linked follow-up tickets.
Reuse existing tickets where appropriate; record the finding, impact, rationale,
acceptance, validation and priority in the ticket, and link it from the PR and
review thread. Resolve deferred threads only with that explicit disposition.

Once these conditions are met, merge promptly without another approval request.
This authorizes the merge and its existing automatic delivery workflows; it does
not authorize protection bypasses, unrelated deployments, paid services or new
scheduled tasks. Verify CI/deployment and update the board normally. The owner
has requested no scheduled Codex wakeups to save credits.


### Pure-sync review exception

The owner-authorized [review carry-forward procedure](codex-review.md#review-carry-forward-for-a-pure-main-sync)
is the sole exception to requesting fresh reviews after a conflict-free main sync.
It requires preserved review evidence, reproducible merge/diff checks, interaction
assessment and passing current-head CI. It does not waive branch protection or
claim current-head external approval. Otherwise the exact-head rules above apply.

## Automated dependency exception

The owner-authorized [Dependabot policy](dependabot.md) allows eligible dependency-only
npm/uv patch and minor PRs to receive automated policy approval and protected
auto-merge without per-PR Codex review. Other PRs retain the normal review rules.
Bot PRs retain upstream titles; VIN-172 tracks the policy.

## Evidence-backed checkpoints

Within the active issue handoff, split substantial work into a few observable
outcomes, ordered by dependencies and risk. Each checkpoint names its acceptance,
verification method and eventual evidence. Agree API/state contracts before
parallel implementation. The verifier can prepare failure scenarios while code
is built; prefer behavioral tests before implementation when they clarify a
contract. Do not add tests that merely repeat copy or implementation wording.

For meaningful UI changes, identify an agreed design or existing reference and
compare the same viewport, data and interaction state. Check appearance and
behavior; record screenshots/results where useful. Backend-only and documentation
changes need no visual gate. Validate docs with relevant link, example and factual
checks, not a mandatory application end-to-end run.

Batch review findings under the existing bounded-review policy. A repeated failure
without new evidence calls for diagnosis or a concrete blocker, not an unlimited
critic/fixer loop. Preserve valid approvals only under the existing review rules.
After the authorized finish line, stop: identifying a next ticket is not permission
to start it. An explicit pause takes effect even with incomplete checkpoints.

### Lightweight handoff checker

For multi-step delivery, export the current issue handoff to a temporary JSON
snapshot and run `python3 scripts/delivery_check.py /path/to/handoff.json` before
claiming completion. The snapshot is disposable, not a second plan or progress
metric. Keep its source and any corrected evidence in the issue handoff.

The object requires nonempty `issue`, `revision` and `finish_line` strings;
`checkpoints` is a nonempty list of objects with `outcome`, `verification`,
`status: "done"` and nonempty `evidence`. `closeout` contains `review`, `merge`,
`deployment` and `tracking`; each has either `status: "done"` plus `evidence`, or
`status: "not-applicable"` plus a `reason` tied to the authorized scope. For a
PR-only request, merge/deployment may be inapplicable; do not excuse an obligation
that belongs to the requested finish line. Pending evidence remains incomplete.

Exit 0 means fields are complete, 1 means evidence fields are incomplete, and 2
means the input cannot be read/parsed. The checker does not query GitHub, validate
links, prove a revision was tested or judge whether an exemption is legitimate.
The lead must verify those facts, including current-head CI/reviews and board
state. It never grants merge permission, changes protection, installs a stop hook
or schedules work. On pause/blockage, record remaining work and the next action;
do not fabricate completion to get exit 0. Trivial single-step work can use the
same completion questions directly without generating JSON.
