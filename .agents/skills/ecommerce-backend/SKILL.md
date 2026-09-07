---
name: ecommerce-backend
description: Implement FastAPI endpoint, authentication, persistence, or commerce changes using this repository's validation and transaction conventions.
---

Read backend/AGENTS.md. Find the route, Pydantic schemas, model, CRUD helpers, and
existing tests for the behavior. Use authentication dependencies in app/api/deps.py;
never duplicate token parsing in endpoints. Check anonymous, customer, admin, and
disabled-user behavior where permissions change.

For a future checkout operation, place transaction ownership in a domain service;
CRUD helpers participating in it must not commit independently. Calculate totals
from server-side product data and store order-item price snapshots. Monetary and
stock constraints need database enforcement as well as Pydantic validation.

Add an Alembic revision for model changes. Test upgrade on an empty database,
metadata consistency, and relevant data migration paths. Use the disposable CI
stack for PostgreSQL checks. Do not stamp or downgrade an existing user database.

Run make check; require container CI for database or startup changes. Regenerate
OpenAPI-derived frontend types when that frontend has been introduced.
