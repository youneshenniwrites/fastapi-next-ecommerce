# Portfolio vision

This is an interview showcase, not a real business. Build a polished, reproducible
fictional desk-accessories shop with decisions and evidence the owner can explain.
GBP is the currency; Vercel/Neon free plans host the demo. Use a modular monolith and add
infrastructure only for a demonstrated need. Deliver focused, reviewed PRs.

The [canonical portfolio completion plan](portfolio-completion.md) owns all current
priorities, status and acceptance gates. This page describes product direction only.

## Product direction

1. Reproducible demo: fictional catalog and explicit, safe admin bootstrap.
2. Polished Next.js/TypeScript storefront: responsive catalog/detail pages,
   accessibility, loading/empty/error states, API contract and frontend CI.
3. Complete sign-in → cart → checkout → confirmation across frontend/backend.
4. Prove commerce correctness: server-owned prices, atomic inventory, checkout
   idempotency, and concurrent attempts to buy the last item. Implement these
   protections with checkout, not as a later patch. Add sandbox payments afterward.
5. Free hosted demo: development and production are live on isolated Vercel/Neon
   resources, with secret stores, API docs and verified GitHub-triggered production
   delivery (#46) and [verified reviewed manual frontend previews](../design/frontend-previews.md#verified-closeout--2-october-2026) (VIN-45). No paid
   upgrades, card or extra API billing.
6. Interview package: architecture diagram, decision records with alternatives,
   test evidence, and a five-minute demonstration walkthrough.

## After the completed demo

VIN-288 plans a richer workspace/home-office catalog of up to 100 items, useful
product information and full-catalog discovery. VIN-290 delivered one stored
category per product and category browsing. VIN-291 delivered a stable local
photograph and optional stated facts. The larger assortment remains open under
VIN-292. Category and media data stay product-agnostic so a later assortment
does not require name-based code.
VIN-295 separately saves owner catalog administration; it is explicitly deferred,
with store-model discovery still open. New product work remains a fictional,
sandbox shop unless the owner separately approves a real-business transition.
The canonical plan owns ordering. Remaining VIN-288 work is planned, not
delivered, and is not a new VIN-155 completion criterion.

## Success criteria

A reviewer can run the demo without editing code, navigate a coherent shopping
journey, and inspect evidence for important failure cases. Explain tradeoffs,
limits, and how the design would evolve at scale. Avoid infrastructure added just
for its name. No real payment details or customer data belong in this demo.

See [roadmap](roadmap.md) for the capability index and
[the canonical portfolio plan](portfolio-completion.md) for status and progress.
Update the canonical plan when priorities change. Dependency proposals are
reviewed separately; failing bot PRs are not a prerequisite to unrelated work.
