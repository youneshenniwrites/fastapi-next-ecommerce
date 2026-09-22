# Cart storefront architecture

The cart uses Next.js Server Components for its initial data and Server Actions
for changes. FastAPI remains the authority for the authenticated customer,
permissions, persistence, prices, stock and GBP totals. No React Query, browser
cart storage or client polling layer is used.

## Read and write flow

The root Server Component reads the session cookie and resolves the customer
through FastAPI, then fetches that customer's cart using the generated OpenAPI
client. Both calls are no-store and bounded by the shared five-second upstream
timeout. Only the verified email and cart display data reach client props; the
HttpOnly bearer stays on the server. Since the shared navigation displays a
private cart count, pages are dynamically rendered with private/no-store HTML.
Public catalog content is still rendered by Server Components.

The client provider receives the server snapshot and supplies shadcn controls
with pending/error feedback. It does not fetch the cart. Add, set and remove call
one Server Action, which validates input with Zod, checks the configured Origin
allowlist, and verifies the cookie's current identity through FastAPI. It rejects
an old page's expected identity if another window has changed the account. The
expected email is a consistency check, never an authorization credential.

Add and the +/− quantity controls read the current backend quantity instead of
stepping a browser snapshot. Explicit quantity entry remains an absolute set.
Next serializes action dispatch within a client; an immediate per-product guard
suppresses double activation. FastAPI still uses absolute-quantity PUT semantics:
independent clients can race between an add's read and write, and the last
serialized absolute write wins. This is not an atomic increment API.

The action calls Next's `revalidatePath("/cart")` after writes and recoverable failures. The
same response includes a freshly rendered server tree, updating the cart and
navigation count without a separate browser fetch/reconciliation loop. The old
frontend `/api/cart` routes were internal to this unmerged feature and are removed;
the FastAPI [cart API](cart-api.md) is unchanged.

The cart shell reads behind a Next.js Suspense boundary that contains only a
snapshot delivery component and the header, not route content. The resolved
header receives the server snapshot directly, so its count is in server HTML
before hydration. The fallback retains a plain Cart link; without JavaScript,
streamed header replacement may not display the count. Public forms remain mounted
while server reads settle. The cart page separately server-renders its private
view, including when JavaScript is disabled. Snapshot delivery does not fetch or
cache data in the browser.
The existing session poll also triggers server revalidation when a session ends.

Cart reads use React request memoization so the layout and cart page share one
private result per server render. This is not persistent caching and does not
share data across requests or users. The cart page renders recovery inside its
own provider; other routes use the shell warning.

## Recovery and account isolation

Visible controls remain mounted during a background refresh, so a focus event
between pointer-down and pointer-up cannot swallow the first click. Editing is
disabled until hydration attaches its handlers.

Explicit retry and focus/page restoration use `router.refresh()`. Explicit retry
also refreshes the existing session observer so an identity failure can recover. There is no
periodic cart poll. Focus and page restoration conceal private cart content until refreshed, using
opacity and accessibility hiding while keeping activation targets mounted.
Private controls use native inert during concealment after any already-started
pointer activation completes, removing hidden controls from the tab order; the Server Action
verifies ownership before accepting an activation already in progress. The cart page provider is keyed by verified owner; the shared shell resets
private feedback during the render when its verified owner changes.

When identity is known and unchanged, failed cart reads may preserve the last
rendered cart with a visible Refresh cart warning. These stale controls are
read-only. Unknown or changed identities never reuse that snapshot. Empty carts
have the same retry behavior. A timed-out mutation has an uncertain outcome:
show recovery feedback and refresh rather than automatically repeating an add.
A newly published successful authoritative read clears that uncertainty after the
Next transition settles; an old ready snapshot is not confirmation. If the read
fails, editing stays disabled until retry succeeds. Every arriving snapshot is
compared with the observed session, including late responses after an account
switch. After hydration, loading or failed session checks keep private snapshots
concealed until identity resolves. A concealed cart offers recovery if refreshing settles without publishing
a snapshot; it never reveals private data merely because the transition ended.

## Verification

`frontend/tests/cart-server.test.ts` exercises origin/input/identity boundaries,
private server reads, status mapping and action refreshes. The browser cart suite
uses the real disposable FastAPI database and a test-only loopback wrapper to
inject per-session upstream failures, including a response delayed after commit.
The wrapper is not imported by the deployed API.

Desktop/mobile journeys cover persistence, removal, quantity validation, stock
rejection, rapid and queued actions, stale account rejection, cross-account read
failures, stale quantity adds, unavailable sessions and timeout recovery, with
keyboard and axe checks. Existing account tests verify private HTML cache headers
and ensure bearer cookies never appear in the document.

## Manual acceptance walkthrough

Use fictional details on the deployment being verified. VIN-120 adds non-payment checkout; consult the completion plan for its deployment status.

1. Signed out, open `/cart`: expect a sign-in prompt and no saved products.
2. Register and sign in. Open an in-stock product, press Add to cart, and check
   the navigation count. Reload: the count should remain.
3. Open the cart. Increase/decrease a quantity, enter a quantity and press Update,
   then remove a line. Check that quantities, count and GBP subtotal agree.
4. Submit 0, 100 and a fractional quantity: expect an inline validation error.
   Request more than available stock: expect a stock error, with the saved quantity
   unchanged. Out-of-stock products must not offer an enabled Add button.
5. Sign out and sign back in: saved items return. Use a second fictional account:
   its cart starts independently, without the first account's products.
6. Keep the first account's cart open in another tab, change the signed-in account,
   then return and try a quantity control. The old cart must not modify the new
   account; refresh should show the current account's cart.
7. Use keyboard-only navigation and a narrow mobile viewport. Check focus,
   labels, pending buttons and readable error messages.

Do not simulate outages or alter inventory on the shared live demo. The disposable
browser suite covers faults and uncertain writes safely.

## Rate-limit rejections

A backend write response of 429 produces a typed rate-limit action failure with
optional validated retry seconds and safe wait guidance. It is a known rejected
write, not an uncertain transport outcome: existing cart data remains available,
and the customer deliberately retries after waiting. The provider never replays
the write automatically. This does not change limiter identity or thresholds.

## Request deadlines and timeout recovery

The server API client bounds retrieval of the complete JSON read response, including
its body, to five seconds. An explicit promise deadline accompanies transport
cancellation: cancellation alone was insufficient when Request copies and garbage
collection interrupted signal propagation. The client drains a response clone
within that deadline, preserves the original response metadata for openapi-fetch,
and cancels both body branches on expiry. These API endpoints are JSON endpoints;
this client is not a streaming-download adapter.

The explicit promise deadline applies only to GET/HEAD. Mutations retain the
existing transport timeout; an abort-ignoring write is not detached by a promise
race. A fresh read alone cannot order a write still running upstream. Durable
operation-status/idempotency support is outside this read-deadline fix, so this
does not establish a general guarantee for delayed commits after connection loss.

A timed-out mutation still has an uncertain outcome and is never automatically
replayed. Existing revalidation and read-only recovery require a fresh server
snapshot; the deadline correction does not change cart ownership or last-writer-
wins quantity semantics. Unit tests cover ignored aborts, delayed bodies and late
responses; a real-fetch regression forces GC across Request copies. The unchanged
browser cases cover committed writes, recovery controls and account isolation.
