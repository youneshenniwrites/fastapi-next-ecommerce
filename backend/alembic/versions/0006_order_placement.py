"""Allow atomic order placement and customer-scoped retry keys."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    """Preserve drafts while adding placed state and unique retry identity."""
    with op.batch_alter_table("orders") as batch:
        batch.drop_constraint("ck_orders_status", type_="check")
        batch.create_check_constraint(
            "ck_orders_status", "status IN ('draft', 'placed')"
        )
        batch.add_column(sa.Column("idempotency_key", sa.String(128), nullable=True))
        batch.create_unique_constraint(
            "uq_orders_customer_key", ["user_id", "idempotency_key"]
        )


def downgrade():
    """Refuse to erase placed-order identity; rehearse only on disposable data."""
    if (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM orders WHERE status = 'placed'"))
        .scalar()
    ):
        raise RuntimeError("Cannot downgrade while placed orders exist")
    with op.batch_alter_table("orders") as batch:
        batch.drop_constraint("uq_orders_customer_key", type_="unique")
        batch.drop_column("idempotency_key")
        batch.drop_constraint("ck_orders_status", type_="check")
        batch.create_check_constraint("ck_orders_status", "status = 'draft'")
