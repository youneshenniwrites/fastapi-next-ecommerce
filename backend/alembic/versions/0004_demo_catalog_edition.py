"""Track the explicit demo catalog expansion without changing product identities.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "demo_catalog_editions",
        sa.Column("edition", sa.String(length=64), primary_key=True),
    )


def downgrade():
    # Products and carts survive; expansion history is lost on schema rollback.
    op.drop_table("demo_catalog_editions")
