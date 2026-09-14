# Frontend agent guidance

Read root [AGENTS.md](../AGENTS.md) and the assigned issue's scope/handoff first;
[delivery policy](../docs/delivery.md) governs ticket splitting and resume steps.

This is the runnable Next.js App Router/TypeScript catalog. Read the root portfolio
plan and naming skill. Use Node 24.20.0 (.nvmrc) and npm 11.19.1; commit package-lock.json.

From frontend/: npm ci, npm run dev, npm run lint, npm run format:check,
npm run typecheck, npm test, npm run build, npm run test:e2e. Browser tests require
backend/.venv (make setup), a production build, and Playwright Chromium installed.
They launch disposable real FastAPI and fault-fixture servers; never reuse live data.

Use src/app for composition, src/components for UI, src/lib/api for the client.
FastAPI owns permissions, prices, stock and future order state. API_BASE_URL is
server-side only. No credentials belong in browser environment variables.

To update generated types: from backend/ run uv run python -m scripts.export_openapi,
then from frontend/ run npm run api:generate. Commit both outputs. CI checks drift.
Do not hand-edit generated schemas or maintain independent response interfaces.

Preserve loading, empty, error, not-found, out-of-stock and reduced-motion behavior.
Verify keyboard access, mobile layout and automated accessibility checks. Product
photography is licensed and stored locally; unknown names use a Lucide placeholder.
Read PHOTO_CREDITS.md before replacing assets. Never create custom SVG artwork.

Server-mediated sessions, registration/login screens, profile/navigation and the signed-in cart storefront are implemented; checkout remains planned. Development and production demos are deployed.
Read deploy/environments/README.md in the repository root for the approved hosting plan. Do not
present working purchase controls until the corresponding transaction exists.

Use Tailwind semantic tokens and shadcn primitives for new UI. Read
[design-system.md](design-system.md) before adding components or changing global
CSS. Preserve the documented reset strategy and server/client boundaries.
Use lucide-react for UI icons; do not create custom SVG artwork.

Before Next.js changes, read relevant version-matched guides under
`node_modules/next/dist/docs/` from this frontend directory. Inspect runtime
errors and verify affected pages in the browser; use documented fixes. See
[framework guidance](../docs/framework-agent-guidance.md) for discovery and fallback.
