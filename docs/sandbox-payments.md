# Sandbox payments

VIN-30 adds hosted Stripe Checkout to newly placed orders when the API's sandbox
configuration is enabled. PR #194 merged the implementation on 23 September 2026; the
[canonical plan](plans/portfolio-completion.md) records merge and hosted proof.
All products, customers and payments are fictional. GBP only; no live charges.

## Configuration and activation

On the **development API project only**, store `STRIPE_API_KEY` and
`STRIPE_WEBHOOK_SECRET` as server-only secrets. Only `sk_test_`/`rk_test_` keys are
accepted. Restricted keys require Accounts read access for `GET /v1/account`,
plus Checkout Sessions read/write access for creation, retrieval, listing and
expiry. Before activation, verify those calls with the actual development key;
configuration alone does not prove its permissions. A denied account lookup keeps
payment creation unavailable and inventory reserved. Set `STRIPE_CHECKOUT_ORIGIN` to the exact development storefront origin,
and enable `STRIPE_ENABLED=true` only after migrations and reviewed code deploy.
Never prefix these secrets with `NEXT_PUBLIC_`, commit them or paste them in issues.
Without activation, existing non-payment checkout continues working.

For protected development hosting, set server-only
`STRIPE_WEBHOOK_RELAY_ENABLED=true` on the **development frontend only**. Its
existing `API_BASE_URL` and `VERCEL_PROTECTION_BYPASS` target the development API.
Register the public frontend URL `/api/payments/webhook`; the bounded relay sends
unchanged bytes and the Stripe signature to the fixed API path
`/api/v1/payments/webhook`. It never accepts a caller-selected destination.
The API remains protected and verifies signatures. Do not put a protection bypass
token in the Stripe URL. Production relay configuration remains disabled.

Subscribe to these snapshot events:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `checkout.session.expired`

The adapter and destination use API version `2026-08-26.dahlia`. Keep recovery
links disabled; a recovered Checkout Session could accept money after stock was
released. Session line items and amounts come only from persisted order snapshots.
Do not enable adjustable quantities, promotions, shipping or tax on this integration.

The approved free sandbox setup and development activation were verified on
23 September 2026. The destination uses the public frontend relay because direct
API access requires Vercel sign-in. The hosted evidence below proves the deployed
journey. Production sandbox payments and their relay remain disabled.

For a guided presentation, use the [customer walkthrough and five-minute script](demo.md#try-the-hosted-sandbox-shop).
This runbook owns operator configuration, recovery and verification evidence.

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

Normal provider expiry is delivered through the signed webhook. Unstarted orders
have a one-hour deadline. Starting payment persists a fixed 23-hour-50-minute
Checkout expiry, allowing the same request to remain valid across the 23-hour
idempotency replay window. Starting Checkout therefore extends the stock claim. Unstarted claims
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

If no session ID can be found, after the persisted expiry plus five minutes run:

```sh
python -m app.reconcile_payments --order-id ORDER_ID --verify-absent-session
```

This verifies the original Stripe account identity persisted with the creation
intent, then scans at most 1,000 sessions in the provider-enforced creation window.
A matching session is reconciled normally. Only a complete scan with no match can
release the claim, after locking and rechecking for a concurrent webhook binding.
The expired immutable request cannot create another payable session. Missing account
identity, changed credentials pointing at another account, incomplete pagination,
multiple matches or provider errors keep inventory reserved for operator investigation.
A generic Stripe 400 response never proves that no session exists: validation may
run before the idempotency lookup. Do not delete or change payment-reference metadata
at Stripe, because reconciliation depends on it. This bounded recovery is explicit;
there is no scheduler or guarantee that idle reservations are reclaimed promptly.

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

## Hosted development evidence — 23 September 2026

Verified at 19:20–19:30 UTC, with a paid-stock follow-up at 19:42–19:44 UTC,
using fictional products/users and Stripe test mode.
Revision `8685cc1bae6f6edad34e569ffa66e78739b8be8d` was redeployed unchanged after
development-only configuration: API `HQxhFPtHraGoAYAMaHMWyPmdcs9Y`, frontend
`5Y9ry8kMnoHvM3a1vBN5smmfUoyC`. The workflow dispatch skipped the already-deployed
revision, so Vercel's Redeploy operation applied configuration to that same revision.

| Scenario | Observed result |
| --- | --- |
| Purchase, order 1 | Stripe `complete` / `paid`, £12.90 GBP; application showed paid and order history was verified. |
| Paid inventory, order 4 | One unit of product 5, £12.90 GBP: stock 29 before placement (19:42:29 UTC), 28 after placement (19:43:14), and still 28 after the server confirmed Paid (19:44:24). Payment did not decrement stock again. |
| Cancellation, order 2 | Application cancelled; Stripe session expired/unpaid. Product 5 stock rose 28 → 29 and stayed 29 after refresh. |
| Expiry, order 3 | Application expired; Stripe session expired/unpaid. Product 5 stock rose 28 → 29. |
| Duplicate expiry event | Original delivery at 19:27:45 UTC and manual replay at 19:29:40 UTC both returned HTTP 200; stock stayed 29. |
| Unsigned webhook | Public relay/API path returned HTTP 400. |

Stripe account `acct_1UItNbAsSrcPIxfF` and all observed sessions had `livemode=false`.
Destination `we_1UItjTAsSrcPIxfFEAhEy1f0` sends to
`https://vindor-ecommerce-development.vercel.app/api/payments/webhook`.
No API keys, webhook secrets or payment credentials are included here.

<details>
<summary>Provider references for reproducing the evidence</summary>

- Paid order 1: `cs_test_a10PAk1kN5DdlDRoh7DvtPwi1mTv2FOPXbagoA5yXkkLRblY90lidv4I4t`.
- Cancelled order 2: `cs_test_a1ioTmUaWO6sAMww49VflHJjLsH6UWygoLFQ8BGvhfwddPVR1CExQOMql2`.
- Expired order 3: `cs_test_a1obPdBiuMkcvdl74VKTdl1WvM48ZfqpO6V1RKHGbyrVKRV1Wv0mSTxZ61`.
- Paid inventory order 4: `cs_test_a1Xv3az6r9DlcvBvh5tFDFrKdyw0T7aGXQyXBZlEClyLdFBUkF5p60xqvx`.
- Replayed expiry: `evt_1UIvpUAsSrcPIxfFCkWfEBjY`.

</details>

Inventory observations came from the public product's server-rendered DTO with an
uncached backend fetch, together with application and Stripe state. Direct Neon
inspection was unavailable: this does not claim inspection of hosted event rows or
`reserved_stock`. PR #194's 77 PostgreSQL payment tests supply separate automated
transaction/race evidence. This hosted run does not complete privacy/monitoring,
restore, accessibility, preview or limiter acceptance in the canonical plan.
