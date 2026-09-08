# Customer sessions — proposal for issue #24

Status: proposed, not implemented. This note defines the intended security and
verification boundaries before account UI work (#25–27). FastAPI bearer auth
already exists; Next.js customer sessions do not. Revise this note with actual
routes, cookie settings and evidence when the implementation lands.

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

Cookie lifetime must not outlive the access token. The current token response has
no expires_in value, so implementation must select and document an explicit
lifetime source. If an unverified exp claim is read solely to bound cookie expiry,
it must never establish authentication or authorization; FastAPI validates tokens.
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
