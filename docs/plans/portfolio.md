# Senior SWE portfolio plan

This is an interview showcase, not a real business. Build a polished, reproducible
fictional desk-accessories shop with decisions and evidence the owner can explain.
GBP is the currency; Azure is the hosting target. Use a modular monolith and add
infrastructure only for a demonstrated need. Deliver focused, reviewed PRs.

## Delivery sequence

1. Reproducible demo: fictional catalog and explicit, safe admin bootstrap.
2. Polished Next.js/TypeScript storefront: responsive catalog/detail pages,
   accessibility, loading/empty/error states, API contract and frontend CI.
3. Complete sign-in → cart → checkout → confirmation across frontend/backend.
4. Prove commerce correctness: server-owned prices, atomic inventory, checkout
   idempotency, and concurrent attempts to buy the last item. Implement these
   protections with checkout, not as a later patch. Add sandbox payments afterward.
5. Azure demo: infrastructure as code, managed secrets, logs, health checks,
   deployment/rollback documentation. Agree spending limits before provisioning.
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
