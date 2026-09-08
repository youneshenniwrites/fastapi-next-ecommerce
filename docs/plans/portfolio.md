# Senior SWE portfolio plan

This is an interview showcase, not a real business. Build a polished, reproducible
fictional desk-accessories shop with decisions and evidence the owner can explain.
GBP is the currency; Vercel/Neon free plans host the demo. Use a modular monolith and add
infrastructure only for a demonstrated need. Deliver focused, reviewed PRs.

## Delivery sequence

1. Reproducible demo: fictional catalog and explicit, safe admin bootstrap.
2. Polished Next.js/TypeScript storefront: responsive catalog/detail pages,
   accessibility, loading/empty/error states, API contract and frontend CI.
3. Complete sign-in → cart → checkout → confirmation across frontend/backend.
4. Prove commerce correctness: server-owned prices, atomic inventory, checkout
   idempotency, and concurrent attempts to buy the last item. Implement these
   protections with checkout, not as a later patch. Add sandbox payments afterward.
5. Free hosted demo: development and production are live on isolated Vercel/Neon
   resources, with secret stores, API docs and smoke evidence. Production workflow
   acceptance (#46) and frontend PR previews (#45) finish this milestone. No paid
   upgrades, card or extra API billing.
6. Interview package: architecture diagram, decision records with alternatives,
   test evidence, and a five-minute demonstration walkthrough.

## Success criteria

A reviewer can run the demo without editing code, navigate a coherent shopping
journey, and inspect evidence for important failure cases. Explain tradeoffs,
limits, and how the design would evolve at scale. Avoid infrastructure added just
for its name. No real payment details or customer data belong in this demo.

See [roadmap](roadmap.md) for implemented status and remaining PRs. Keep this plan
and the roadmap consistent when priorities change. Dependency proposals are
reviewed separately; failing bot PRs are not a prerequisite to unrelated work.
