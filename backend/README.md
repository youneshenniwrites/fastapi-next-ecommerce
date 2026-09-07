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
external database. Container CI also runs a real PostgreSQL registration/login smoke test and checks
migration upgrade, rollback, and metadata consistency.

For the server, configure `DATABASE_URL` (use `postgresql+psycopg://` for PostgreSQL)
and a random `SECRET_KEY` of at least 32 characters, then run:

```sh
uv run uvicorn app.main:app --reload
```

From the repository root, `make dev` generates configuration and starts the full
local backend stack. On the host, `uv run alembic upgrade head` applies migrations.
The old `python -m app.db.init_db` command now delegates to Alembic.

The initial migration targets an empty database. If an existing unversioned database
contains tables, back it up and compare its schema before deciding whether to stamp
the baseline. Never blindly stamp or drop an existing database to bypass errors.

Cart, orders, payments, and frontend remain planned work.

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
