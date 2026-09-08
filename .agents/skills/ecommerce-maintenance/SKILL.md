---
name: ecommerce-maintenance
description: Handle dependency-update PRs, quality-tooling changes, and maintenance documentation in this ecommerce repository.
---

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
updates; the agent still reviews the exact head and follows the owner's merge
instructions. Do not activate the legacy AWS workflow during maintenance.

When documenting tooling, name the executable command, what it verifies, and its
limits. Keep the runnable catalog distinct from planned authentication and checkout. Keep
README, development/tooling docs, and relevant agent guidance consistent. Validate
new skill metadata and local links. Report self-review honestly and avoid claiming
production readiness from coverage or vulnerability-audit results alone.
