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

Use the PR template for a readable description: summary, Jira ticket, validation,
and compatibility/operations. Include the real Jira key/link if provided; otherwise
write "No Jira ticket." Never invent an issue or imply one is attached.

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
reference separately from Jira. At merge, verify acceptance criteria before issue
closure/Done, and record any remaining work instead of implying completion.
