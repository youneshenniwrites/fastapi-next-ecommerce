# Backend conventions

Routes in app/api/v1 handle HTTP parsing and responses. Authentication dependencies
live in app/api/deps.py. As commerce grows, domain services coordinate business
transactions and CRUD helpers perform database operations. Provider adapters handle
payments/email. Do not introduce a new abstraction without a concrete caller.

Use Pydantic v2 request validation and SQLAlchemy 2. Migrations must match model
metadata (`alembic check`). Production startup must not use metadata.create_all.
SQLite fixtures are fast behavioral checks; the container CI job proves PostgreSQL
startup, migrations, registration/login, and denied product writes.

JWT subjects are strings. Reject disabled users at login and on protected requests.
Product reads are public; writes require require_admin. Signup cannot grant admin
status. New password hashes use Argon2; legacy bcrypt verification remains until a
separate migration decision removes it. Never log passwords or bearer tokens.

Run `make check` at repository root. Changes to migrations, dependencies, startup,
or containers also require the container CI job to pass. Do not mutate an applied
migration once main contains it; add a new revision. The initial migration targets
empty databases; existing unversioned databases require schema comparison first.

Product money uses Decimal / NUMERIC(12, 2), serializes as a two-place string, and
is GBP-only. Preserve the partial PUT contract and reject null required fields.
See docs/decisions/0001-product-money.md from the repository root for the decision.
Dependency updates must pass make requirements-check and make audit. CI enforces
an 85% coverage minimum; tests are not a substitute for PostgreSQL migration checks.
