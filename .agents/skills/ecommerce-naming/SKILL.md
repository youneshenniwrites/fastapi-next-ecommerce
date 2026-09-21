---
name: ecommerce-naming
description: Name ecommerce task branches, commits, PR titles, and squash commits using issue aliases and Conventional Commits.
---

Read the Naming conventions section of CONTRIBUTING.md before creating a branch,
commit, or PR, and again when finalizing its title for merge. It is the canonical
policy, including the local branch adaptation and examples.

Choose names from the actual final change, not the agent identity. Never create
an agent/ branch. Preserve existing bot branch names and real authorship when
maintaining Dependabot PRs. Do not rewrite merged history to apply this policy.

Before pushing, inspect git status, the branch name, and the commit subjects.
For non-Dependabot PRs, use `[VIN-N] [type] Description` for titles and link the actual GitHub issue
as `**Issue:** [VIN-N — Issue title](issue-url)`. Follow with Closes/Refs and a
separate **Problem:** line; do not repeat an Issue section. N is the issue
number; PR identifiers remain `PR #N`.
Before merge, read back the PR title and explicitly pass a separate Conventional
Commits subject to `gh pr merge --squash --subject`, including the VIN-N alias.
Do not use the VIN-prefixed PR title as the squash commit subject.
Retain exact-head CI and review requirements from AGENTS.md. If scope changes,
update the PR title to describe the final diff; branch names need not be renamed
solely for a minor scope adjustment. Use the ownership skill for assignment/labels.

When creating or refreshing a Dependabot PR, preserve its upstream title under
the VIN-172 exception. Do not rename it to the manual PR format. Commits and
squash subjects still use Conventional Commits.
