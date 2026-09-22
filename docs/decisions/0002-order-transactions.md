# ADR 0002: order snapshots and checkout transactions

Date: 21 September 2026. Status: accepted for VIN-29 implementation.
Architecture review: VIN-118 → VIN-119 → VIN-120. This records the intended epic
architecture; draft persistence is delivered by VIN-118; VIN-119 adds placement.

## Decision

FastAPI owns order money, permissions and state. Routes parse HTTP, shared auth
resolves the active customer, and a domain service owns the database transaction.
CRUD read helpers never commit. SQLAlchemy authentication may already begin the
request transaction; the service commits or rolls back that transaction once.
No transaction spans a payment-provider call.

VIN-118 accepts 1–100 distinct product IDs with quantities 1–99. It saves an
immutable draft quotation from one catalog SELECT, with GBP name/price snapshots
and an exact Decimal total. NUMERIC(16,2) accommodates the maximum supported order
(100 × 99 × £9,999,999,999.99). Line totals are derived, not separately stored.
Database checks constrain money, quantity, currency and the currently supported
state. Cross-row total equality is maintained by the service, not a SQL CHECK.

Product IDs on lines are historical identifiers, deliberately not cascading
foreign keys: deleting or renaming a catalog product must preserve order evidence.
User deletion is restricted while orders exist. Customer list/detail queries
always filter ownership, including for admins. Cursor pagination bounds list reads.
VIN-118 introduced no draft update/delete or placement endpoint. VIN-119 adds
the placement endpoint described below. Draft retries
can create multiple quotations; they cannot charge money, reserve stock or clear a
cart. Existing per-customer write throttling applies. Retention/expiry of unused
drafts is a later maintenance concern, not an unbounded list response.

## Placement (VIN-119) and future payment (VIN-30)

Placement revalidates the draft's product IDs, quantities, current prices and stock.
It creates final immutable placement snapshots; draft amounts are never a promise
of final pricing. A changed quotation must return a conflict for customer
reconfirmation before inventory is claimed. No client-supplied total is trusted.

One service transaction claims the customer-scoped idempotency key, locks products
in deterministic ID order (or uses guarded updates), writes final order state,
decrements inventory and clears the purchased cart lines. Cart disposition must
serialize with cart writes and preserve unrelated items. Equal-key/equal-request
retries return the original result; incompatible reuse conflicts. PostgreSQL
concurrency, rollback and lost-response tests are VIN-119 acceptance requirements.

VIN-30 adds a provider adapter and pending-payment lifecycle. Persisted totals
create hosted sandbox sessions; verified, deduplicated webhooks establish payment
state. Expiry/cancellation release inventory exactly once; redirects cannot mark
paid. These states require a new migration, not loosening draft rules prematurely.

## Alternatives and limits

Rejected: browser-owned totals, live joins for historical prices, route-level
multi-commit CRUD, and early order placement without atomic inventory/idempotency.
No microservice, event bus or payment abstraction is added before a concrete caller.
At higher load, draft retention and paginated query plans need measurement; no
claim of distributed throttling is made. Next.js will consume the generated API
contract in VIN-120 without owning transactions or payment state.

## Placement contract

`POST /api/v1/orders/{order_id}/place` accepts an `Idempotency-Key` header
(1–128 ASCII letters, digits, underscores or hyphens). Keys are scoped to the
customer and identify one draft ID. Same-key/same-draft retries return the original
placed order; different draft reuse and alternate keys for a placed order conflict.
A successful placement returns 200, including retries. Failed transactions do not
consume the key. Order amounts and lines remain immutable quotation snapshots;
price changes require a fresh draft and customer confirmation.

Placement locks the customer row first, matching all existing cart writers, then
locks products in ascending ID order. Every purchased cart line must still exist
with the quoted quantity; otherwise return 409 without changes. Successful
placement removes those exact lines and preserves unrelated items. Customer
serialization also prevents simultaneous same-key inserts; a database unique
constraint provides a second guard. The service commits once and rolls back every
mutation on failure. Status `placed` means inventory claimed, not paid or fulfilled.
No payment collection or inventory expiry is delivered in this slice.
