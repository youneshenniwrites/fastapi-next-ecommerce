# Reproducible portfolio demo

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
