---

## **1️⃣ Backend Enhancements**

1. **Users & Authentication**

   * Create `User` model, schema, and CRUD.
   * Implement authentication:
     * JWT tokens
     * Password hashing
     * Login / signup endpoints
   * Add dependency to get `current_user` for protected routes.

2. **Orders & Cart**

   * Build models: `Order` and `Cart`.
   * CRUD endpoints for adding items to cart, viewing cart, and creating an order.
   * Integrate relationships: user → cart → order → products.

3. **Services Layer**

   * Start with email notifications and caching (Redis).
   * Implement payment service (Stripe sandbox) for orders.

4. **Validation & Error Handling**

   * Proper 404/401/400 responses.
   * Global exception handlers in `core/logging.py`.

5. **Database Migrations**

   * Switch from `Base.metadata.create_all` to Alembic migrations.
   * Create first migration for all models.

---

## **2️⃣ API Versioning & Documentation**

- Ensure all routes are versioned under `/api/v1/`.
- Validate schemas for requests/responses.
- Check FastAPI docs: `/docs` and `/redoc`.

---

## **3️⃣ Testing**

- Write `pytest` tests for:

  - Products (already mostly done)
  - Users (signup/login)
  - Orders/cart flow

- Use `pytest-asyncio` for async endpoints.

---

## **4️⃣ DevOps / Deployment Prep**

- Create **Makefile** for running server, migrations, tests.
- Dockerize backend:

  - Build image
  - Connect to PostgreSQL + Redis services in `docker-compose`.

- Prepare AWS deployment:

  - ECS/Fargate or Lambda + API Gateway
  - RDS for PostgreSQL
  - Secrets Manager for env vars
  - CloudWatch/Sentry for logging

---

## **5️⃣ Optional**

- Pagination helpers for endpoints returning lists.
- Rate limiting on sensitive endpoints.
- Caching frequently accessed endpoints (products listing).

---

✅ **Tomorrow’s priority**:

- Finish **Users + Auth**.
- Orders & Cart can be started once auth is working.
- Tests and deployment prep after endpoints are solid.

---
