"""Add a catalog identity and an import ledger without rewriting products.

Revision ID: 0010
Revises: 0009

This revision only adds schema. Product rows, prices, stock, photos and the
twelve-product edition are imported by an explicit operator command.
"""

import sqlalchemy as sa

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

_CATALOG_KEY_CHECK = (
    "catalog_key IS NULL OR (length(catalog_key) >= 1 AND length(catalog_key) <= 64)"
)


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("LOCK TABLE products IN ACCESS EXCLUSIVE MODE"))
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("catalog_key", sa.String(length=64), nullable=True))
        batch.create_check_constraint("ck_products_catalog_key", _CATALOG_KEY_CHECK)
        batch.create_unique_constraint("uq_products_catalog_key", ["catalog_key"])
    op.create_table(
        "imported_catalog_items",
        sa.Column("catalog_key", sa.String(length=64), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "length(catalog_key) >= 1 AND length(catalog_key) <= 64",
            name="ck_imported_catalog_items_key",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_imported_catalog_items_product_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("product_id", name="uq_imported_catalog_items_product_id"),
    )


def downgrade():
    op.drop_table("imported_catalog_items")
    with op.batch_alter_table("products") as batch:
        batch.drop_constraint("uq_products_catalog_key", type_="unique")
        batch.drop_constraint("ck_products_catalog_key", type_="check")
        batch.drop_column("catalog_key")
