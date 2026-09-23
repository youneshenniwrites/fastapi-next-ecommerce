"""Add explicit sandbox reservations; legacy placed orders remain unmanaged."""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products") as batch:
        batch.add_column(
            sa.Column(
                "reserved_stock", sa.Integer(), nullable=False, server_default="0"
            )
        )
        batch.create_check_constraint(
            "ck_products_reservation_range",
            "reserved_stock >= 0 AND stock + reserved_stock <= 2147483647",
        )
    with op.batch_alter_table("orders") as batch:
        for name, kind in (
            ("payment_status", sa.String(20)),
            ("payment_reference", sa.String(36)),
            ("payment_session_id", sa.String(255)),
            ("payment_checkout_url", sa.String(2048)),
            ("payment_request", sa.Text()),
            ("payment_expires_at", sa.DateTime(timezone=True)),
            ("payment_started_at", sa.DateTime(timezone=True)),
            ("inventory_released_at", sa.DateTime(timezone=True)),
        ):
            batch.add_column(sa.Column(name, kind, nullable=True))
        batch.create_unique_constraint(
            "uq_orders_payment_reference", ["payment_reference"]
        )
        batch.create_unique_constraint(
            "uq_orders_payment_session_id", ["payment_session_id"]
        )
        batch.create_check_constraint(
            "ck_orders_payment_status",
            "payment_status IS NULL OR payment_status IN ('pending', 'paid', 'failed', 'cancelled', 'expired')",
        )
        batch.create_check_constraint(
            "ck_orders_payment_managed",
            "payment_status IS NULL OR (status = 'placed' AND payment_reference IS NOT NULL AND payment_expires_at IS NOT NULL)",
        )
        batch.create_check_constraint(
            "ck_orders_payment_release",
            "inventory_released_at IS NULL OR payment_status IN ('failed', 'cancelled', 'expired')",
        )
    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text("SELECT count(*) FROM orders WHERE payment_status IS NOT NULL")
        )
        .scalar()
    ):
        raise RuntimeError("Cannot downgrade while managed payment orders exist")
    op.drop_table("payment_events")
    with op.batch_alter_table("orders") as batch:
        for name in (
            "ck_orders_payment_status",
            "ck_orders_payment_managed",
            "ck_orders_payment_release",
        ):
            batch.drop_constraint(name, type_="check")
        for name in ("uq_orders_payment_reference", "uq_orders_payment_session_id"):
            batch.drop_constraint(name, type_="unique")
        for name in (
            "payment_status",
            "payment_reference",
            "payment_session_id",
            "payment_checkout_url",
            "payment_request",
            "payment_expires_at",
            "payment_started_at",
            "inventory_released_at",
        ):
            batch.drop_column(name)
    with op.batch_alter_table("products") as batch:
        batch.drop_constraint("ck_products_reservation_range", type_="check")
        batch.drop_column("reserved_stock")
