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

| Time      | Show                                  | Explain                                                                                                 |
| --------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 0:00–0:45 | Catalog and signed-in navigation      | Fictional GBP shop; Next.js storefront, FastAPI and PostgreSQL; free Vercel/Neon hosting.               |
| 0:45–1:30 | Cart and checkout draft               | Prices/totals belong to the server. A draft reserves nothing.                                           |
| 1:30–2:15 | Place the order                       | Atomic placement claims inventory; retry identity prevents duplicate placement.                         |
| 2:15–3:30 | Stripe sandbox and paid confirmation  | Only verified server-side payment evidence establishes paid state; payment does not deduct stock twice. |
| 3:30–4:00 | Order history                         | The same customer's order and final status persist across navigation.                                   |
| 4:00–5:00 | Linked evidence and limitations below | Explain what was tested, what is still unfinished and why the design is bounded.                        |

### Evidence and honest limits

- [Development monitoring](observability.md#hosted-trace-continuity--verified-1-october-2026)
  includes verified error/commerce signals and one joined storefront/API trace.
  Privacy filtering and sampling remain explicit; production monitoring is not
  activated. This rehearsal reuses that evidence rather than generating a new
  monitoring incident.
- [Focused keyboard/mobile journey evidence](accessibility-journey.md) records
  the local production matrix, mobile overflow and hydration repairs, and passing
  desktop/mobile checks on deployed development on 4 October. VIN-259’s bounded
  accessibility acceptance is verified; this does not establish full accessibility
  conformance. Verified demo acceptance and deferred follow-ups are recorded in
  the [completion plan](plans/portfolio-completion.md).

- [Hosted payment evidence](sandbox-payments.md#hosted-development-evidence--23-september-2026)
  records purchase/history, stock before/after payment, cancellation, expiry and
  duplicate webhook delivery. This guide reuses that evidence; writing it is not
  a new hosted verification run.
- [Order transaction decisions](decisions/0002-order-transactions.md) and
  [payment lifecycle decisions](decisions/0003-sandbox-payments.md) explain ownership,
  idempotency, money and inventory boundaries. [Architecture](architecture.md)
  describes the components and hosting.
- [Disposable restore rehearsal](restore-rehearsal.md) is verified on merged
  revision `0f547cb`; [VIN-258](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/258)
  records schema/data/sequence agreement, ownership checks and cleanup. Its tiny
  local fictional dataset does not establish hosted recovery guarantees.
- No real fulfilment, refunds or production payment activation. Consult the
  [single completion plan](plans/portfolio-completion.md) for verified monitoring,
  reliability and deferred post-demo work. Do not claim enterprise readiness
  or full accessibility conformance.

Keep these boundaries visible during the presentation:

- Unstarted unpaid orders can retain reserved stock until a customer status check
  or [operator reconciliation](sandbox-payments.md#recovery) after their deadline.
  There is no durable background expiry worker.
- Rate-limit counters are process-local. Restarts, multiple instances and shared
  networks limit protection; this is not a distributed traffic budget.
- Cart recovery uses a fresh server read, but does not prove ordering for every
  [late-committing write](design/cart-storefront.md#request-deadlines-and-timeout-recovery).
  Relative changes are not atomic across clients.
- Signing out clears the browser cookie; it does not revoke a copied JWT before
  its expiry. See [session boundaries](design/customer-sessions.md).
- Catalog browsing is paged by the API (24 per page) and offset pages can shift
  when products change between requests. Connection recovery and
  free-tier hosting are not measured capacity or availability guarantees. See
  [hosting limits and rollback](../deploy/environments/README.md#runtime-limits).

Maintenance stays separate from the demo: [VIN-269](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/269)
owns the dependency exception expiring **10 October 2026 at 23:59 UTC**;
[VIN-147](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/147)
owns remaining workflow overhead; [VIN-279](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/279)
owns temporary framework patches. [VIN-38](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/38)
automatic review enforcement is owner-deferred; verified reviews and protected CI
remain required. [VIN-261](https://github.com/youneshenniwrites/fastapi-next-ecommerce/issues/261)
delivered scoped service typing, not repository-wide static checking.

### Final rehearsal — 4 October 2026

The development shop ran deployed application revision `5fb29af`, whose
[actual gated delivery](https://github.com/youneshenniwrites/fastapi-next-ecommerce/actions/runs/37228378685)
passed migrations, API/storefront deployment and public checks. A new fictional
account was registered and signed in before the timed presentation.

From **19:39:50 to 19:43:51 UTC**, the browser journey completed product detail,
one-item cart, a £12.90 GBP draft, placement, Stripe's displayed **Sandbox** card
checkout, server-confirmed **Paid — sandbox only**, history and the same paid
order detail. Order #7 contains one Notebook Set. Payment-detail saving stayed
off; the account was signed out afterward. The fictional paid record and its
inventory claim remain as evidence; no production data or real payment was used.

The shopping segment took **4 minutes 1 second** in this single run, including a
browser-tool timeout while filling Stripe's form. Preparation, documentation
inspection and narration were not timed. The five-minute table is a presentation
budget, not proof that every complete narrated demo fits it. Monitoring, restore
and accessibility evidence above were checked separately and retain their
original dates and scope.

A clean source archive of main `074bbc3`, without existing configuration or
dependencies, also bootstrapped on isolated local ports and a new PostgreSQL
volume: `make setup`, `make dev`, migrations, `make demo` (twelve GBP products,
one out of stock), frontend installation/start and fictional registration,
login, profile and logout passed. Local Stripe was not configured. The owned
stack was stopped afterward; its disposable volume was retained, not reset.

## Prepare a disposable local demo

For a fresh checkout, follow the [README quick start](../README.md#quick-start)
and [development configuration](development.md) first. Python 3.12, uv, running
Docker/Compose, Node 24.20.0 and npm 11.19.1 are required. No cloud account is
needed locally. The local
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
cannot grant admin access. Start the storefront from the repository root:

```sh
cd frontend
cp -n .env.example .env.local
# Existing file? Merge the session settings below before continuing.
npm ci
npm run dev
```

Browse `http://127.0.0.1:3000`, matching the example's exact `APP_ORIGIN` and
explicit local HTTP session permission. Preserve existing configuration. For an
isolated stack, change `API_BASE_URL` and `APP_ORIGIN` to its API/browser ports
as well as the [backend port settings](development.md#configuration).
If `.env.local` already exists, `cp -n` leaves it untouched. Before starting the
frontend, merge `APP_ORIGIN=http://127.0.0.1:3000` (your exact browser origin) and
`ALLOW_LOCAL_HTTP_SESSIONS=true` into that file, updating existing entries rather
than duplicating keys. Keep its API URL and other settings intact. Older files
with only `API_BASE_URL` cannot support account actions until this step is done.

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

`make import-catalog` loads the reviewed 60-product workspace catalog. It is
repeatable and atomic: the manifest and local photo files are checked before
any write, and the database transaction commits the whole import or rolls it
back. Reruns do not duplicate items, replenish stock, overwrite names, prices,
photos or descriptions, or recreate a product that was imported and later
deleted. An empty database receives the full catalog. A database that already
has the twelve original demo names, each exactly once, keeps those rows and
their ids, and receives only the additional products. Edited prices, stock,
reservations, carts and order snapshots stay as they are. The
`twelve-products` edition marker is left in place.

The command refuses the whole import when an original demo name matches more
than one row, or is missing while any products already exist. That avoids
guessing whether a product was renamed or deleted. Apply migrations first,
including revision 0010. Confirm the target before running it:

```sh
cd backend
uv run python -m app.bootstrap import-catalog --confirm-import
```

The flag acknowledges fictional catalog data. It does not detect a production
or hosted database. Do not point this command at hosted data. A hosted import
is a separate authorized step and needs a named revision plus backup or
recovery evidence.

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
