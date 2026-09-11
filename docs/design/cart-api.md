# Persistent cart API

Each active signed-in customer has one logical cart: rows in `cart_lines`, keyed
by `(user_id, product_id)`. An empty cart has no rows. Bearer authentication uses
the existing active-user dependency; clients cannot supply ownership or prices.
The storefront integration is tracked separately in #72.

## Contract

- `GET /api/v1/cart/`: current items, product details, quantity, `available`,
  two-place GBP `line_total` and `subtotal`. Successful responses are private/no-store.
- `PUT /api/v1/cart/items/{product_id}` with `{"quantity": 2}`: set an absolute
  integer quantity from 1 to 99 and return the updated cart. Extra fields are
  rejected. A missing product returns 404; insufficient stock for a new line or
  increase returns 409. Invalid bodies/identifiers return 422.
- `DELETE /api/v1/cart/items/{product_id}`: remove your own line; return 204 even
  if absent. There is no endpoint taking another customer's ID or a cart-line ID.

Example in Swagger: register, authorize with email/password, obtain a product ID
from the public catalog, PUT its quantity, GET the cart, then DELETE the line.
A fresh login restores saved rows. Tokens are not persisted in the cart.

## Prices, stock and transactions

Prices are current backend product prices, calculated using Decimal; carts do
not freeze prices or reserve inventory. A later shortage retains the saved
quantity and returns `available: false`. Unchanged quantities and reductions
remain permitted even when still above stock. Checkout (#29) must independently
revalidate prices and reserve inventory atomically before creating an order.

PostgreSQL mutations lock the customer row, including an initially empty cart,
then the affected product for quantity writes. Concurrent writes to a customer's
cart serialize; the last serialized absolute write wins. Repeating a PUT does
not add quantities or duplicate lines. Deletion participates in the same customer
lock. Responses reflect a transaction snapshot, not a guarantee against later
changes. Reads obtain quantities and product prices in one SQL statement.

The composite primary key prevents duplicate products per customer; foreign keys
cascade product/customer deletion, and a check constraint enforces quantity
bounds. Deleting a product intentionally removes it from all carts. Migration
0003 only adds a table/index; it does not modify existing users or products.
Production applies it through the existing deployment workflow.

## Verification

`make check` covers API behavior, ownership, invalid input, exact money,
persistence, deletion and migration metadata. The PostgreSQL CI job runs the same
suite plus concurrent requests using separate database sessions. SQLite tests are
sequential and explicitly enable foreign keys; they do not claim to validate row
locks. All tests use disposable databases.
