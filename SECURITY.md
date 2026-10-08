# Security policy

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/youneshenniwrites/fastapi-next-ecommerce/security/advisories/new).
Private reporting is enabled for this repository. Avoid public issues or PRs that
expose an exploitable vulnerability before it has been assessed.

Include the affected revision, reproduction steps using synthetic data, expected
and observed behavior, impact, and any proposed mitigation. Do not submit live
passwords, access tokens, payment details, or customer records. If a credential
was exposed, revoke/rotate it through the owning service and redact it from reports.

There is no promised response SLA or bug bounty. This project is under development;
main is the maintained branch and there are no supported production release lines yet.

## Implemented controls and limits

The API validates JWT claims, rejects disabled accounts, restricts product writes
to active admins, hashes new passwords with Argon2, and upgrades legacy bcrypt
hashes on login. Product constraints are enforced at API and database boundaries.
Local credentials are generated into an ignored file and excluded from Docker builds.

CI audits locked Python and frontend dependencies, validates code/tests, and checks
PostgreSQL migrations. The owner-approved, development-only VIN-269 audit exception
is [bounded and expires on 17 October 2026](docs/tooling.md#temporary-vin-269-tooling-exception--expires-17-october-2026); it is accepted risk, not remediation.
Rate limiting is implemented with process-local counters; it is not a distributed
limit across serverless instances. Password recovery, full security scanning and
production hardening remain roadmap work. These checks do not prove production
readiness. The health endpoint checks process liveness, not database readiness.

Do not deploy the legacy AWS Terraform as part of this project's current roadmap.
Vercel Hobby and Neon Free are the demo targets; see deploy/environments/README.md.
