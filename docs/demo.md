# Reproducible portfolio demo

## Try the hosted sandbox shop

Use the [development storefront](https://vindor-ecommerce-development.vercel.app)
for payments. Production supports the unpaid demo journey; its Stripe payments
remain disabled. No purchase charges real money or ships goods. You do not need
a Stripe account or a real card to try the customer flow.

1. [Create an account](https://vindor-ecommerce-development.vercel.app/register)
   with a unique fictional address, such as `your-demo-name@example.com`, and a
   password you do not use elsewhere. Then [sign in](https://vindor-ecommerce-development.vercel.app/login);
   registration does not sign you in automatically. Development accounts are
   separate from production accounts.
2. Choose an in-stock product, select **Add to cart**, and open **Cart**. Use one
   item for a short demo; stock and prices can change between visits.
3. Select **Review checkout**. The draft shows server-calculated GBP lines and
   totals but has not reserved stock. Select **Place demo order** once. Placement
   claims inventory; it does not establish payment.
4. Choose **Pay with Stripe sandbox** and confirm Stripe displays **Sandbox**.
   Select card payment and use `4242 4242 4242 4242`, a future expiry such as
   `12/34`, and a three-digit CVC such as `123`. Use fictional name/email details
   and leave payment-detail saving off. These are [Stripe's documented test values](https://docs.stripe.com/testing#testing-interactively),
   not real payment credentials.
5. Complete the test payment. On return, look for **Paid — sandbox only** and
   server confirmation. If still pending, deliberately select **Check payment
   status**; returning from Stripe alone is not proof of payment. Do not place a
   second order to retry this payment.
6. Open **Order history** and revisit the same order to see its persisted status.
   Sign out through **My account** when finished.

If the payment button is absent, confirm you used development and a newly placed
order. Orders placed before sandbox activation remain unpaid legacy records.
If stock or prices changed, return to the cart and review it again. For a 429,
follow the displayed wait guidance before retrying; repeated clicks do not help.
Other payment problems belong in the [payment recovery runbook](sandbox-payments.md#recovery).

### Optional cancellation demonstration

On a separate unpaid order, use **Cancel unpaid order** and confirm the cancelled
status. Returning through Stripe's back/cancel link alone does not cancel the
order or release stock. Cancellation does not refill the cart. Avoid placing
unneeded orders: inventory is claimed at placement, and idle unstarted orders
need a status check or operator reconciliation after their deadline. Provider
expiry/replay evidence is already recorded in the runbook; do not wait for expiry
as part of a five-minute presentation.

## Five-minute demonstration script

Prepare a fictional account and an in-stock item first. This is a suggested
presentation sequence, not a measured completion-time guarantee.

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:45 | Catalog and signed-in navigation | Fictional GBP shop; Next.js storefront, FastAPI and PostgreSQL; free Vercel/Neon hosting. |
| 0:45–1:30 | Cart and checkout draft | Prices/totals belong to the server. A draft reserves nothing. |
| 1:30–2:15 | Place the order | Atomic placement claims inventory; retry identity prevents duplicate placement. |
| 2:15–3:30 | Stripe sandbox and paid confirmation | Only verified server-side payment evidence establishes paid state; payment does not deduct stock twice. |
| 3:30–4:00 | Order history | The same customer's order and final status persist across navigation. |
| 4:00–5:00 | Linked evidence and limitations below | Explain what was tested, what is still unfinished and why the design is bounded. |

### Evidence and honest limits

- [Hosted payment evidence](sandbox-payments.md#hosted-development-evidence--23-september-2026)
  records purchase/history, stock before/after payment, cancellation, expiry and
  duplicate webhook delivery. This guide reuses that evidence; writing it is not
  a new hosted verification run.
- [Order transaction decisions](decisions/0002-order-transactions.md) and
  [payment lifecycle decisions](decisions/0003-sandbox-payments.md) explain ownership,
  idempotency, money and inventory boundaries. [Architecture](architecture.md)
  describes the components and hosting.
- No real fulfilment, refunds or production payment activation. Monitoring privacy
  work, restore rehearsal, hosted reliability checks and the focused accessibility
  review remain unfinished. Do not claim enterprise readiness or full accessibility
  conformance; consult the [single completion plan](plans/portfolio-completion.md).

## Prepare a disposable local demo

For a fresh checkout, follow [development setup](development.md) first. The local
bootstrap below does not configure Stripe; local sandbox integration requires the
separate [payment configuration](sandbox-payments.md#configuration-and-activation).

Use a disposable local database. This is a fictional desk-accessories shop with
GBP prices, including an out-of-stock product for frontend empty-stock states.

From the repository root:

```sh
make dev
make demo
make admin EMAIL=admin@example.com
```

The admin command prompts twice for a private password (8–128 characters). There
is no shared default password, command-line password option, or generated secret
in output. Use the account in `/docs` through the login endpoint. Public signup
cannot grant admin access. Start the storefront with cd frontend && npm ci && npm run dev; browse 127.0.0.1:3000.

`make demo` seeds twelve products only when the catalog is empty. Reruns leave all
existing products untouched, including changed names, prices and depleted stock.
A partially populated catalog is also left untouched; this is not a repair or
reset command. It creates no users and never deletes data. PostgreSQL serializes
seeding with a product-table write lock for the short transaction.

To expand an existing six-product demo after applying migration 0004, explicitly run:

```sh
cd backend
uv run python -m app.bootstrap expand-demo --confirm-demo
```

This appends six new products once, preserving every existing product ID, edited
name, price, stock count and saved cart line. On an empty database it creates all
twelve. A small `demo_catalog_editions` marker commits in the same transaction
as the products, so reruns do not duplicate renamed additions or recreate deleted
ones. Name collisions before the first expansion are refused for manual inspection;
no existing row is adopted or overwritten. This is an explicit demo-only operation,
not a migration side effect or a reset. An unrelated catalog would also receive six
additions, so verify the target database before confirming. Rolling back migration
0004 preserves products/carts but loses the expansion marker; do not rerun expansion
after that rollback without manually checking the data.

`make admin` creates a new active admin, or leaves an existing active admin and
its password unchanged. Existing customers require explicit promotion:

```sh
cd backend
uv run python -m app.bootstrap admin --email admin@example.com --promote-existing
```

Promotion preserves the existing password. Disabled accounts are refused; an
unknown promotion target is refused. There is no password-reset operation.
Concurrent attempts to create the same email are protected by the unique database
constraint; a losing operation rolls back and can be rerun.

Commands use backend/.env's host DATABASE_URL, so migrations must already be
applied and any DB_PORT change must be reflected there. They do not create tables
or migrate automatically. All writes in each command commit together or roll back.
For direct seeding use `uv run python -m app.bootstrap seed-demo --confirm-demo`
from backend/. The flag acknowledges fictional demo data; it does not detect a
production database. Never point this command at data you want to treat as live.
