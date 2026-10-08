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


def _park_cart_lines(connection) -> None:
    """Move cart rows aside so a SQLite product rebuild cannot cascade-delete them."""
    connection.execute(
        sa.text(
            "CREATE TABLE cart_lines_import_park ("
            "user_id INTEGER NOT NULL, "
            "product_id INTEGER NOT NULL, "
            "quantity INTEGER NOT NULL, "
            "PRIMARY KEY (user_id, product_id))"
        )
    )
    connection.execute(
        sa.text(
            "INSERT INTO cart_lines_import_park (user_id, product_id, quantity) "
            "SELECT user_id, product_id, quantity FROM cart_lines"
        )
    )
    connection.execute(sa.text("DROP TABLE cart_lines"))


def _restore_cart_lines(connection) -> None:
    op.create_table(
        "cart_lines",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity >= 1 AND quantity <= 99", name="ck_cart_quantity"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "product_id"),
    )
    op.create_index("ix_cart_lines_product_id", "cart_lines", ["product_id"])
    connection.execute(
        sa.text(
            "INSERT INTO cart_lines (user_id, product_id, quantity) "
            "SELECT user_id, product_id, quantity FROM cart_lines_import_park"
        )
    )
    connection.execute(sa.text("DROP TABLE cart_lines_import_park"))


def _rebuild_products(connection) -> None:
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        _park_cart_lines(connection)
    try:
        if connection.dialect.name == "postgresql":
            connection.execute(sa.text("LOCK TABLE products IN ACCESS EXCLUSIVE MODE"))
        with op.batch_alter_table("products") as batch:
            batch.add_column(
                sa.Column("catalog_key", sa.String(length=64), nullable=True)
            )
            batch.create_check_constraint("ck_products_catalog_key", _CATALOG_KEY_CHECK)
            batch.create_unique_constraint("uq_products_catalog_key", ["catalog_key"])
    finally:
        if sqlite:
            _restore_cart_lines(connection)


def upgrade():
    connection = op.get_bind()
    _rebuild_products(connection)
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
    connection = op.get_bind()
    op.drop_table("imported_catalog_items")
    sqlite = connection.dialect.name == "sqlite"
    if sqlite:
        _park_cart_lines(connection)
    try:
        with op.batch_alter_table("products") as batch:
            batch.drop_constraint("uq_products_catalog_key", type_="unique")
            batch.drop_constraint("ck_products_catalog_key", type_="check")
            batch.drop_column("catalog_key")
    finally:
        if sqlite:
            _restore_cart_lines(connection)
