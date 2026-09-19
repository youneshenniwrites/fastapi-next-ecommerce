---
name: architecture-review
description: Structural review before large epics — component placement, coupling, transaction boundaries, API contracts and scalability — writing an ADR when warranted.
---

Read root AGENTS.md, [delivery policy](../../../docs/delivery.md),
[architecture](../../../docs/architecture.md) and the epic issue first. Invoke
this skill before large epics only — never per PR; per-PR review belongs to
[self-review](../self-review/SKILL.md) and [preflight-review](../preflight-review/SKILL.md).

Answer the placement questions from the repository's component rules: routes in
app/api/v1 handle HTTP parsing only, authentication dependencies live in
app/api/deps.py, domain services own multi-step transactions, CRUD helpers
perform database operations without committing inside another service's
transaction, provider adapters isolate payments and email. Do not introduce a
new abstraction without a concrete caller. On the frontend, routes compose in
src/app, shared UI lives in src/components, API access goes through
src/lib/api against regenerated OpenAPI types; credentials and monetary
decisions stay server-side and out of client bundles.

Check coupling, transaction boundaries, API contracts and scalability: who owns
permissions, money and inventory (FastAPI always does); whether totals and
snapshots are authoritative server-side; whether the OpenAPI contract and
generated frontend types must be regenerated together; whether migrations keep
metadata consistent without editing applied revisions; what breaks first at
ten times the load and what is deliberately left unscaled.

Write or update a numbered record under docs/decisions/ following the
established pattern when the epic sets a durable technical direction;
never rewrite an accepted decision to change its direction — a new
currency, for example, needs a new numbered record and PR, not an edit to
Decision 0001. Otherwise record the placement decision and rejected alternatives
in the epic issue. Architecture review does not authorize implementation, merge or
deployment.
