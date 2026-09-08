# Automated Codex review gate

The owner's accepted approval signal is a completed clean Codex review of the
latest commit with every review thread resolved. A human Approve review is not
required once this gate is installed and required in branch protection. CI remains
mandatory. Ticket acceptance still requires implementation evidence checked by the
shipping agent; this gate does not infer task completion from resolved comments.

## Request and evidence

Request review using a new, unedited comment (substitute the full current SHA):

```
@codex review
<!-- codex-review-head:FULL_40_CHARACTER_HEAD_SHA -->
```

The gate requires this commit-bound request, a fresh completed Code Review summary
from the verified Codex bot (GitHub user ID 199175422), the matching summary commit,
a +1 reaction from that bot on the request (or its explicit, unedited clean-result
comment identifying the current commit), and no unresolved review threads. The
explicit-result path also supports existing unedited review requests. Later
requests or findings invalidate an older clean result.
An old clean review, edited request, human reaction, unknown summary format or
missing evidence leaves the check pending. Re-request review after changes.

The required commit status is **Codex review**. It shows a pending indicator and
short reason while reviewing; success means the evidence conditions passed. It is
not a percentage progress bar. The separate workflow refreshes evidence on PR and
comment events, manually, and approximately every five minutes to catch
reactions and resolved threads (GitHub scheduling may be delayed).

## Trust and operations

The write-enabled workflow uses pull_request_target, default-branch issue_comment,
schedule and manual events. It executes only the protected default branch's gate code,
never pull-request code. It does not install PR dependencies or interpolate PR
content into shell commands. Evidence is paginated; API failures abort evaluation
with a pending status. New SHAs require their own success. The protocol adapter is
fail-closed because Codex's summary format can change. Unit tests cover spoofed,
stale, edited and incomplete evidence. Separate read-only CI tests PR changes.

Protect main with this required status plus normal CI, up-to-date branches and
resolved conversations. Do not remove an existing approval requirement until the
replacement has been tested and its current-head success verified. Bootstrap may
run the reviewed gate locally with gh credentials to publish a real evidence-backed
status; it must not fabricate a pass. After installation, use workflow_dispatch
for recovery, and inspect the workflow failure before retrying. Missing clean bot
signals require investigation, never an assumed approval.

The gate does not merge PRs itself. The shipping agent verifies ticket acceptance,
all required checks and current-head evidence before merging. No admin bypass.
