---
name: release-readiness
description: Pre-deploy readiness check for the ecommerce demo — environments, migrations, secrets, CI gate, smoke, Sentry and rollback — before any release.
---

Read root AGENTS.md, [delivery policy](../../../docs/delivery.md) and the
[environment plan](../../../deploy/environments/README.md) first. Invoke this
skill before any development or production release; it gates the release, it
does not authorize deployment. Cloud provisioning needs its own agreement on
environment, budget, secrets design and rollback.

Verify each gate against the approved hosts — Vercel Hobby for Next.js and
FastAPI, Neon Free for PostgreSQL, with isolated development and production
resources. Azure is optional future work, the legacy AWS Terraform is not a
deployment path, and no paid upgrades are authorized:

- Environments: development and production configs isolated; each env points
  at its own database URL, secret key, API base URL and Sentry DSN.
- Migrations: Alembic upgrade applied and metadata-checked before the API
  deploys; the API deploys before the frontend.
- Secrets: server-only values in secret stores, never in code, client
  bundles or browser variables; local credentials stay in the ignored file.
- CI gate: the exact revision passed all applicable checks before release.
- Smoke: public endpoints verified after deploy (storefront, health, docs,
  contract) plus the auth and catalog journey on fictional data.
- Observability: per-environment Sentry DSNs active; errors visible before
  traffic is expected.
- Rollback and recovery: known previous good revision, database restore
  path with written RTO/RPO where applicable, and a production checklist
  recording who approved, what was verified and the next unblocked step.

Report each gate pass or fail with evidence; a failed gate blocks the release
until fixed and re-verified. Record the outcome in the tracking issue with the
tested revision. This skill never invents a hosted endpoint, test result or
deployment.
