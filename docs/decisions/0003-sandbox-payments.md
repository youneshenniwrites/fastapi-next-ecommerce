# ADR 0003: sandbox payment authority and inventory release

Date: 23 September 2026. Status: proposed for VIN-30; not a claim of deployment.

## Context

ADR 0002 placement already claims stock and removes purchased cart lines. Payment
must not decrement stock again. Stripe's connected sandbox and implementation
planner confirm hosted one-time Checkout as the chosen integration; the project
remains fictional, GBP-only, with no real payment or fulfilment.

## Decision

FastAPI owns the payment lifecycle alongside the existing draft/placed order
state. A provider adapter uses Stripe Checkout Sessions. Next.js only initiates
owned actions and renders authoritative state. Browser success/cancel URLs are
navigation, never evidence of payment or a safe inventory release.

Persist a single payment creation intent and stable provider idempotency key
before making a network call. No database transaction spans that call. Reconcile
its result in a new transaction, checking the current order state again. Lost
responses reuse the intent; they must never create another order or use a new key.
Never retry creation after the provider's idempotency retention window without
reconciliation proving the original result. Uncertainty retains the stock claim.
Starting Checkout sets a fixed 23-hour-50-minute expiry, keeping the immutable
request valid throughout a 23-hour retry window; unstarted reservations retain
one-hour deadlines. This trades longer claims for safe response-loss recovery.
Persist the current Stripe account identity with the request before creation so a
credential change cannot make a different account's empty session list prove absence.

Verified test-mode webhook events establish payment success. Validate session
association, expected GBP amount and currency. Deduplicate event processing and
commit its effects together. Disabled customers' existing payments still settle;
webhooks do not depend on active-customer login. Paid orders are immutable.

Release stock exactly once within the transaction that establishes a terminal
unpaid state. Cancellation of a provider-backed order first makes the session
unpayable at Stripe. Local time or a cancel redirect is insufficient. A completed
but unsettled asynchronous payment retains inventory until a verified terminal
provider result. Refunds and post-payment cancellation remain VIN-128.

Product mutation guards must preserve the ability to restore inventory: prevent
deletion while a managed reservation exists, and bound available plus reserved
stock to the database integer range. Placement and release lock products in
ascending ID order. Cancellation never restores old cart contents.

Existing placed orders remain historical unpaid demo records; migration must not
invent expiry or restore stock that cannot be reconciled. New managed orders have
explicit deadlines. Missing configuration preserves the non-payment demo; no live
Stripe key is accepted. Provider-supported amount bounds are checked before stock
is claimed for a managed order.

## Recovery and limits

Provider expiry webhooks handle normal session expiry. An explicit customer
status check and a bounded operator reconciliation entry point recover missed
notifications and unfinished session creation. No local background task or Codex
schedule is an expiry guarantee. Idle claims without provider sessions need
operator reconciliation; document this limitation in the runbook and hosted demo.

An explicit operator absence check waits until the immutable expiry plus five
minutes, verifies the original account and completely scans the provider-bounded
creation window (at most 1,000 sessions). A match uses ordinary reconciliation;
only complete absence plus a locked recheck permits release. Incomplete scans,
unknown account identity, provider errors or ambiguous matches retain inventory.
Do not mutate provider payment-reference metadata. Generic 4xx responses cannot
prove absence because Stripe can validate requests before idempotency lookup.

Stripe recovery links must remain disabled: they create a new session after stock
may already have been released. Session amounts/quantities are not adjustable;
promotions, shipping, tax and adaptive currency changes are outside this release.

## Verification

Require PostgreSQL concurrency and rollback evidence for creation, event
processing, cancellation, stock release and product mutation. Include lost provider
responses and database commits, disabled customers, invalid signatures, wrong
amount/currency/mode and out-of-order events. Browser tests cover deliberate retry,
account isolation, accessible state and desktop/mobile checkout. Hosted proof is
separate from mocked provider tests and CI.

## References

- [Stripe planner approach: hosted Checkout](https://docs.stripe.com/payments/accept-a-payment?payment-ui=checkout&ui=stripe-hosted)
- [Limited inventory and session expiry](https://docs.stripe.com/payments/checkout/managing-limited-inventory?payment-ui=stripe-hosted)
- [Recovery links create new sessions](https://docs.stripe.com/payments/checkout/abandoned-carts?payment-ui=stripe-hosted)
- [Canonical completion plan](../plans/portfolio-completion.md)

- [Stripe idempotency semantics](https://docs.stripe.com/api/idempotent_requests)
- [Stripe low-level error handling](https://docs.stripe.com/error-low-level)
