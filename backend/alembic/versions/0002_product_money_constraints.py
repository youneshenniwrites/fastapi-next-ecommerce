"""Store GBP prices as decimals and enforce catalog invariants."""

from decimal import Decimal, InvalidOperation

import sqlalchemy as sa

from alembic import context, op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise RuntimeError(
            "Migration 0002 requires an online connection for legacy-data validation"
        )
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("LOCK TABLE products IN ACCESS EXCLUSIVE MODE"))
    # Refuse lossy conversions before issuing DDL. Operators must correct invalid
    # legacy data deliberately; this migration never rounds or deletes products.
    rows = connection.execute(
        sa.text("SELECT id, name, description, price, stock FROM products")
    )
    for row in rows.mappings():
        try:
            price = Decimal(str(row["price"]))
            valid_price = (
                price.is_finite()
                and 0 <= price <= Decimal("9999999999.99")
                and price == price.quantize(Decimal("0.01"))
            )
        except InvalidOperation:
            valid_price = False
        if (
            not valid_price
            or row["stock"] is None
            or not 0 <= row["stock"] <= 2147483647
            or not row["name"].strip()
            or len(row["name"]) > 255
            or (row["description"] is not None and len(row["description"]) > 10000)
        ):
            raise ValueError(
                f"Product {row['id']} needs correction before migration 0002; no data was changed"
            )

    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "price",
            existing_type=sa.Float(),
            type_=sa.Numeric(12, 2),
            existing_nullable=False,
        )
        batch.alter_column("stock", existing_type=sa.Integer(), nullable=False)
        batch.add_column(
            sa.Column("currency", sa.String(3), nullable=False, server_default="GBP")
        )
        batch.create_check_constraint(
            "ck_products_price_range", "price >= 0 AND price <= 9999999999.99"
        )
        batch.create_check_constraint(
            "ck_products_stock_range", "stock >= 0 AND stock <= 2147483647"
        )
        batch.create_check_constraint("ck_products_currency", "currency = 'GBP'")
        batch.create_check_constraint(
            "ck_products_name_length", "length(trim(name)) >= 1 AND length(name) <= 255"
        )
        batch.create_check_constraint(
            "ck_products_description_length",
            "description IS NULL OR length(description) <= 10000",
        )


def downgrade():
    # Downgrade returns to legacy floating-point storage and removes currency.
    with op.batch_alter_table("products") as batch:
        for name in (
            "ck_products_price_range",
            "ck_products_stock_range",
            "ck_products_currency",
            "ck_products_name_length",
            "ck_products_description_length",
        ):
            batch.drop_constraint(name, type_="check")
        batch.drop_column("currency")
        batch.alter_column("stock", existing_type=sa.Integer(), nullable=True)
        batch.alter_column(
            "price",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Float(),
            existing_nullable=False,
        )
