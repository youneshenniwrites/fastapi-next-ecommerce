# Frontend skeleton

Reserved for the Next.js App Router + TypeScript storefront. This folder is not
runnable yet: package.json, dependencies, routes, and frontend CI arrive in the
Next.js implementation PR. `make dev` currently starts the backend only.

- `src/app/`: future routes and layouts
- `src/components/`: future shared UI
- `src/lib/api/`: future OpenAPI-generated client and integration helpers
- `AGENTS.md`: frontend conventions
- `.agents/skills/ecommerce-frontend/`: scoped development skill

Azure is the hosting target. See [architecture](../docs/architecture.md) and the
[roadmap](../docs/plans/roadmap.md) for the proposed deployment and implementation order.
