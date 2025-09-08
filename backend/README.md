## Backend Directory Structure

```text
backend/
├── alembic/                 # DB migrations (Alembic)
│   ├── versions/            # Migration files
│   └── env.py
│
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point (FastAPI instance, routers, middleware)
│   ├── config.py            # Settings (env vars, loaded via Pydantic/Secrets Manager)
│   │
│   ├── api/                 # API layer (routes/endpoints)
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependencies (auth, db session, pagination, etc.)
│   │   ├── v1/              # Versioned APIs
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── cart.py
│   │   │   ├── orders.py
│   │   │   └── users.py
│   │
│   ├── core/                # Core app config & security
│   │   ├── __init__.py
│   │   ├── security.py      # JWT, password hashing, OAuth2 schemes
│   │   ├── logging.py       # Logging config (integrate Sentry, CloudWatch)
│   │   └── settings.py      # Pydantic BaseSettings (env vars)
│   │
│   ├── db/                  # Database layer
│   │   ├── __init__.py
│   │   ├── session.py       # SQLAlchemy session
│   │   ├── base.py          # Base class for models
│   │   └── init_db.py       # Seeding, initial setup
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── cart.py
│   │
│   ├── schemas/             # Pydantic models (request/response validation)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── cart.py
│   │
│   ├── crud/                # DB interaction functions (CRUD ops)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── cart.py
│   │
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── payments.py      # (Stripe/PayPal integration)
│   │   ├── email.py         # Email sending (SES)
│   │   └── cache.py         # Redis caching
│   │
│   ├── tests/               # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py      # pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   └── test_orders.py
│   │
│   └── utils/               # Small helpers
│       ├── __init__.py
│       ├── hashing.py
│       ├── pagination.py
│       └── datetime.py
│
├── .env                     # Local env vars (NEVER commit to git)
├── alembic.ini              # Alembic config
├── Dockerfile               # Docker image for backend
├── docker-compose.yml       # Local dev (backend + db + redis)
├── pyproject.toml            # Dependencies (poetry/pip)
├── requirements.txt          # (alt to poetry)
└── README.md
```
