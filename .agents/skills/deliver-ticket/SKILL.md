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

While CI/review is running, use bounded waits and do independent work within the
same ticket. Batch findings into coherent fixes; independently verify each finding.
Keep non-blocking deferrals linked under existing policy. Do not request duplicate
reviews for an unchanged head. New blocking correctness/security findings remain
blocking even after multiple rounds. Internal verification is not external approval.

When genuinely blocked, record the exact dependency, current revision, completed
evidence and next action on the issue. Ask only for missing decisions/access or
unauthorized consequential actions; continue independent authorized work. Do not
busy-loop unchanged failures, fabricate approval, bypass checks or silently take
another backlog ticket. A skill does not keep a finished turn running or create a
scheduler. No scheduled wakeups without a separate explicit request.

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

## Closeout

Use update-delivery-board and update-docs after merge. Update the one canonical
checklist only for verified outcomes, then synchronize VIN-155's percentage and
pink graphic from that count. Preserve implemented/merged/deployed/verified
distinctions. Report outcome, PR, evidence, blocker and next action concisely.
Do not spawn another task or enable background automation as an implicit follow-up.
