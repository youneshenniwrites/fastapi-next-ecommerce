---
name: ecommerce-pr-ownership
description: Set and verify owner assignment, scope labels, the linked issue's priority and milestone, and a ready-for-review pull request. Never leave a pull request in draft.
---

Select the reviewer before taking review actions: verified Dependabot PRs follow
[dependency policy](../../../docs/dependabot.md); eligible routine documentation
follows the [documentation exception](../../../docs/codex-review.md#routine-documentation-review-exception-vin-225).
Dependabot and other non-exempt PRs use Codex within the existing subscription
allowance. Only eligible routine documentation uses CodeRabbit without Codex
requests or statuses. Reclassify the complete diff after changes; mixed and
agent-policy changes require Codex.

Use ecommerce-naming for branch, commit, and PR naming before creation.

The repository owner is youneshenniwrites. Before opening an agent-authored PR,
verify `gh api user --jq .login` is that account so GitHub attributes authorship
correctly. If a different account is authenticated, use an already-authorized
owner connection or report the mismatch; never falsify authorship or rewrite history.
Existing bot/contributor PRs retain their real authors.

Use .github/pull_request_template.md as the canonical description structure:
Issue/Problem opening, Summary, optional Before / After, Acceptance criteria, Testing, Review,
and optional Deployment notes. Lead with the customer or contributor outcome,
derive acceptance criteria from the issue, but include only observed, verified
deliverables in the PR checklist. Never tick unverified outcomes or add unchecked
future work. Put pending CI/review in Review and genuine post-merge verification
in Deployment notes. Keep every unfulfilled ticket criterion open on its source
issue with its proving PR/event and next action. Use Refs for partial delivery;
use Closes only when the ticket is fully completed. Do not hide unfinished scope
or relabel an unverified implementation outcome as post-merge work to make the
checklist appear complete. Follow the canonical
[PR writing standard](../../../docs/delivery.md#human-readable-pr-writing): report actual
results in plain English and preserve the tested commit in linked or collapsed evidence.
Keep Review to a brief self-review disclosure and links to current-head external
review and CI evidence, explicitly noting pending or failed results. Remove
unused optional sections. Keep owner assignment and labels in the sidebar; do
not duplicate them or add review checkboxes to the body. Link real issues and
never claim unverified review or test success. Use this structure when maintaining bot PRs, preserving useful
upstream release information.

Open every pull request ready for review. Never create one as a draft, and never
convert a ready pull request back to a draft, including when the creation tool
defaults to draft. A draft is not a handoff. Do not add the pull request to the
project board; the linked issue card is the only board item.

After creating a PR, choose labels that describe its actual scope: bug,
enhancement, documentation, tooling, dependencies, github_actions, or docker.
Apply assignment, those scope labels, and the linked issue sidebar from the
repository root:

```sh
python3 .agents/skills/ecommerce-pr-ownership/scripts/set_metadata.py PR_NUMBER --labels documentation tooling
```

Replace PR_NUMBER with the actual number and select the relevant scope labels.
The helper links the issue from the PR title's `[VIN-N]` key, otherwise from
Closes/Fixes/Resolves, otherwise from Refs. It assigns youneshenniwrites, adds
the scope labels plus every `priority:` label on that issue, and sets the
issue's milestone on the pull request. It does not invent a priority or
milestone when the issue has none. Adding assignees and scope labels keeps
people and scope labels already on the pull request. If adding the assignee is
rejected, the fallback update sends the people already assigned plus the owner.
A later run matches the linked issue again: it clears a milestone the issue no
longer has, and removes a `priority:` label the issue no longer has. It does
not send a milestone update when the pull request already matches, including
when both are empty. The helper
reads the sidebar back. `--dry-run` reads the PR and prints intended changes
without writing. Re-running it is safe if a previous call only partially succeeded.

Verify author, assignee, scope labels, priority labels, and milestone before
handing off a PR. A pull request that is still a draft, or that is missing the
linked issue's milestone or `priority:` label, is incomplete. CODEOWNERS expresses
code-review ownership; it does not assign PRs or make an author's own review an
independent approval. Follow root review/CI/merge instructions separately.

Follow docs/delivery.md for issue linkage and board status. Include a GitHub issue
reference. At merge, verify acceptance criteria before issue
closure/Done, and record any remaining work instead of implying completion.

## Reviewer requests

Assign the owner on every PR, but do not request their review. For routine documentation PRs, apply [the documentation exception](../../../docs/codex-review.md#routine-documentation-review-exception-vin-225): require current-head CodeRabbit approval and resolved findings, without requesting Codex. Check actual changed files; agent-policy and mixed changes retain Codex. For other human-authored PRs, Codex is the
requested reviewer; ownership and reviewer requests are separate.
### Only for PRs classified as requiring Codex

Request Codex Code Review using its configured integration (or @codex review
comment). Listing Codex in the PR body is not a request. Inspect existing review
activity before posting to avoid duplicate requests; request a new review when
code changes invalidate the reviewed head. Verify the actual bot response and
reviewed commit. Do not assume the integration bot is a requestable GitHub user.

For these Codex-reviewed PRs, external review is required before merge. Follow docs/codex-review.md:
post a fresh commit-bound request, verify the trusted bot's clean result for the
current head and all resolved threads, and require CI. The clean result is the
trusted whole comment: the fixed opening sentence, one short signoff of at most
80 characters or one `:token:` such as `:+1:`, and the reviewed commit. It is
not a fixed word list. Finding words, a second sentence, and the wrong commit
stay pending. The Codex review status
is informational pending #38; any owner-approved exception must be explicitly
recorded and linked to deferred work. Verify ticket acceptance separately. No human Approve review is required.
Self-review and CI alone are insufficient. Missing evidence keeps the PR open.
Never bypass protection. Only for these non-exempt PRs, after pushing publish a pending Codex review status if
the workflow has not yet run; never publish success without the evidence adapter.

The exact-head review instructions above have one exception: the owner-authorized
[pure-main-sync carry-forward procedure](../../../docs/codex-review.md#review-carry-forward-for-a-pure-main-sync).
Apply every evidence and CI condition before omitting a repeat review; all other
changes require current-head review. This does not waive branch protection.

For verified Dependabot PRs, follow [dependency policy](../../../docs/dependabot.md): trusted continuation requests Codex on the current head and approves/merges only after verified clean review evidence, resolved findings and CI. Avoid duplicate manual requests; missing review or exhausted allowance keeps delivery pending.
