# VINDOR UI foundation

Tailwind CSS v4 supplies utilities and semantic tokens. shadcn/ui supplies editable
React components in `src/components/ui`; shop components compose them. Button,
Badge, Skeleton, Sheet, Input, Checkbox, Select and NativeSelect were generated with the pinned shadcn CLI using the official
new-york registry, then adapted to VINDOR tokens and the local `cn` helper.

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
  preserve the VINDOR identity. Use system sans-serif text and Georgia headings.
- Use Button for actions, `buttonVariants()` on real links, Badge for stock labels,
  and Skeleton inside a labelled loading status. Never nest a button inside a link.
- Keep layout/server components on the server. Add client boundaries only for
  interactive behavior. `asChild` is available for compositions that need Radix Slot.
- Preserve disabled, keyboard-focus, error, empty, stock and reduced-motion states.
  There is no dark-mode switch or supported dark palette yet.

## Layout and navigation

SiteHeader/SiteFooter, SectionHeading, ProductCard and ProductDetails compose the
storefront. The mobile Sheet has a labelled dialog, close control, focus trap and
Escape dismissal; links close it before navigating. Sorting uses shadcn Select for a themed popup with keyboard and mobile interaction. Search uses Input,
and the labelled Checkbox filters available stock.

All existing page layouts now use Tailwind utilities. Preflight is enabled after
migrating the hero, catalog, details, loading, error and not-found pages; obsolete
layout CSS is removed. Base CSS retains semantic tokens, keyboard focus and
reduced-motion rules. The `product` and `detail-price` hooks remain for browser
assertions, not styling. No dark palette or transactional controls are introduced.

Use named imports from `lucide-react` for UI icons; decorative icons are hidden
from assistive technology and icon buttons have accessible names. Do not hand-draw
SVG icons or illustrations. Use locally stored photographs with source and licence records in PHOTO_CREDITS.md. Third-party notices retain Lucide/Feather and
shadcn licence terms.

## Verification

Run lint, formatting, types, unit tests, build and Playwright as described in the
README. Browser tests cover actual catalog/retry behavior, keyboard and mobile
access, axe checks, theme styles and reduced-motion loading. Desktop/mobile
screenshots are produced in `test-results` and retained by CI artifacts.

## Account form validation

Account forms use React Hook Form with a Zod resolver and shadcn Field, FieldLabel
and FieldError. Schemas live in src/lib/account-validation.ts. Validate on submit,
then on change; associate inline messages with inputs and focus the first invalid
field. Hydrated forms suppress native tooltips with noValidate. Preserve required
attributes, pre-hydration disabled controls and POST fallback. Login and registration
use different password limits; never trim or log passwords. API validation remains
authoritative. Test invalid submissions for zero navigation and zero API calls.
See the [design-system Wiki](https://github.com/youneshenniwrites/fastapi-next-ecommerce/wiki/Design-system).

## Consistency rules

Buttons, text inputs and select triggers use the shared rounded-md token (4px).
Form actions/fields are 48px tall; compact catalog controls are 40px tall.
Keep the global 2px warm keyboard outline with 4px offset; do not layer additional
focus rings onto it. Image containers remain rectangular; supporting panels may
use the existing 8px radius, and decorative icon badges may remain circular.

The homepage renders its hero and approach sections independently of catalog
fetching. The catalog Suspense fallback matches the two-column mobile/three-column
desktop grid, 6:5 images and title/price/description slots. Loading is announced
once by a labelled status; visual placeholders are hidden from assistive technology.

All interactive controls should compose shadcn primitives. Keep native page scrolling
without global smooth scrolling, so validation focus does not animate the viewport;
use shadcn ScrollArea when a bounded custom scroll panel is needed. Select retains
its own Radix viewport and scroll controls. Do not wrap its menu in a second scroll
container. Reserve inline form-error space so corrections do not move submit controls.

## Cart storefront

Cart data is read in a Next.js Server Component and passed to an owner-keyed
CartProvider. Server Actions validate input and identity, call FastAPI, and refresh
the server tree. There is no separate fetch/cache library or cart polling loop. See the
[cart architecture](../docs/design/cart-storefront.md) for boundaries and recovery.

AddToCartButton, CartLink and CartView compose shadcn Button, Badge, Input and
Skeleton using the shared 4px corners and 48px/40px control heights. Quantity forms
use React Hook Form and Zod; FastAPI owns prices, totals and stock. Controls show
pending feedback and associated inline errors. Failed same-account cart reads
preserve a read-only view with a visible Refresh cart action, including empty carts.
Unknown identities discard private content. Signed-out visitors get a sign-in
action; no guest storage exists.
