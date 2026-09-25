---
name: deliver-ticket
description: Carry an authorized VINDOR implementation ticket through testing, PR review, eligible merge and delivery closeout. Use when asked to deliver or continue a ticket; not for questions or review-only requests.
---

# Deliver a ticket

Read root AGENTS.md, docs/delivery.md, docs/delivery-mode.md and the issue's latest
handoff. The existing portfolio-completion plan owns priorities; this skill is
execution guidance, not another plan. Verify actual GitHub and Git state on resume.

## Scope and persistence

Identify the requested finish line and existing authorization. Continue through
implementation, relevant tests, self-review/preflight, create-pr, review fixes,
eligible merge, authorized deployment verification and docs/board closeout.
Invoke the existing named skills for these operations rather than duplicating
policy here. PR creation, CI starting or a review comment is not itself completion.
A create-PR-only or review-only request retains its narrower finish line.
Example finish line: deliver VIN-30 through reviewed PRs, merge under existing
policy, verify development and update plan/board until complete or genuinely blocked.
Keep one feature active; parallelize within its outcome, not unrelated features.

While CI/review is running, use bounded waits and do independent work within the
same ticket. Batch findings into coherent fixes; independently verify each finding.
Complete a full internal verification pass before external review; retain Codex
and CodeRabbit review under repository policy. Keep non-blocking deferrals linked
under existing policy. Do not request duplicate
reviews for an unchanged head. New blocking correctness/security findings remain
blocking even after multiple rounds. Internal verification is not external approval.

When genuinely blocked, record the exact dependency, current revision, completed
evidence and next action on the issue. Ask only for missing decisions/access or
unauthorized consequential actions; continue independent authorized work. Do not
busy-loop unchanged failures, fabricate approval, bypass checks or silently take
another backlog ticket. A skill does not keep a finished turn running or create a
scheduler. No scheduled wakeups without a separate explicit request.

## Checkpoints and verification

Follow [evidence-backed checkpoints](../../../docs/delivery.md#evidence-backed-checkpoints)
in the existing issue handoff. Define observable outcomes and verification before
implementation; let an independent verifier prepare failure scenarios in parallel
when useful. Apply visual acceptance only to relevant UI changes. Use the linked
lightweight handoff checker for multi-step completion; its output is structural
validation, never proof of approval or delivery. Do not create another plan.

## Durable handoff and completion check

Use the existing issue handoff as the recovery record, not a second task ledger.
Before an interruption or phase transition, record the branch/PR and exact head,
completed evidence, unresolved findings, current blocker, next action and any
external action already requested. On resume reconcile these with GitHub and Git;
old handoff text is context, not proof that a check or review is still current.

Before ending an implementation turn, check whether the requested finish line is
met, an explicit pause applies, or a genuine blocker prevents further authorized
work. If a review or check is pending, continue bounded supervision during the
active run. If continuation is unavailable, leave an honest resumable handoff;
never claim monitoring continues after the turn ends. This is an instruction-level
check, not an installed stop hook or guarantee of unattended execution.

Deduplicate work by PR, head revision and review/comment identifier. Re-read live
state before repeating a review request, response, merge or board mutation. A
retry after an interrupted tool call must first establish whether it succeeded.
Keep investigation-only assignments read-only with findings and a next decision;
turn them into implementation only within the owner's authorized scope.

These principles are adapted from [Firstmate](https://github.com/kunchenguid/firstmate).
Its [Codex App boundary](https://github.com/kunchenguid/firstmate/blob/main/docs/codex-app-backend.md)
does not provide a supported desktop runtime backend. No Firstmate scripts,
watchers, terminal backends or hooks are installed by this workflow.

## Execution mode

Read docs/delivery-mode.md at the start of each ticket. Direct user instructions
prevail. Change the saved mode only when the owner explicitly asks to switch; a
quota reset or elapsed time is not authorization. Persist a requested switch in
that file through the normal PR process; disclose if it is still local/unmerged.

- **Lean:** one agent; no delegation. Batch independent reads, reuse valid test
  evidence and run checks proportionate to the change. Finish the same delivery
  loop; Lean does not mean weaker acceptance or review.
- **Parallel:** when explicitly enabled and tools permit, the lead may delegate
  bounded implementation and independent verification work. Start with at most
  three agents including the lead. Agree contracts first; give each writer an
  isolated worktree and disjoint ownership, plus isolated ports/databases for tests.
  The verifier challenges acceptance and reproduces failures. The lead integrates,
  runs combined checks, handles external reviews, and serializes merges/closeout.
  Avoid parallel work whose dependency or coordination cost exceeds its benefit.

## Roles in Parallel mode

- Lead: priorities, integration, PRs, merges, deployment evidence and tracking.
- Implementer: bounded feature implementation and regression tests.
- Verifier: independently challenge acceptance, reproduce failures and test the
  customer journey. For payments, prepare webhook-race and inventory-release
  scenarios while implementation proceeds, after agreeing the state/API contract.

## Bookkeeping tooling and pilot

Reuse existing naming, metadata and documentation-discovery tooling. Proposed
extensions should validate issue links/labels/milestones, report required checks
and exact reviewed revisions, reconcile board state after merge, calculate the
percentage and pink graphic from the canonical checklist, and flag contradictory
plan/issue summaries. These extensions are recorded requirements, not implemented
automation in this skill. Scripts handle deterministic checks and arithmetic;
agent judgment still decides whether acceptance evidence warrants completion.
Do not turn this tooling into a prerequisite for the next feature.

Run the one-time pilot only when VIN-30 is the authorized active ticket and its
issue handoff does not record the pilot as completed. Otherwise skip this block.
Use the currently selected mode; record pilot completion in VIN-30’s handoff
when finished so later invocations do not restart it. Record start/end
revision and timestamps, owner interventions needed to resume routine work,
external review rounds, and elapsed time to verified delivery in the issue handoff.
Separate waiting time and product/access decisions from avoidable interventions.
Do not invent a baseline or promise a speedup; evaluate the pilot before expanding.

## Optional unattended continuation

Only after a separate explicit request, configure a bounded follow-up for the
specified delivery: stop at completion or the agreed boundary, prevent overlapping
runs, and notify only for meaningful progress or action required. Local scheduled
work needs the computer on and app running; closing the laptop does not move the
checkout to the cloud. No scheduler is enabled by this skill or by Parallel mode.

## Closeout

Use update-delivery-board and update-docs after merge. Update the one canonical
checklist only for verified outcomes, then synchronize VIN-155's percentage and
pink graphic from that count. Preserve implemented/merged/deployed/verified
distinctions. Report outcome, PR, evidence, blocker and next action concisely.
Stop at the authorized finish line; naming the next ticket does not authorize
starting it. Do not spawn another task or enable background automation as an implicit follow-up.
