# 🏗️ Professional FastAPI Developer Checklist

A **Professional FastAPI Developer Checklist** — concise, one-page, and focused on production-ready practices. This checklist is a **developer reference** before production deployment.

## 1. Project Structure & Organization

- [ ] Modular structure (`app/routers`, `app/models`, `app/services`, `app/db`, `app/utils`)
- [ ] Separate `main.py` (entrypoint) from business logic
- [ ] Use **APIRouter** to organize endpoints by domain

---

## 2. Dependencies & Environment

- [ ] Use **virtual environment** (venv, Poetry, Pipenv)
- [ ] Pin dependencies for reproducibility
- [ ] Separate dev / staging / prod configs via `.env` or environment variables

---

## 3. Pydantic & Validation

- [ ] Use Pydantic models for request & response schemas
- [ ] Reuse shared schemas across endpoints
- [ ] Enable `orm_mode = True` for ORM responses

---

## 4. Database & ORM

- [ ] Use SQLAlchemy or Tortoise ORM
- [ ] Use async if endpoints are async
- [ ] Connection pooling configured properly
- [ ] Use Alembic for migrations
- [ ] Proper session management (`Depends` for DB session)

---

## 5. Security

- [ ] Hash passwords (bcrypt / passlib)
- [ ] Use OAuth2/JWT for authentication
- [ ] Validate inputs to prevent injections
- [ ] Enforce HTTPS in production
- [ ] Configure CORS policies

---

## 6. Performance

- [ ] Use `async` for I/O-bound operations
- [ ] Cache heavy queries (Redis, in-memory)
- [ ] Gzip compression enabled if needed
- [ ] Monitor DB connection usage

---

## 7. Error Handling & Logging

- [ ] Custom exception handlers
- [ ] Consistent API error responses
- [ ] Structured logging (logging module or structlog)
- [ ] Integrate Sentry / monitoring tools

---

## 8. Testing

- [ ] Unit tests for business logic
- [ ] Integration tests for endpoints (`TestClient`)
- [ ] Use pytest fixtures for DB setup/teardown
- [ ] Test edge cases and authentication

---

## 9. Documentation

- [ ] Use FastAPI auto docs (`/docs` & `/redoc`)
- [ ] Add docstrings and response models
- [ ] Keep docs in sync with code

---

## 10. Deployment & DevOps

- [ ] Dockerize app for consistent environments
- [ ] CI/CD: lint, test, build, deploy
- [ ] Separate dev/staging/prod environments
- [ ] Deploy behind reverse proxy / ALB / Nginx
- [ ] Monitor app health (Prometheus, Grafana, Sentry)

---

## 11. Best Practices

- [ ] Type hints everywhere
- [ ] Services separate from routes for testability
- [ ] Consistent API responses (status, message, data)
- [ ] Rate-limiting for public endpoints
- [ ] Reusable dependencies (`Depends`) for auth, DB, etc.
