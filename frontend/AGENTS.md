# Frontend agent guidance

This folder is a directory skeleton for the planned Next.js App Router storefront.
It contains no package manifest, installed dependencies, or runnable application.
The root make commands currently operate only on the backend.

Use the scoped skill in .agents/skills/ecommerce-frontend for frontend changes.
When implementing the app, use TypeScript, pin the runtime/package manager, commit
one lockfile, and add real lint, typecheck, build, and browser checks to CI. Record
those commands here once they exist; do not report placeholder checks as passing.

FastAPI owns authentication enforcement, prices, stock, and order state. Generate
API types from its OpenAPI contract. Keep credentials and session tokens out of
browser-accessible environment variables. Azure is the cloud target; coordinate
server-side API URLs with the deployment plan in ../docs/architecture.md.
