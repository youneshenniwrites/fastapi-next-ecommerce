"""Persist customer draft order snapshots.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    """Create draft storage without altering carts, products or inventory."""
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("currency", sa.String(3), server_default="GBP", nullable=False),
        sa.Column("total", sa.Numeric(16, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("status = 'draft'", name="ck_orders_status"),
        sa.CheckConstraint("currency = 'GBP'", name="ck_orders_currency"),
        sa.CheckConstraint(
            "total >= 0 AND total <= 98999999999901.00", name="ck_orders_total"
        ),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_table(
        "order_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.UniqueConstraint("order_id", "product_id", name="uq_order_lines_product"),
        sa.CheckConstraint(
            "quantity >= 1 AND quantity <= 99", name="ck_order_lines_quantity"
        ),
        sa.CheckConstraint(
            "unit_price >= 0 AND unit_price <= 9999999999.99",
            name="ck_order_lines_price",
        ),
        sa.CheckConstraint("product_id >= 1", name="ck_order_lines_product_id"),
        sa.CheckConstraint(
            "length(trim(product_name)) >= 1 AND length(product_name) <= 255",
            name="ck_order_lines_name",
        ),
    )


def downgrade():
    """Remove draft records; only rehearse against disposable databases."""
    op.drop_table("order_lines")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_table("orders")
