# Visible Codex reviews in GitHub Actions

This optional workflow uses the official `openai/codex-action`, pinned to a full
commit. It is separate from the existing hosted `@codex review` integration.
It runs a new review; it cannot expose an existing hosted review session.

## Enable and run

1. Configure OPENAI_API_KEY under repository Settings → Secrets and variables →
   Actions. Use an OpenAI API project with an appropriate usage budget. Do not
   paste credentials in issues, PRs or chat. A ChatGPT subscription is not an API key.
2. After this workflow is merged, open Actions → Codex Actions review → Run workflow.
   Select the default branch and supply an open, non-draft PR number.
3. Open **Codex · Prepare and review PR**, then **Run Codex review** to inspect
   execution output. The separate publishing job links the report to that run.

The action emits available JSON events/tool output and a final review. This is not
access to hidden model reasoning or a percentage progress indicator. A missing
credential or failed review fails the job; a head change prevents publication.
A successful job means execution completed, not that the findings are clean.
Reports are informational; the existing current-head external review policy still
applies. Automatic triggering or replacement of that policy follows a verified
live trial, not this initial manual rollout. Protection enforcement remains #38.

## Boundaries

The workflow runs only from the default branch. It keeps trusted configuration
checked out, fetches immutable base/head Git objects, and reviews a diff without
executing PR code. Codex runs read-only with sudo dropped and a read-only GitHub
job token; only the separate publisher receives PR write permission. GitHub-hosted
runners are used. No session directory, credentials or raw transcript artifacts
are uploaded. Review output is visible in Actions and the PR; never include real
customer data in test fixtures. GitHub retains logs according to repository settings.

The action version is pinned; its CLI version defaults to the action's selected
version and should be recorded during the live trial. No live execution is claimed
until OPENAI_API_KEY is configured and a run succeeds.

References: [official guide](https://learn.chatgpt.com/docs/github-action) and
[existing review policy](codex-review.md).
