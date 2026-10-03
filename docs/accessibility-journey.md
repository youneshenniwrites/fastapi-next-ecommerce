# Focused demo accessibility evidence — VIN-259

The local production build supports the bounded keyboard and mobile demo journey.
This verifies the application's controls and feedback; it is not a full WCAG audit
or a claim about Stripe's hosted checkout accessibility. VIN-131 retains that
broader scope. Merge, deployment and delivery acceptance remain tracked in
[VIN-259](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/259).

## Reproduced defect and repair

At a 320px viewport, guest catalog actions extended beyond their product cards.
The document was 339px wide while its layout viewport was 320px. Chromium expanded
`innerWidth` to 339px, so the old overflow assertion incorrectly passed.

Compact product actions now fit their card and wrap their complete labels. The
regression compares document width to Playwright's configured viewport. The
repaired local catalog measured 320px for document, layout and inner width; a
full-page visual inspection confirmed readable labels without horizontal clipping.
The loading, guest, retry, signed-in and stock states share this sizing rule.

## Journey and state matrix

Tested implementation: `209946e`, based on `160ab3e`, on 3 October 2026.
Production build, disposable real FastAPI/SQLite fixtures, Chromium desktop
1280×720 and Pixel 7 emulation 393×851. The added complete journey and catalog
failure/loading checks also explicitly use 320×740.

| Step/state                                        | Keyboard and feedback evidence                                                                                                                     | Layout and automated checks                                                                                                         |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Catalog, product, stock, missing product          | Skip link; mobile dialog opening, Escape and focus return; named product/sign-in actions                                                           | 320px overflow regression; axe on catalog/detail/dialog; visual catalog inspection                                                  |
| Login/registration, invalid input and credentials | Email-to-password tab order; password toggle; submit by Tab/Enter; incorrect login alert receives focus; registration status and inline validation | Existing account axe checks on desktop/mobile; added login/error 320px checks                                                       |
| Add/cart and stale/uncertain recovery             | Add by Tab/Enter; Saved status; cart link; named quantity controls; visible retry/status; stale writes remain disabled until recovery              | Existing cart axe and recovery tests on desktop/mobile; complete journey cart at 320px                                              |
| Checkout and placement conflicts                  | Review and Place reached by Tab/Enter; stock/cart conflict alerts; lost response retry keeps one order                                             | Existing checkout axe and ownership/conflict regressions; added review/confirmation 320px checks                                    |
| Sandbox return and history                        | Pay and Order history reached by Tab/Enter; server-confirmed payment has a status announcement                                                     | Axe and layout at pending confirmation, paid return and history; paid/cancelled/expired/failed/lost-response/processing regressions |
| Empty, failure and loading catalog                | Named loading status; reduced-motion skeleton; named failure alert; retry reached by Tab/Enter                                                     | Added axe and 320px layout checks; retry restores the empty state                                                                   |

The new keyboard journey traverses real tab order and checks a solid 2px focus
outline before activation. Its important controls occur in the expected task
sequence: product → sign-in → cart → review → place → payment → history.
Axe runs after stable route state is visible and cart writes are enabled; transient
session-refresh disabling is not mistaken for the settled view.

## Reproducible checks

From `frontend/`, with the repository's Node version and Chromium installed:

```sh
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
npx playwright test --project='payments-Desktop Chrome' --project='payments-Pixel 7' --project=desktop --project=mobile --project='account-Desktop Chrome' --project='account-Pixel 7' --project='orders-Desktop Chrome' --project='orders-Pixel 7' --project=cart-desktop --project=cart-mobile --project=failure-states --grep 'keyboard demo journey|mobile navigation|out-of-stock|complete UI account|password visibility|checkout places|sandbox checkout reconciles|signed-in cart journey|same-account failed reads keep|uncertain writes stay|two-account isolation|empty catalog|loading state'
```

Lint, formatting, types, unit tests and production build passed. The focused
browser matrix passed 42 tests in approximately three minutes; two desktop-only
mobile-menu cases intentionally skipped. Existing coverage passed: 99.06%
statements, 97.69% branches, 100% functions and 99.74% lines. Local runtime was
Node 24.20.0/npm 11.19.0; CI must additionally verify the pinned npm 11.19.1.
The unchanged dependency audit remains blocked by VIN-269; it was not suppressed.

## Public hosted sanity and cleanup

On 3 October 2026 at 20:07 UTC, read-only Chromium checks visited `/`, `/login`,
`/register`, `/cart`, `/orders` and `/products/1` on
[the development app](https://forme-ecommerce-development.vercel.app), at
320×900 and 1280×900. All twelve responses were HTTP 200. Each route's first Tab
focused the named Skip to content link with a solid 2px outline. All checked
routes fit the viewport except the existing 320px catalog (339px), confirming
that the local repair still needs deployment verification. The deployed Git
revision was not independently established in this sanity check.

No hosted login, account creation, cart mutation or payment was performed; no
hosted data cleanup was needed. Local accounts, carts, orders and signed webhook
fixtures lived only in Playwright's temporary databases, retired on server
teardown. Private journey screenshots/traces remain disabled. Test fixtures mock
the external checkout page and use signed fixture payment events; they do not
prove third-party Stripe conformance or a new hosted paid purchase.

Visual inspection and browser-assisted keyboard checks cover the narrow task
sequence. Screen-reader speech, every possible tab order, all devices and formal
conformance were not evaluated. Current-head CI/review and the repaired hosted
catalog check must be recorded before VIN-259 is marked Done.
