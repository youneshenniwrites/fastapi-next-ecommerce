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

## Streamed account navigation repair

On 4 October, clean local browsing reproduced the hosted React hydration error:
`AccountLink` received a resolved session before its streamed header hydrated.
The server had rendered a busy `Account` span, while the client expected a sign-in
or account link. React discarded and regenerated that part of the header.

The link now uses React's hydration snapshot to retain its server placeholder
for the initial hydration pass. After that pass it follows the current session,
including later loading, guest and authenticated transitions. This does not
suppress hydration warnings or change session permissions. Three regressions
reproduce the mismatch with guest, authenticated and failed session reads; all
failed before the repair and pass afterward. The production browser security
check now also rejects hydration errors after the navigation link settles.

The keyboard journey also now waits for the product page's level-one heading.
Its previous title-only assertion could match a catalog card before navigation
finished and send axe into the destination's loading skeleton. This strengthens
the navigation assertion without adding sleeps or retries.

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
VIN-269 subsequently received an owner-approved, narrowly bounded development-dependency
audit exception through 10 October 2026, extended once on 8 October to
17 October 2026 at 23:59 UTC. It does not waive other
findings or represent an upstream vulnerability repair.

### Hydration repair verification — 4 October

All 424 unit tests and 21 Node checks pass, together with lint, formatting,
type checks and the production build. The production browser matrix passed 45
checks and intentionally skipped two desktop-only mobile-menu cases. Its one
failure exposed the product-heading synchronization bug described above. After
that assertion was corrected, all six desktop/mobile keyboard journeys passed
without retries (three runs per viewport). Both desktop and mobile security tests
passed their new hydration checks across nine routes each.
[PR #282](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/282)
then merged after all CI and a clean Codex review of its current commit.
[The merged-main frontend run](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37223989500)
also passed before delivery.

## Public hosted sanity and cleanup

On 4 October at 18:46 UTC, final read-only Chromium checks visited `/`, `/login`, `/register`,
`/cart`, `/orders` and `/products/1` on
[the development app](https://forme-ecommerce-development.vercel.app), at
320×740 and 1280×900. The deployed revision was `5ebde00`, confirmed by
[development delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37224305159).
All twelve responses were HTTP 200, fit the viewport and passed axe. No
JavaScript page errors, including hydration errors, were observed. Each route's
first Tab focused the named Skip to content link with a solid 2px outline.
Mobile navigation opened by keyboard and returned focus to its trigger on Escape.
The compact catalog actions all fit their cards, verifying the earlier mobile repair.

Two desktop routes still reported React #418 before this hydration repair.
A separate phase-instrumented probe observed the same error before axe ran;
local development diagnostics identified the account-link span/anchor mismatch.
The final deployed check above passed after that repair. Current ticket disposition
and detailed evidence are recorded on VIN-259.

No hosted login, account creation, cart mutation or payment was performed; no
hosted data cleanup was needed. Local accounts, carts, orders and signed webhook
fixtures lived only in Playwright's temporary databases, retired on server
teardown. Private journey screenshots/traces remain disabled. Test fixtures mock
the external checkout page and use signed fixture payment events; they do not
prove third-party Stripe conformance or a new hosted paid purchase.

Visual inspection and browser-assisted keyboard checks cover the narrow task
sequence. Screen-reader speech, every possible tab order, all devices and formal
conformance were not evaluated. This verifies VIN-259’s bounded demo acceptance;
broader accessibility conformance remains VIN-131.
