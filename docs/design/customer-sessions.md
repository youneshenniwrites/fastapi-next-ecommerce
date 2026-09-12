# Customer sessions — issue #24

Session handlers, registration/login screens and profile/navigation are implemented.
The [account journey guide](../account-journey.md) links desktop/mobile verification,
onboarding steps and implementation evidence (#27).

- POST `/api/session/register`: JSON email/password, returns registered: true (201);
  duplicate registration returns a generic 400, validation 422 and upstream failure
  503. Only credentials are forwarded to FastAPI; no admin fields or session token.
- POST `/api/session/login`: JSON email/password, returns authenticated: true.
- GET `/api/session/me`: active profile or 401; upstream failure returns 503.
- POST `/api/session/logout`: clears the session cookie.

Every response is private/no-store. Configure APP_ORIGIN to the exact browser
origin or explicitly configured HTTPS APP_ORIGIN_ALIASES. Local loopback HTTP requires ALLOW_LOCAL_HTTP_SESSIONS=true; deployment
uses HTTPS and __Host-session. No arbitrary redirect destination is supported:
next/redirect login fields are rejected, and account UI owns local navigation.

## Flow and ownership

The browser submits credentials to same-origin Next.js server handlers. Next.js
uses the generated API contract to call FastAPI's form-encoded login endpoint.
FastAPI remains authoritative for token validity, active users and permissions.
Next.js stores the returned bearer token in a host-only HttpOnly cookie and sends
it to FastAPI only from server code. No token in localStorage, client props, client
bundles or logs. Do not share the backend signing secret with Next.js.

## Cookies and request boundaries

Use Path=/, SameSite=Lax, HttpOnly and Secure on HTTPS deployments, with no Domain
attribute. Plain HTTP localhost requires an explicitly local development exception;
production must not silently downgrade cookie security. A __Host- cookie name is
appropriate only where its Secure requirements are satisfied.

Validate the Origin of state-changing requests against an explicitly configured
application origin; reject missing or mismatched origins for browser session
mutations. Do not trust forwarded host headers without an explicit proxy model.
SameSite is defense in depth, not a replacement for origin checks. Mutations use
POST, including logout. Restrict post-login destinations to safe local routes;
reject external, protocol-relative and malformed redirect targets.

## Expiry, failures and logout

FastAPI now returns expires_in (seconds) from the configured issued-token lifetime.
Next.js subtracts upstream elapsed time and a rounding margin before setting cookie
Max-Age. Token expiry remains authoritative in FastAPI even if client clock or
response delivery delays leave a stale browser cookie. No JWT claims are trusted
or decoded by Next.js.
Do not add a refresh-token flow implicitly. Expiry requires sign-in again.

Resolve the profile through FastAPI, handling invalid/expired tokens and disabled
accounts as unauthenticated and clearing invalid session cookies where possible.
An API outage is a temporary failure, not evidence of invalid credentials. Use
bounded timeouts, useful non-sensitive errors, and no shared caching of profile
or authentication responses.

Logout clears the browser cookie using matching path/name attributes. With current
stateless JWTs, this does not revoke a copied token; it remains usable until expiry
unless backend user checks reject it. Document this limitation rather than claiming
server-side revocation. Password reset, MFA, global logout and rate limiting are
separate work, not delivered by this note.

## Required evidence

Test valid login/profile, invalid credentials, disabled user, expired and malformed
tokens, cookie flags/lifetime, logout cookie deletion, missing/mismatched origins,
unsafe redirects and upstream timeout/outage behavior. Verify token secrecy in
browser-visible state and that private responses are not cached. Exercise local
HTTP and deployment cookie policy explicitly. Use disposable data and avoid
credentials in traces/screenshots. UI tickets add accessible forms and full browser
journey evidence; they do not replace session-handler tests in #24.

## Account forms (#25)

`/register` and `/login` compose shadcn Input and Button with visible labels,
native validation, pending states, focusable error feedback and keyboard access.
Inputs and submission stay disabled until client handlers are ready. The form
uses POST as a fallback and explains when JavaScript must be enabled. First
submissions and service errors do not reload the page; successful login still
uses a full navigation to clear previous session state.
Registration asks users to sign in after success; it does not retry writes or
silently authenticate. An uncertain response advises trying sign-in before
registering again. Login always navigates to `/#collection`, ignoring query-string
redirect destinations. Credentials are not persisted in browser storage or traces.
Password reset, email verification and rate limiting remain separate work.


## Profile and navigation (#26)

The profile component on `/account` renders a loading shell and retrieves the
current customer through GET `/api/session/me`. The shared cart now renders safe
customer/cart display data on the server; page HTML is private/no-store and never
contains bearer tokens. The private profile endpoint remains no-store; UI state is held only
in memory. The account page displays email and membership date, never admin flags.
A missing/expired session shows a sign-in prompt; an outage hides details and
shows a retry action without claiming the customer is signed out.

Desktop and mobile navigation share a session lookup. The account page uses its
own lookup boundary so session updates do not wrap streamed catalog content. It is revalidated on
mount, page restoration, focus/visibility changes, and every minute while visible.
Guest sign-in links use client navigation without prefetching. Authenticated
account links and successful sign-in use full navigations to prevent cached
private screens from being restored by the client router. Hidden/leaving pages clear their profile snapshot; aborted or superseded
requests cannot restore it. The sign-out button posts to the origin-checked
logout handler and then performs a full navigation to `/login` to discard the
router cache. Failed sign-out shows an error and allows retry; it never claims
success. Clearing a browser cookie still does not revoke copied JWTs.
