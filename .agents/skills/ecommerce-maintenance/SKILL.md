---
name: ecommerce-maintenance
description: Handle dependency-update PRs, quality-tooling changes, and maintenance documentation in this ecommerce repository.
---

Select the reviewer before taking review actions: verified Dependabot PRs follow
[dependency policy](../../../docs/dependabot.md); eligible routine documentation
follows the [documentation exception](../../../docs/codex-review.md#routine-documentation-review-exception-vin-225).
Dependabot and other non-exempt PRs use Codex within the existing subscription
allowance. Only eligible routine documentation uses CodeRabbit without Codex
requests or statuses. Reclassify the complete diff after changes; mixed and
agent-policy changes require Codex.

Read docs/tooling.md and CONTRIBUTING.md. Inspect the actual manifest, lockfile,
workflow, and open PRs before choosing an update; do not assume a green dependency
bot PR proves compatibility. Keep maintenance changes focused and reviewable.

For Python updates, use backend/pyproject.toml and uv.lock as authority. Regenerate
requirements.txt with the command in docs/development.md. Run requirements-check,
audit, normal tests, and coverage when affected; require the PostgreSQL/container
jobs for runtime, database, or image changes. Investigate audit network failures
separately from vulnerability findings without bypassing either check.

For action updates, verify the upstream commit corresponding to the intended
release and retain SHA pins with readable version comments. Dependabot proposes
updates; Codex reviews their exact head and trusted automation follows
the [dependency policy](../../../docs/dependabot.md). Avoid duplicate requests already made by continuation. Missing review or quota
exhaustion leaves delivery pending without a paid fallback. Do not activate the legacy AWS workflow during maintenance.

When documenting tooling, name the executable command, what it verifies, and its
limits. Distinguish implemented behavior from proposed work using the canonical plan. Keep
README, development/tooling docs, and relevant agent guidance consistent. Validate
new skill metadata and local links. Report self-review honestly and avoid claiming
production readiness from coverage or vulnerability-audit results alone.

Read docs/delivery.md and the maintenance decisions in docs/tooling.md. Resolve or
record a concrete next action for failing bot PRs during maintenance handoff. Do
not claim live autonomous delivery is proven without a recorded review, approval
and protected merge. GitHub continuation is separate from scheduled Codex chats.
