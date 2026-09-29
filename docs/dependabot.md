# Dependabot maintenance (VIN-172)

VIN-38 replaces Codex review for verified Dependabot PRs with CodeRabbit review.
The owner approved this policy on 29 September 2026. Human-authored PRs retain
Codex review. Every eligible dependency PR requires CodeRabbit's current-head
`APPROVED` review, no unresolved review findings, and applicable CI before an
Actions approval and SHA-bound protected squash merge. A comment, reaction or
compliment is not approval. Missing, stale or contradictory review evidence blocks
merging; the automation does not infer approval from prose.

This supersedes the Codex-reviewed policy introduced by PR #214 and the older
patch/minor policy-only exception. Rollout and live proof remain pending until
recorded on VIN-38 and VIN-172; merging a PR manually is not proof of autonomy.
No paid API or scheduled Codex chat is configured.

## Continuation

Same-repository, non-draft Dependabot PRs targeting main qualify, including Actions
updates and major versions. Bot PRs retain upstream titles and authorship. Human
repair commits do not pretend to be Dependabot commits and still need review.

The initial workflow and continuation share a serial queue. Completion of CI/review
workflows, main pushes and manual dispatch recheck live evidence. Gate completions
include the existing five-minute polling, which provides recovery when
review evidence changes without another CI completion. Reducing unchanged polling runs is deferred to VIN-147; this is GitHub
Actions continuation, not a scheduled Codex chat or repeated review request. Each run examines
at most 30 candidates and makes at most one branch update, export repair or merge.
Pending work keeps its place; explicit failures remain open while other candidates
can proceed. There is no permanent auto-merge authorization or administrator bypass.
GitHub receives the expected head SHA and enforces branch protection.

The workflow updates an outdated branch before requesting review, waits for CI,
and requests CodeRabbit review once per revision when needed. It checks current evidence and CI again immediately before
merging, and withdraws its own approvals when their supporting evidence is stale
or delivery cannot proceed. Existing approvals are checked across the bounded
queue even when an earlier candidate is still pending. Missing credentials, unknown review evidence, conflicts and genuine test
failures prevent delivery. It cannot automatically repair arbitrary incompatibilities;
those require a code change and fresh review. A clean review is not proof that every
possible defect was found.

## Trusted Python export repair

Dependabot manages pyproject.toml and uv.lock; requirements.txt is excluded from
independent pip updates. For eligible Python-only changes, trusted main code reads
bounded regular dependency files through GitHub's API and generates the runtime
export with pinned uv 0.8.22, offline and without installing dependencies. Only
registry declarations and public PyPI artifacts are accepted. Custom build, uv,
workspace and source configuration are rejected.

The subprocess receives no GitHub credentials. The workflow never checks out or
executes PR code or consumes PR artifacts. A repair changes only requirements.txt,
is parent-bound to the inspected head and uses a non-forced ref update. CI and
CodeRabbit must approve the repaired revision. Lock/manifest inconsistencies that cannot
be exported safely remain visible failures; the requirements check stays enabled.

## Credential and repository configuration

Enable **Allow GitHub Actions to create and approve pull requests**. Keep default
workflow permissions read-only. Store `DEPENDABOT_REVIEW_TOKEN` as a repository
Actions secret: a fine-grained token restricted to this repository, with Contents
and Pull requests read/write and the required read-only Metadata permission.
No administration or protection-bypass permission is needed.

The member token requests CodeRabbit reviews, updates branches, publishes generated
exports and merges. Unlike the built-in Actions token, these events can trigger
normal CI and main deployment workflows. The built-in token records the approval.
The privileged jobs run trusted main code with checkout credentials disabled.

The credential provisioned on 28 September expires on **28 October 2026**. Rotate
it in the repository secret before expiry; never record its value in a ticket,
log or source file. Missing/expired credentials require renewal, not bypassing
review. Dependabot-triggered events may lack the repository secret; the trusted
completion workflow provides continuation with that secret.

Enable CodeRabbit automatic review for Dependabot and its request-changes/approval
workflow (`reviews.request_changes_workflow: true`). Approval must be a GitHub
review bound to the current commit, not an optimistic summary. See the
[CodeRabbit configuration reference](https://docs.coderabbit.ai/reference/configuration).

Record the first live request, approval and protected merge on VIN-172 before
claiming this replacement automation is operationally verified. Script tests alone
are not hosted proof.

## Tracking

Keep bot PRs out of the engineering board; use GitHub's dependency PR list
(`is:pr is:open author:app/dependabot`). VIN-172 tracks maintenance and blockers.
Do not close updates merely to hide them. Historical PR #168 proved the previous
policy, not this replacement workflow.

Reference: [GitHub Dependabot automation](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/automate-dependabot-with-actions).
