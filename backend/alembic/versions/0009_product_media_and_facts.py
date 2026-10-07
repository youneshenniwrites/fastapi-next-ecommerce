"""Store an allowlisted photo and optional stated facts without rewriting edits.

Revision ID: 0009
Revises: 0008

The allowlist and demo backfill below are frozen for this revision. A later
change to the live catalog media belongs in a new migration.
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

# Copied from the catalog at the time this revision was added. Do not replace
# these with an import of the live application constants.
_IMAGE_KEYS = (
    "stand",
    "mat",
    "lamp",
    "tray",
    "notebooks",
    "cup",
    "keyboard",
    "headphones",
    "bottle",
    "planter",
    "clock",
    "mouse",
)
_IMAGE_KEY_CHECK = (
    "image_key IS NULL OR image_key IN ("
    + ", ".join(f"'{key}'" for key in _IMAGE_KEYS)
    + ")"
)
_IMAGE_PAIR_CHECK = (
    "(image_key IS NULL AND image_alt IS NULL) OR "
    "(image_key IS NOT NULL AND image_alt IS NOT NULL "
    "AND length(trim(image_alt)) >= 1 AND length(image_alt) <= 200)"
)
_DEMO_MEDIA = (
    {
        "name": "Oak Monitor Stand",
        "image_key": "stand",
        "image_alt": "Representative photograph of a wooden monitor stand",
        "material": "Solid oak",
        "width_mm": 540,
        "depth_mm": 220,
        "height_mm": 80,
    },
    {
        "name": "Felt Desk Mat",
        "image_key": "mat",
        "image_alt": "Representative photograph of a felt desk mat",
        "material": "Felt",
        "width_mm": 800,
        "depth_mm": 400,
        "height_mm": None,
    },
    {
        "name": "Task Light",
        "image_key": "lamp",
        "image_alt": "Representative photograph of a desk lamp",
        "material": "Aluminium",
        "width_mm": 150,
        "depth_mm": 150,
        "height_mm": 420,
    },
    {
        "name": "Cable Tray",
        "image_key": "tray",
        "image_alt": "Representative photograph of a wooden desk tray",
        "material": "Wood",
        "width_mm": 300,
        "depth_mm": 200,
        "height_mm": 40,
    },
    {
        "name": "Notebook Set",
        "image_key": "notebooks",
        "image_alt": "Representative photograph of two notebooks",
        "material": "Paper",
        "width_mm": 140,
        "depth_mm": 15,
        "height_mm": 210,
    },
    {
        "name": "Ceramic Pen Cup",
        "image_key": "cup",
        "image_alt": "Representative photograph of a ceramic cup holding pencils",
        "material": "Ceramic",
        "width_mm": 90,
        "depth_mm": 90,
        "height_mm": 100,
    },
    {
        "name": "Compact Keyboard",
        "image_key": "keyboard",
        "image_alt": "Representative photograph of a computer keyboard",
        "material": "Plastic",
        "width_mm": 310,
        "depth_mm": 120,
        "height_mm": 22,
    },
    {
        "name": "Focus Headphones",
        "image_key": "headphones",
        "image_alt": "Representative photograph of over-ear headphones",
        "material": "Plastic",
        "width_mm": None,
        "depth_mm": None,
        "height_mm": None,
    },
    {
        "name": "Insulated Bottle",
        "image_key": "bottle",
        "image_alt": "Representative photograph of a steel bottle",
        "material": "Steel",
        "width_mm": 75,
        "depth_mm": 75,
        "height_mm": 260,
    },
    {
        "name": "Handled Planter",
        "image_key": "planter",
        "image_alt": "Representative photograph of a ceramic planter",
        "material": "Ceramic",
        "width_mm": 140,
        "depth_mm": 140,
        "height_mm": 130,
    },
    {
        "name": "Analogue Desk Clock",
        "image_key": "clock",
        "image_alt": "Representative photograph of a round analogue clock",
        "material": None,
        "width_mm": None,
        "depth_mm": None,
        "height_mm": None,
    },
    {
        "name": "Wireless Mouse",
        "image_key": "mouse",
        "image_alt": "Representative photograph of a wireless computer mouse",
        "material": "Plastic",
        "width_mm": 110,
        "depth_mm": 62,
        "height_mm": 38,
    },
)


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
        batch.create_check_constraint("ck_products_image_key", _IMAGE_KEY_CHECK)
        batch.create_check_constraint("ck_products_image_pair", _IMAGE_PAIR_CHECK)
        batch.create_check_constraint(
            "ck_products_material",
            "material IS NULL OR (length(trim(material)) >= 1 AND length(material) <= 80)",
        )
        for column in ("width_mm", "depth_mm", "height_mm"):
            batch.create_check_constraint(
                f"ck_products_{column}",
                f"{column} IS NULL OR ({column} >= 1 AND {column} <= 10000)",
            )

    # Fill an empty photo only when one row has that demo name. Names are not
    # unique, so a second product with the same name is left untouched. Prices,
    # stock, descriptions and ids stay as edited. A renamed product has no photo.
    counts = dict(
        connection.execute(
            sa.text("SELECT name, COUNT(*) FROM products GROUP BY name")
        ).all()
    )
    for media in _DEMO_MEDIA:
        if counts.get(media["name"]) != 1:
            continue
        connection.execute(
            sa.text(
                "UPDATE products SET image_key = :image_key, image_alt = :image_alt, "
                "material = :material, width_mm = :width_mm, depth_mm = :depth_mm, "
                "height_mm = :height_mm "
                "WHERE name = :name AND image_key IS NULL"
            ),
            media,
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
