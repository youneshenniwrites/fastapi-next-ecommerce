---
name: refine-tickets
description: Split broad ecommerce work into independently testable stories and persist scope and handoff before implementation.
---

Read root AGENTS.md, [delivery policy](../../../docs/delivery.md), relevant scoped
guidance and the parent issue. Inspect existing issues and PRs with pagination
before creating duplicates. Use the canonical hierarchy, scope checklist and
review-size guidance there; do not maintain a second copy of those rules here.

Within the owner's planning authorization, propose or update linked child stories
with outcomes, dependencies, exclusions, acceptance criteria and validation.
Separate independently deliverable architectural prerequisites before coding;
keep each behavior's required tests, security and recovery together. Preserve
existing ownership, links and implementation evidence. Do not close a parent
merely because it has been split or one child has merged.

Record the next unblocked story and a compact handoff in the issue. Use
[update-delivery-board](../update-delivery-board/SKILL.md) for actual statuses,
not invented workflow columns. Read back changed issues and links. Refinement
does not authorize implementation, parallel work, merge or deployment.
