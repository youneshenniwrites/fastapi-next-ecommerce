---
name: security-review
description: Adversarial security pass over an ecommerce change, reporting severity, location, trigger and consequence without expanding scope.
---

Read root AGENTS.md, [delivery policy](../../../docs/delivery.md),
[security policy](../../../SECURITY.md) and [backend conventions](../../../backend/AGENTS.md).
For session changes also read [customer sessions](../../../docs/design/customer-sessions.md).
Invoke this skill when the change touches authentication, sessions, permissions,
money, stock, checkout, PII, secrets, abuse, throttling or dependencies — not on every PR.

Assume the attacker controls all browser input: forged or expired tokens,
disabled-user sessions, cross-account IDs, null or out-of-range fields, and
replayed checkout or admin requests. Check each boundary against the
implemented controls, not against framework defaults:

- Sessions: string JWT subjects, disabled users rejected at login and on
  protected requests, HttpOnly same-origin cookies, exact origin checks,
  logout clearing the cookie. Review each cookie-authenticated
  state-changing request for CSRF defenses covering the implemented
  SameSite, origin-check, and any token controls.
- Privilege: product writes behind require_admin, signup cannot grant admin,
  no public route creates an admin.
- Money and inventory: server-owned prices, stock and future order totals;
  Decimal two-place GBP strings; Pydantic validation plus database enforcement.
- Injection: trace attacker-controlled strings to SQL, shell, template, HTML,
  and outbound-request sinks; verify parameterization and encoding beyond
  shape validation.
- Secrets and PII: never log passwords or bearer tokens; local credentials
  stay in the ignored file; no customer data in tests or seeds; report live
  vulnerabilities privately per the security policy.
- Abuse and payments: auth/write throttling behavior preserved; browser input
  never establishes payment state; dependency changes keep the lockfile export
  and audit green.

Follow [self-review](../self-review/SKILL.md) for modes and evidence: in a
review-only request report each finding with severity, location, trigger and
consequence without editing. During an authorized fix task, reproduce and fix
findings, add regression coverage and rerun relevant checks. Never publish an
exploitable vulnerability in an issue or PR before it is assessed.
