---
name: ecommerce-pr-ownership
description: Set and verify the owner's assignment and appropriate labels when opening or repairing pull requests in this ecommerce repository.
---

Use ecommerce-naming for branch, commit, and PR naming before creation.

The repository owner is youneshenniwrites. Before opening an agent-authored PR,
verify `gh api user --jq .login` is that account so GitHub attributes authorship
correctly. If a different account is authenticated, use an already-authorized
owner connection or report the mismatch; never falsify authorship or rewrite history.
Existing bot/contributor PRs retain their real authors.

Use .github/pull_request_template.md as the canonical description structure:
Summary, Issue, optional Before / After, Acceptance criteria, Testing, Review,
and optional Deployment / Compatibility. Fill it with actual evidence; remove
unused optional sections. Link real issues and never pre-check unverified review
or test claims. Use this structure when maintaining bot PRs, preserving useful
upstream release information.

After creating a PR, choose labels that describe its actual scope: bug,
enhancement, documentation, tooling, dependencies, github_actions, or docker.
Apply assignment and labels from the repository root:

```sh
python3 .agents/skills/ecommerce-pr-ownership/scripts/set_metadata.py PR_NUMBER --labels documentation tooling
```

Replace PR_NUMBER with the actual number and select the relevant labels. The
helper uses additive REST operations, preserves other assignees/labels, and reads
back the result. `--dry-run` reads the PR and prints intended changes without
writing. Re-running it is safe if a previous call only partially succeeded.

Verify author, assignee, and labels before handing off a PR. CODEOWNERS expresses
code-review ownership; it does not assign PRs or make an author's own review an
independent approval. Follow root review/CI/merge instructions separately.

Follow docs/delivery.md for issue linkage and board status. Include a GitHub issue
reference. At merge, verify acceptance criteria before issue
closure/Done, and record any remaining work instead of implying completion.

## Reviewer requests

Assign the owner on every PR, but do not request their review. Codex is the sole
requested reviewer; ownership and reviewer requests are separate.
Request Codex Code Review using its configured integration (or @codex review
comment). Listing Codex in the PR body is not a request. Inspect existing review
activity before posting to avoid duplicate requests; request a new review when
code changes invalidate the reviewed head. Verify the actual bot response and
reviewed commit. Do not assume the integration bot is a requestable GitHub user.

External review and approval are required before merge. Follow docs/codex-review.md:
post a fresh commit-bound request, verify the trusted bot's clean result for the
current head and all resolved threads, and require the Codex review status plus
CI. Verify ticket acceptance separately. No human Approve review is required.
Self-review and CI alone are insufficient. Missing evidence keeps the PR open.
Never bypass protection. After pushing, publish a pending Codex review status if
the workflow has not yet run; never publish success without the evidence adapter.
