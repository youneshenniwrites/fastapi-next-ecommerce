# Framework/Architecture Audit

**Date:** 16 Sep 2026
**Status:** Completed
**Issue:** #84

## Installed Versions
- **FastAPI:** ≥ 0.141.1 (Python 3.12, SQLAlchemy 2.0.x, Pydantic 2.x)
- **Next.js:** App Router (Node 24)

## Findings

### A. Backend — FastAPI patterns

| File/Area | Finding | Severity | Recommendation |
| --- | --- | --- | --- |
| `app/models/` and `app/crud/` | **SQLAlchemy 1.x style mapping.** Models use `Column(...)` instead of `Mapped[...]` and `mapped_column()`. CRUD functions use `db.query()` instead of `db.execute(select(...))`. | **P1 (Must fix before checkout)** | Refactor models to use SQLAlchemy 2.0 type hints (`Mapped`) and 2.0 style select statements. This ensures robust type checking and proper concurrency/locking for checkout. |
| `app/schemas/` | Pydantic v2 conventions are followed correctly (`ConfigDict`, `@field_serializer`, `@model_validator`). | **No finding** | Continue current pattern. |
| `app/api/deps.py` | Dependency injection, synchronous session scoping (`yield db`), and auth dependency shape look correct for `psycopg[binary]`. | **No finding** | Continue current pattern. |
| `app/api/v1/auth.py` | OAuth2 form handling and token responses match FastAPI conventions. | **No finding** | Continue current pattern. |
| `app/main.py` | No lifespan or `@app.on_event` usage; app initialization is clean. CORS middleware is configured correctly. | **No finding** | Continue current pattern. |

### B. Frontend — Next.js App Router patterns

| File/Area | Finding | Severity | Recommendation |
| --- | --- | --- | --- |
| `src/app/cart/actions.ts` | **Undocumented `refresh` import.** Uses `import { refresh } from "next/cache"`. While this works, the documented standard public API for clearing cache is `revalidatePath`. | **P2 (Should fix)** | Change to `revalidatePath("/cart")` or `revalidateTag` to adhere strictly to the public Next.js App Router API. |
| `src/app/` layout and page | Server Components vs Client Components boundary is correctly placed. `layout.tsx` fetches data securely on the server. | **No finding** | Continue current pattern. |
| `src/lib/api/client.ts` | Excellent use of `openapi-fetch` restricted to server-side only (`import "server-only"`). Browser never talks directly to backend. | **No finding** | Continue current pattern. |

### C. Cross-cutting

| File/Area | Finding | Severity | Recommendation |
| --- | --- | --- | --- |
| `backend/infra/` | **Unused Azure Terraform.** Terraform scripts exist for Azure, but environments README states the project is on Vercel + Neon Free. | **P3 (Technical debt)** | Remove unused Terraform files or track as technical debt. |
| `next.config.ts` | **Security Headers Missing.** CSP and HSTS are absent. | **P3 (Tracked)** | Tracked by epic #126 (Security hardening). |
| Stub files | Stub files like `models/order.py` and `services/payments.py` exist as placeholders. | **No finding** | Expected, these are targets for #118-#120. |

## Sequence recommendation
1. **Refactor Backend Models (P1)**: Update to SQLAlchemy 2.0 syntax (`Mapped`, `mapped_column`, `select()`) as a prerequisite task before starting checkout.
2. **Fix Next.js `refresh` API (P2)**: Small change to use `revalidatePath` in cart actions.
3. Proceed with **#118 Checkout Implementation** safely.
