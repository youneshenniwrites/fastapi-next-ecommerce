---
name: update-docs
description: Update ecommerce README, Wiki, onboarding, architecture or API documentation to match a specified change or delivered PR.
---

Read [delivery policy](../../../docs/delivery.md) and inspect the requested change against current code. Determine affected documentation rather than rewriting everything: README for entry points, versioned docs for commands/contracts/design decisions, Wiki for explanations, board for live delivery state. Preserve useful detail; link between sources instead of duplicating changing status tables.

Document only verified behavior as implemented. Label proposed features and deployment plans clearly; keep Azure as the chosen cloud and GBP as the demo currency. Describe localhost links as requiring the local stack. Never invent a hosted endpoint, test result or deployment.

For API changes, update source OpenAPI metadata and relevant examples using the repository's established contract generation/check commands. Avoid hand-editing generated contracts. Such code changes require the normal relevant validation and PR review. Verify examples, paths, links and commands where practical; report prerequisites that prevent verification.

Keep repository changes on the task branch and use the normal PR workflow. Inspect the Wiki clone's remote and working tree before editing; preserve unrelated edits. Publish Wiki changes only within documentation-publication authorization and after the described behavior is available, or explicitly label the page as a proposal. Reuse existing authorization without asking again.

Read back published pages and inspect the final diff. Report changed pages, verification and any unpublished updates. Use [update-delivery-board](../update-delivery-board/SKILL.md) only when the task also calls for delivery tracking; docs updates do not themselves imply a ticket is Done.
