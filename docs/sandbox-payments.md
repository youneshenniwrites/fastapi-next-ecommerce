# Sandbox payments

VIN-30 adds hosted Stripe Checkout to newly placed orders when the API's sandbox
configuration is enabled. This document describes the implementation; the
[canonical plan](plans/portfolio-completion.md) records merge and hosted proof.
All products, customers and payments are fictional. GBP only; no live charges.

## Configuration and activation

On the **development API project only**, store `STRIPE_API_KEY` and
`STRIPE_WEBHOOK_SECRET` as server-only secrets. Only `sk_test_`/`rk_test_` keys are
accepted. Set `STRIPE_CHECKOUT_ORIGIN` to the exact development storefront origin,
and enable `STRIPE_ENABLED=true` only after migrations and reviewed code deploy.
Never prefix these secrets with `NEXT_PUBLIC_`, commit them or paste them in issues.
Without activation, existing non-payment checkout continues working.

Register `/api/v1/payments/webhook` on the API with these snapshot events:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `checkout.session.expired`

The adapter and destination use API version `2026-08-26.dahlia`. Keep recovery
links disabled; a recovered Checkout Session could accept money after stock was
released. Session line items and amounts come only from persisted order snapshots.
Do not enable adjustable quantities, promotions, shipping or tax on this integration.

The approved free sandbox setup is verified. The development destination and
secrets were configured on 23 September 2026; this is configuration evidence,
**not evidence that a deployed purchase works**. Hosted proof follows reviewed
implementation deployment. Production-shop activation is outside this rollout.

## Customer flow

Place the order once, then choose **Pay with Stripe sandbox**. Placement has
already claimed inventory; payment success never decrements it again. A return
URL cannot mark an order paid. Use **Check payment status** while a signed webhook
is pending. A completed delayed payment keeps its stock until definitive success
or failure. Retrying uses the same persisted order and provider creation identity.

**Cancel unpaid order** expires an open provider session before releasing stock.
Returning through Stripe's cancel link alone does not cancel the order. Failed,
cancelled and expired orders release stock exactly once; paid orders remain
immutable. Cancellation does not restore the cart. Historical orders placed before
activation remain unmanaged, unpaid demo records.

## Recovery

Normal provider expiry is delivered through the signed webhook. Unstarted claims
also expire, but need a customer status check or an explicit operator reconciliation
run; no periodic reconciliation scheduler is installed. An idle unstarted claim can
therefore hold stock past its deadline until reconciliation runs.

From the backend, with the intended environment configured securely:

```sh
python -m app.reconcile_payments --after-id 0 --limit 100
```

Check the command output and advance the cursor for further batches. Never run
against a different environment by copying credentials into shell history.
Provider calls occur outside database locks. Provider uncertainty retains inventory.
If creation's response was lost and the session remains unbound after 23 hours,
the API refuses to create again because Stripe's idempotency retention is finite.
Locate the original session in the sandbox using its order metadata, then run:

```sh
python -m app.reconcile_payments --order-id ORDER_ID --session-id cs_test_SESSION_ID
```

This retrieves and validates the existing session; it does not create a replacement.
Paid snapshots still require replay of the original signed success event from Stripe
before the order becomes paid. Resolve a conflicting terminal state explicitly;
never manually decrement or release inventory to silence an error.

## Verification

Backend tests cover signed payload rejection, exact totals/ownership, rollback,
provider response loss and operator recovery. PostgreSQL tests exercise concurrent
session creation, duplicate/out-of-order events, cancellation and stock release.
Browser fixtures use a separate disposable API/database and signed fictional
webhooks; the provider page is mocked. They are not hosted Stripe evidence.

Hosted acceptance must separately record the deployed revision, fictional order,
sandbox session/event IDs, final payment state and inventory effect for success,
cancellation and expiry. Never publish API keys, signatures or customer credentials.
See [ADR 0003](decisions/0003-sandbox-payments.md) for transaction decisions.
