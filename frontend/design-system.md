# FORME UI foundation

Tailwind CSS v4 supplies utilities and semantic tokens. shadcn/ui supplies editable
React components in `src/components/ui`; shop components compose them. Button,
Badge and Skeleton were generated with the pinned shadcn CLI using the official
new-york registry, then adapted to FORME tokens and the local `cn` helper.

## Adding a component

From `frontend/`, run `npx --no-install shadcn add COMPONENT`. Review generated
code and dependency changes, use exact direct dependency versions, and commit the
lockfile. `components.json` defines aliases and the CSS entry point. If the CLI
imports `cn` from its package, switch it to `@/lib/utils`, our clsx/tailwind-merge
helper. Do not install the whole registry. Add components for real feature needs.

## Styling rules

- Use semantic utilities (`bg-primary`, `text-muted-foreground`, `border-border`)
  instead of repeating palette values. Tokens live in `src/app/globals.css`.
- Paper backgrounds, forest-green actions, sage surfaces and a warm focus outline
  preserve the FORME identity. Use system sans-serif text and Georgia headings.
- Use Button for actions, `buttonVariants()` on real links, Badge for stock labels,
  and Skeleton inside a labelled loading status. Never nest a button inside a link.
- Keep layout/server components on the server. Add client boundaries only for
  interactive behavior. `asChild` is available for compositions that need Radix Slot.
- Preserve disabled, keyboard-focus, error, empty, stock and reduced-motion states.
  There is no dark-mode switch or supported dark palette yet.

## Incremental CSS migration

Tailwind theme and utilities are imported explicitly, without Preflight. Existing
native-control resets and typography remain in the components layer; utilities
can override them. Component primitives receive solid zero-width borders in the
base layer, so their border utilities work without resetting all native controls.
Existing layout selectors remain until the separate storefront migration. Do not
turn Preflight on without auditing untouched pages and native form controls.

The shared Button default keeps FORME's rectangular, comfortably sized action
style. Default badges support stock labels; skeletons honor reduced motion. No
account forms, cart interactions or checkout behavior are introduced here.

## Verification

Run lint, formatting, types, unit tests, build and Playwright as described in the
README. Browser tests cover actual catalog/retry behavior, keyboard and mobile
access, axe checks, theme styles and reduced-motion loading. Desktop/mobile
screenshots are produced in `test-results` and retained by CI artifacts.
