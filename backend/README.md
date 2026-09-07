# Backend

Python 3.12, FastAPI, SQLAlchemy 2, and PostgreSQL. Dependencies are declared in
`pyproject.toml` and resolved in `uv.lock`. Install with `uv sync --locked`.
`requirements.txt` is a generated, runtime-only compatibility export; do not edit it.

Run checks from this directory:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Tests use a fresh in-memory SQLite database for each test and need no `.env` or
external database. PostgreSQL migration/integration coverage is a follow-up.

For the server, configure `DATABASE_URL` (use `postgresql+psycopg://` for PostgreSQL)
and a random `SECRET_KEY` of at least 32 characters, then run:

```sh
uv run uvicorn app.main:app --reload
```

Database migrations and container startup are not implemented yet. Do not treat
this backend as a production-ready shop. Cart, orders, payments, and frontend
remain planned work.

Registration returns 201. Login accepts form fields `username` (email) and
`password`; use its bearer token for `/api/v1/auth/me`. Product reads are public;
product writes require an active user whose `is_superuser` flag is true. Signup
never grants admin privileges. There is currently no admin bootstrap command.

New passwords use Argon2. Existing bcrypt hashes upgrade after a successful
login. The JWT implementation now requires `sub`, `iat`, and `exp`; tokens issued
by an older version without these claims require a new login.

To refresh the pip compatibility export after changing dependencies:

```sh
uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt
```
