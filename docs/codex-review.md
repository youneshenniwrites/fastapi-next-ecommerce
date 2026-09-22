# Automated Codex review gate

## Delivery decision — 8 September 2026

The owner merged #37 and explicitly requested finishing #35 while deferring
remaining work to the board. This delivery provides **review-status visibility**,
not enforceable PR-specific approval. The inherited-SHA approval finding and
protection coverage are deferred to #38. Do not require this commit status in
branch protection until that ticket is resolved. The formal human approval count
is not part of the owner's automated workflow; existing CI and conversation
protections remain.

For future PRs, inspect Codex's current-head review and address findings before
merge. Any exception requires explicit owner authorization and a linked deferral;
never label it a clean review. The #35/#37 exception is specific to this delivery.
Ticket acceptance is checked separately by the shipping agent.

## Request and evidence

Request review as a repository owner, member or collaborator, using a new,
unedited comment containing exactly the request below (substitute the full current
SHA). Incidental mentions and outsider comments are not authoritative requests:

```
@codex review
<!-- codex-review-head:FULL_40_CHARACTER_HEAD_SHA -->
```

The gate requires this commit-bound request, a fresh completed Code Review summary
from the verified Codex bot (GitHub user ID 199175422), the matching summary commit,
a +1 reaction from that bot on the request (or its explicit, unedited clean-result
comment identifying the current commit), and no unresolved review threads. The
explicit-result path also supports existing unedited review requests. Later
requests or findings invalidate an older clean result. Review edits use GraphQL
update timestamps; inline comments are checked separately, including resolved
threads whose comments were later edited.
An old clean review, edited request, human reaction, unknown summary format or
missing evidence leaves the check pending. Re-request review after changes.

The informational commit status is **Codex review**. It shows a pending indicator and
short reason while reviewing; success means the evidence conditions passed. It is
not a percentage progress bar. Its Details link opens the Actions run that
inspected the evidence, with logs and a readable summary. PR test runs also
inspect live evidence with a read-only token; their green job result means the
inspection ran, not that Codex approved. The separate workflow refreshes evidence on PR and
comment events, a read-only review-event relay, manually, and approximately every five minutes to catch
reactions and resolved threads (GitHub scheduling may be delayed).

## Trust and operations

The write-enabled workflow uses pull_request_target, default-branch issue_comment,
schedule, manual and default-branch workflow_run events. Review submissions,
edits and dismissals trigger a separate permissionless relay; the receiver reads
fresh GitHub evidence and never trusts relay artifacts or executes its code. It executes only the protected default branch's gate code,
never pull-request code. It does not install PR dependencies or interpolate PR
content into shell commands. Evidence is paginated with bounded cursors. A failure
in one PR does not abandon the others: affected commit groups stay pending and
the workflow fails. PRs sharing a SHA are evaluated together; all must pass,
including when using a scoped refresh. Head and draft state are checked again
after inspection. New SHAs require their own success.

Publication occurs only when state or reason changes, avoiding GitHub's limit of
1,000 statuses per SHA/context. The Details link therefore identifies the last
status transition; unchanged refreshes are available in Actions. If GitHub cannot
list PRs or accept a status write, the workflow fails but cannot erase an old
status remotely. The shipping agent must require a successful fresh refresh and
recheck current-head evidence before merging. Events and API reads are snapshots,
not an atomic lock against a concurrent review. Broader UI/protection enforcement
is tracked separately in #38. The protocol adapter is
fail-closed because Codex's summary format can change. Unit tests cover spoofed,
stale, edited and incomplete evidence. Separate read-only CI tests PR changes.

Required-status enforcement, safe PR-specific approval and recovery behaviour
are deferred to #38. The current status must not be used as the sole authorization
to merge: a new PR can inherit an old status attached to the same SHA. Refer to
current review evidence and the owner's explicit delivery authorization instead.
The reporter does not merge PRs. No admin bypass is used.

## Review service recovery — 19 September 2026

Review activity has resumed: #153 has a completed Codex summary and a subsequent
explicit result identifying merge commit 2c083d0. Its PR head was aa86869, so do
not conflate those revisions or claim this proves pre-merge approval. The prior
date-bound outage instruction is retired. Apply the normal current-head evidence
protocol above to every new PR; the former owner exception is not standing merge
authorization. #38 still owns safe enforced review gating.

## Review carry-forward for a pure main sync

Owner-authorized on 20 September 2026. This is a manual merge exception, not a
claim that reviewers reviewed the new head. Automation belongs to #38. All of the
following must hold; otherwise request fresh current-head review:

1. Record the previously reviewed head R and its merge base B with main. Both
   Codex and CodeRabbit completed review of R, with links to actual results and
   no unresolved blocking findings. Preserve any authorized non-blocking deferrals.
2. Record incorporated main revision M and verify its applicable review/CI
   evidence. Main ancestry alone does not prove that M was reviewed. Every change
   incorporated since B must have review evidence; missing evidence fails closed.
3. The new head H is a single, conflict-free merge with exactly two parents, R
   first and M second. No rebase, squash, manual resolution or additional edits.
   Worktree and index must be clean before the merge. Reconstruct the merge with
   `git merge-tree --write-tree R M`: it must succeed without conflicts and its
   tree must equal `git rev-parse H^{tree}`.
4. Compare `git diff --binary --full-index B R` with
   `git diff --binary --full-index M H`. Require identical output, including
   paths/modes; do not rely only on patch-id or a diff summary. A mismatch or
   unsupported comparison means fresh review, not a relaxed comparison.
5. Inspect the incoming main changes for interactions with the PR, including
   dependencies, configuration, callers and contracts. Unchanged patch text alone
   does not prove unchanged behavior. Any material interaction or uncertainty
   requires fresh review. Record this as self-review, not external approval.
6. Required CI passes on H and branch protection permits the merge. Recheck main,
   head, reviews and unresolved threads immediately before merging. A further
   change invalidates this evidence. Never bypass protection to use this exception.

Start the comment with plain English: what changed, which checks passed, and
what still blocks merge. Put technical evidence inside a collapsed `<details>`
section with descriptive labels; never lead with unexplained letters or hashes.
Publish one evidence comment on the same PR with R/B/M/H full SHAs, original
review links, incorporated-main evidence, merge-tree and exact-diff comparison
results, interaction assessment, current-head CI links and retained deferrals.
Label the decision **Owner-authorized review carry-forward; H not externally
reviewed**. Do not request another paid review solely for this verified sync.
Do not fabricate or change the informational Codex status to success; it may stay
pending. If that status becomes required, this manual exception cannot bypass it.

The ordinary exact-head protocol remains the default. Already-running automatic
reviews are not cancelled or claimed to be prevented by this policy. This policy
change itself requires normal current-head review; it cannot approve itself.

## Automated dependency exception

The owner-authorized [Dependabot policy](dependabot.md) allows eligible dependency-only
npm/uv patch and minor PRs to receive automated policy approval and protected
auto-merge without per-PR Codex review. Other PRs retain the normal review rules.
Bot PRs retain upstream titles; VIN-172 tracks the policy.

## Consolidated review guidance

Root AGENTS.md's Review guidelines section supplies repository instructions to
Codex Code Review. This is the supported reviewer customization surface, not a
new skill the connector must be assumed to invoke. See [OpenAI's custom review
rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex).

The goal is one complete related-area pass with root-cause grouping, not guaranteed
single-round approval. These instructions cannot change the hosted service's
internal budget, enforce exhaustive coverage or convert comments into approval.
Use the next authorized representative PR to assess grouped findings, a safe
counterexample and unrelated changes; record observed behavior on VIN-190. Do not
launch extra paid reviews solely to claim this policy is tested. Until observed,
reduced review rounds remain an intended benefit, not verified performance.
