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
