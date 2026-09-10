# Customer account journey

The account milestone covers registration, sign-in, private profile navigation and
sign-out. Cart, checkout, payments, password recovery and email verification are
separate work. Use the [delivery board](https://github.com/users/youneshenniwrites/projects/1)
for their current status.

## Walk through the demo

Use the [development storefront](https://vindor-ecommerce-development.vercel.app)
for experiments. Use a unique fictional email and a password you do not use
elsewhere; development and production have separate accounts and databases.

| Step | Action | Expected result |
| --- | --- | --- |
| Register | Open `/register`, enter a fictional email and an 8–128 character password, then select Create account. | Confirmation and Continue to sign in; registration does not sign in automatically. |
| Sign in | Follow Continue to sign in and submit the same credentials. | Return to the collection; navigation shows My account. On mobile, open the navigation menu to find it. |
| View profile | Select My account. | Only the signed-in customer's email and membership date appear. |
| Sign out | Select Sign out on the account page. | Return to `/login`; opening `/account` now shows the sign-in prompt. |

On first load the form waits for its scripts before accepting input. Empty or
incomplete submissions focus the invalid field without sending a login request.
Guest sign-in links use client navigation; successful login/logout and
signed-in account navigation load a new document to discard stale private state.

Invalid credentials show an error. Duplicate registration suggests signing in.
A service outage has retry guidance rather than claiming the session is invalid.
An uncertain registration response advises trying sign-in before registering
again, to avoid blindly repeating a write.

## Boundaries and limitations

FastAPI owns authentication and active-user checks. The browser calls same-origin
Next.js session handlers, which keep the bearer token in a host-only HttpOnly
cookie. The profile page is a public shell; private details load from a no-store
endpoint. Tokens are not placed in local storage or rendered into client props.

A missing or expired session shows the sign-in prompt. Hidden account pages clear
private snapshots and defer profile requests until visible. Logout clears this
browser's cookie; it does not revoke a previously copied JWT, which remains valid
until expiry unless backend user checks reject it. There is no refresh-token,
global logout, password reset, MFA or email-verification flow in this milestone.

See the [session design](design/customer-sessions.md) for exact origin checks,
expiry, failure handling and the distinction between browser sessions and the
[direct bearer-token API](api.md#browser-sessions-and-the-direct-api).

## Reproduce the automated evidence

Follow [frontend setup and verification](../frontend/README.md#verification) to
install the locked dependencies and Playwright Chromium. From `frontend/`:

```sh
npm run build
npm run test:e2e
```

The suite starts disposable local FastAPI/SQLite and fault-fixture services. It
never points at hosted customer databases. Separate backend CI tests PostgreSQL.
The `account-Desktop Chrome` and `account-Pixel 7` projects run the complete UI
journey with a unique fictional account, including registration confirmation,
invalid login, profile access and UI logout. Pixel 7 is browser emulation, not a
physical-device test. Safari and Firefox are not covered by this configuration.

| Evidence | Location |
| --- | --- |
| Complete UI journey, native validation, first-load readiness, expiry, logout failures and restoration | [account.spec.ts](../frontend/tests/browser/account.spec.ts) |
| Real API session boundaries, HttpOnly/no-store behavior, origin rejection | [session.spec.ts](../frontend/tests/browser/session.spec.ts) |
| Session handler unit checks | [session.test.ts](../frontend/tests/session.test.ts) |
| Browser projects and disposable service configuration | [playwright.config.ts](../frontend/playwright.config.ts) |
| CI commands and artifacts | [Frontend CI](../.github/workflows/frontend.yml) |

Account/session projects disable automatic traces and screenshots. Explicit
screenshots use empty forms or mocked fictional profiles; never add real
credentials to fixtures, screenshots, traces, logs or shared Postman exports.
The browser report is retained in GitHub Actions for 14 days. Automated axe
checks and keyboard/mobile tests supplement review; they are not a complete
accessibility certification.

The implementation was delivered in [#41](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/41)
(session handlers), [#64](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/64)
(registration/login screens), [#66](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/66)
(profile/navigation), and [#69](https://github.com/youneshenniwrites/fastapi-next-ecommerce/pull/69)
(form readiness and guest navigation). Each PR links its review and test evidence.
