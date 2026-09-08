---
name: ecommerce-frontend
description: Scaffold or implement the Next.js ecommerce storefront, its FastAPI integration, and browser verification inside frontend/.
---

Read frontend/AGENTS.md and the root roadmap. Inspect package.json and the existing catalog, generated API types, and checks.
Preserve the working App Router/TypeScript baseline when adding shopping features.

Use src/app for route composition, src/components for shared UI, and src/lib/api
for the API client. Generate request/response types from FastAPI's OpenAPI schema;
avoid independently maintained copies. Keep authorization and monetary calculations
on the backend, and keep server-only credentials out of client bundles.

Build loading, empty, error, and out-of-stock states alongside each shopping view.
Verify keyboard use and mobile layout, then run the actual frontend checks and
capture relevant browser evidence. Label checks not yet available as untested.

Use deploy/environments/README.md for the approved Vercel/Neon hosting design
when deployment is in scope; frontend scaffolding itself does not require cloud resources.

Use docs/delivery.md for ticket and board tracking. For customer sessions, consult
docs/design/customer-sessions.md before implementation; update the proposed note
when actual behavior lands and verify it against the linked acceptance criteria.

For UI components and styling, read frontend/design-system.md. Use semantic
Tailwind tokens and compose shadcn primitives; retain reduced-motion behavior and
review generated registry code, dependencies and server/client boundaries.

Use Lucide named imports for icons; do not author new SVG artwork. SiteHeader,
SiteFooter, SectionHeading, ProductCard and ProductDetails are the shared layout
compositions. Include mobile Sheet keyboard/focus checks when changing navigation.
