"""Add one flat category per product without rewriting existing catalog edits.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa

from alembic import op
from app.catalog_taxonomy import CATEGORIES, PRODUCT_CATEGORIES, UNCATEGORIZED_SLUG

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "length(slug) >= 1 AND length(slug) <= 64",
            name="ck_categories_slug_length",
        ),
        sa.CheckConstraint("slug <> 'all'", name="ck_categories_slug_not_all"),
        sa.CheckConstraint(
            "length(trim(name)) >= 1 AND length(name) <= 80",
            name="ck_categories_name_length",
        ),
        sa.CheckConstraint("position >= 0", name="ck_categories_position"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    categories = sa.table(
        "categories",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("position", sa.Integer),
    )
    op.bulk_insert(
        categories,
        [
            {"slug": slug, "name": name, "position": position}
            for slug, name, position in CATEGORIES
        ],
    )

    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("LOCK TABLE products IN ACCESS EXCLUSIVE MODE"))
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("category_id", sa.Integer(), nullable=True))

    # Set only category_id. Names, descriptions, prices, stock and ids stay as edited.
    for name, slug in PRODUCT_CATEGORIES.items():
        connection.execute(
            sa.text(
                "UPDATE products SET category_id = ("
                "SELECT id FROM categories WHERE slug = :slug"
                ") WHERE name = :name AND category_id IS NULL"
            ),
            {"slug": slug, "name": name},
        )
    connection.execute(
        sa.text(
            "UPDATE products SET category_id = ("
            "SELECT id FROM categories WHERE slug = :slug"
            ") WHERE category_id IS NULL"
        ),
        {"slug": UNCATEGORIZED_SLUG},
    )
    missing = connection.execute(
        sa.text("SELECT COUNT(*) FROM products WHERE category_id IS NULL")
    ).scalar_one()
    if missing:
        raise RuntimeError(
            "Category assignment left products unset; no further product changes were made"
        )

    with op.batch_alter_table("products") as batch:
        batch.alter_column("category_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key(
            "fk_products_category_id",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_products_category_id", ["category_id"])


def downgrade():
    with op.batch_alter_table("products") as batch:
        batch.drop_index("ix_products_category_id")
        batch.drop_constraint("fk_products_category_id", type_="foreignkey")
        batch.drop_column("category_id")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_table("categories")
