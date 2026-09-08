# Frontend agent guidance

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
art is locally authored SVG illustration; unknown names use neutral fallback art.

Server-mediated sessions are implemented; account UI, cart, checkout remain planned. Development and production demos are deployed.
Read deploy/environments/README.md in the repository root for the approved hosting plan. Do not
present working purchase controls until the corresponding transaction exists.

Use Tailwind semantic tokens and shadcn primitives for new UI. Read
[design-system.md](design-system.md) before adding components or changing global
CSS. Preserve the documented reset strategy and server/client boundaries.
Use lucide-react for UI icons; do not create custom SVG artwork.
