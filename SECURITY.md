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

CI audits locked Python dependencies, validates code/tests, and checks PostgreSQL
migrations. These checks do not prove the app is ready for production. Rate limiting,
password recovery, browser session design, full security scanning, and Azure
production hardening remain roadmap work. The health endpoint checks process
liveness; it is not a database-readiness or security assessment.

Do not deploy the legacy AWS Terraform as part of this project's current roadmap.
Azure is the selected target, but no Azure deployment is provisioned.
