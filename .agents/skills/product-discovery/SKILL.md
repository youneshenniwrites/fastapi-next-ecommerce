---
name: product-discovery
description: Interrogate the product owner about genuine product decisions before ticket refinement, then record a decision note for refine-tickets.
---

Read root AGENTS.md, [delivery policy](../../../docs/delivery.md), the
[portfolio plan](../../../docs/plans/portfolio.md), [roadmap](../../../docs/plans/roadmap.md)
and [architecture](../../../docs/architecture.md) first. Then inspect the code and
design notes for the idea's area — routes, models, storefront views and the
matching notes under docs/design — before asking anything.

Interrogate only decisions the repository cannot answer: expected user behaviour,
edge cases, what happens when X fails, admin vs customer, MVP vs later, explicit
exclusions. Never ask technical questions answerable from the repo, existing
issues, or prior decisions; cite what you already found instead.

Record a decision note in the tracking issue: outcome, MVP boundary, included
behaviour, exclusions, and each open decision with the owner's answer. Durable
cross-cutting product decisions may also go to docs/plans/<topic>-decisions.md
with a link from the issue. Hand the note to
[refine-tickets](../refine-tickets/SKILL.md) for story decomposition.

Discovery does not authorize refinement, implementation, merge or deployment.
