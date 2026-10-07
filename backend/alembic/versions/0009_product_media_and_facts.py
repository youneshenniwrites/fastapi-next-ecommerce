"""Store an allowlisted photo and optional stated facts without rewriting edits.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa

from alembic import op
from app.catalog_media import PRODUCT_MEDIA, image_key_sql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("LOCK TABLE products IN ACCESS EXCLUSIVE MODE"))
    with op.batch_alter_table("products") as batch:
        batch.add_column(sa.Column("image_key", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("image_alt", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("material", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("width_mm", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("depth_mm", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("height_mm", sa.Integer(), nullable=True))
        batch.create_check_constraint("ck_products_image_key", image_key_sql())
        batch.create_check_constraint(
            "ck_products_image_pair",
            "(image_key IS NULL AND image_alt IS NULL) OR "
            "(image_key IS NOT NULL AND length(trim(image_alt)) >= 1 "
            "AND length(image_alt) <= 200)",
        )
        batch.create_check_constraint(
            "ck_products_material",
            "material IS NULL OR (length(trim(material)) >= 1 AND length(material) <= 80)",
        )
        for column in ("width_mm", "depth_mm", "height_mm"):
            batch.create_check_constraint(
                f"ck_products_{column}",
                f"{column} IS NULL OR ({column} >= 1 AND {column} <= 10000)",
            )

    # Fill only empty photo slots for the known demo names. Names, prices, stock,
    # descriptions and ids stay as edited. A renamed product is left without a photo.
    for name, media in PRODUCT_MEDIA.items():
        connection.execute(
            sa.text(
                "UPDATE products SET image_key = :image_key, image_alt = :image_alt, "
                "material = :material, width_mm = :width_mm, depth_mm = :depth_mm, "
                "height_mm = :height_mm "
                "WHERE name = :name AND image_key IS NULL"
            ),
            {
                "name": name,
                "image_key": media["image_key"],
                "image_alt": media["image_alt"],
                "material": media.get("material"),
                "width_mm": media.get("width_mm"),
                "depth_mm": media.get("depth_mm"),
                "height_mm": media.get("height_mm"),
            },
        )


def downgrade():
    with op.batch_alter_table("products") as batch:
        for name in (
            "ck_products_image_key",
            "ck_products_image_pair",
            "ck_products_material",
            "ck_products_width_mm",
            "ck_products_depth_mm",
            "ck_products_height_mm",
        ):
            batch.drop_constraint(name, type_="check")
        for column in (
            "height_mm",
            "depth_mm",
            "width_mm",
            "material",
            "image_alt",
            "image_key",
        ):
            batch.drop_column(column)
