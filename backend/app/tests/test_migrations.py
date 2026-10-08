import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

BACKEND = Path(__file__).resolve().parents[2]


def test_migration_upgrade_downgrade_and_metadata(tmp_path):
    """Verify repeatable migrations, metadata and cart constraints on disposable storage."""
    database_url = os.environ.get(
        "TEST_MIGRATION_DATABASE_URL", f"sqlite:///{tmp_path / 'migration.db'}"
    )
    env = dict(os.environ, DATABASE_URL=database_url)

    def alembic(*args):
        """Run a checked migration command against the disposable test database."""
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    alembic("upgrade", "head")
    alembic("upgrade", "head")
    alembic("check")
    engine = create_engine(database_url)
    assert {
        "users",
        "products",
        "cart_lines",
        "demo_catalog_editions",
        "orders",
        "order_lines",
        "categories",
        "imported_catalog_items",
    } <= set(inspect(engine).get_table_names())
    schema = inspect(engine)
    assert schema.get_pk_constraint("cart_lines")["constrained_columns"] == [
        "user_id",
        "product_id",
    ]
    assert {
        constraint["name"] for constraint in schema.get_check_constraints("cart_lines")
    } == {"ck_cart_quantity"}
    check = schema.get_check_constraints("cart_lines")[0]["sqltext"]
    normalized = "".join(check.replace("(", "").replace(")", "").split()).lower()
    assert normalized == "quantity>=1andquantity<=99"
    foreign_keys = schema.get_foreign_keys("cart_lines")
    assert {
        (
            tuple(key["constrained_columns"]),
            key["referred_table"],
            tuple(key["referred_columns"]),
            key["options"].get("ondelete"),
        )
        for key in foreign_keys
    } == {
        (("user_id",), "users", ("id",), "CASCADE"),
        (("product_id",), "products", ("id",), "CASCADE"),
    }
    alembic("downgrade", "base")
    assert "users" not in inspect(engine).get_table_names()
    alembic("upgrade", "head")
    alembic("check")
    engine.dispose()


# TEST_MIGRATION_DATABASE_URL, when set, must point to a separate disposable DB.
def test_existing_product_migration_preserves_money_and_rejects_loss(tmp_path):
    """Preserve valid legacy prices and reject migration that would lose precision."""
    from decimal import Decimal

    from sqlalchemy import MetaData, Table, text

    url = os.environ.get(
        "TEST_MIGRATION_DATABASE_URL", f"sqlite:///{tmp_path / 'legacy.db'}"
    )
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args, check=True):
        """Run legacy migration steps, optionally retaining an expected failure result."""
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=check,
            capture_output=True,
            text=True,
        )

    # Only the dedicated disposable migration DB is reset here.
    migrate("downgrade", "base")
    migrate("upgrade", "0001")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products (name, price, stock) VALUES ('Legacy', 19.99, 4)"
            )
        )
    migrate("upgrade", "head")
    table = Table("products", MetaData(), autoload_with=engine)
    with engine.connect() as connection:
        product = connection.execute(table.select()).mappings().one()
        assert product["price"] == Decimal("19.99")
        assert product["currency"] == "GBP"
        assert product["stock"] == 4
    migrate("check")
    migrate("downgrade", "0001")
    with engine.begin() as connection:
        connection.execute(text("UPDATE products SET price=1.234"))
    failed = migrate("upgrade", "head", check=False)
    assert failed.returncode != 0
    assert "needs correction" in failed.stderr
    assert "currency" not in {
        column["name"] for column in inspect(engine).get_columns("products")
    }
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT price FROM products")).scalar_one() == 1.234
        )
    migrate("downgrade", "base")
    engine.dispose()


def test_category_migration_assigns_known_products_without_overwriting_edits(tmp_path):
    """Keep ids and edits, and only fill a category for known names or the fallback."""
    from decimal import Decimal

    from sqlalchemy import create_engine, inspect, text

    url = f"sqlite:///{tmp_path / 'categories.db'}"
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    migrate("upgrade", "0007")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products (name, description, price, currency, stock) "
                "VALUES "
                "('Task Light', 'Edited copy', 12.34, 'GBP', 5), "
                "('Renamed object', 'Keep me', 8.00, 'GBP', 3)"
            )
        )
        before = (
            connection.execute(
                text(
                    "SELECT id, name, description, price, stock FROM products ORDER BY id"
                )
            )
            .mappings()
            .all()
        )
    migrate("upgrade", "head")
    migrate("check")
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT products.id, products.name, products.description, "
                    "products.price, products.stock, categories.slug "
                    "FROM products JOIN categories ON categories.id = products.category_id "
                    "ORDER BY products.id"
                )
            )
            .mappings()
            .all()
        )
        assert (
            connection.execute(
                text("SELECT COUNT(*) FROM categories WHERE slug = 'all'")
            ).scalar_one()
            == 0
        )
    assert [row["id"] for row in rows] == [row["id"] for row in before]
    assert rows[0]["name"] == "Task Light"
    assert rows[0]["description"] == "Edited copy"
    assert Decimal(str(rows[0]["price"])) == Decimal("12.34")
    assert rows[0]["stock"] == 5
    assert rows[0]["slug"] == "lighting"
    assert rows[1]["name"] == "Renamed object"
    assert rows[1]["description"] == "Keep me"
    assert Decimal(str(rows[1]["price"])) == Decimal("8.00")
    assert rows[1]["stock"] == 3
    assert rows[1]["slug"] == "uncategorized"
    migrate("downgrade", "0007")
    assert "category_id" not in {
        column["name"] for column in inspect(engine).get_columns("products")
    }
    assert "categories" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        kept = (
            connection.execute(
                text("SELECT name, description, price, stock FROM products ORDER BY id")
            )
            .mappings()
            .all()
        )
    assert kept[0]["name"] == "Task Light"
    assert kept[0]["description"] == "Edited copy"
    assert Decimal(str(kept[0]["price"])) == Decimal("12.34")
    assert kept[1]["name"] == "Renamed object"
    migrate("downgrade", "base")
    engine.dispose()


def test_media_migration_assigns_known_photos_without_overwriting_edits(tmp_path):
    """A known name receives its photo; a renamed row and prior edits stay put."""
    from decimal import Decimal

    from sqlalchemy import create_engine, inspect, text

    url = f"sqlite:///{tmp_path / 'media.db'}"
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    migrate("upgrade", "0008")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products "
                "(name, description, price, currency, stock, category_id) "
                "VALUES "
                "('Task Light', 'Edited copy', 12.34, 'GBP', 5, "
                "(SELECT id FROM categories WHERE slug = 'lighting')), "
                "('Renamed object', 'Keep me', 8.00, 'GBP', 3, "
                "(SELECT id FROM categories WHERE slug = 'uncategorized'))"
            )
        )
    migrate("upgrade", "head")
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT name, description, price, stock, image_key, material "
                    "FROM products ORDER BY id"
                )
            )
            .mappings()
            .all()
        )
    assert rows[0]["name"] == "Task Light"
    assert rows[0]["description"] == "Edited copy"
    assert Decimal(str(rows[0]["price"])) == Decimal("12.34")
    assert rows[0]["stock"] == 5
    assert rows[0]["image_key"] == "lamp"
    assert rows[0]["material"] == "Aluminium"
    assert rows[1]["name"] == "Renamed object"
    assert rows[1]["description"] == "Keep me"
    assert rows[1]["image_key"] is None
    assert rows[1]["material"] is None
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO products "
                    "(name, price, currency, stock, category_id, image_key) "
                    "VALUES ('Loose photo', 1.00, 'GBP', 1, "
                    "(SELECT id FROM categories WHERE slug = 'lighting'), 'lamp')"
                )
            )
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products "
                "(name, price, currency, stock, category_id, image_key, image_alt) "
                "VALUES ('Paired photo', 1.00, 'GBP', 1, "
                "(SELECT id FROM categories WHERE slug = 'lighting'), "
                "'lamp', 'Representative photograph of a desk lamp')"
            )
        )
    migrate("downgrade", "0008")
    assert "image_key" not in {
        column["name"] for column in inspect(engine).get_columns("products")
    }
    with engine.connect() as connection:
        kept = (
            connection.execute(
                text("SELECT name, description FROM products ORDER BY id")
            )
            .mappings()
            .all()
        )
    assert kept[0]["description"] == "Edited copy"
    migrate("downgrade", "base")
    engine.dispose()


def test_media_migration_skips_a_duplicated_demo_name(tmp_path):
    """Two products with a demo name are ambiguous, so neither receives facts."""
    from sqlalchemy import create_engine, text

    url = f"sqlite:///{tmp_path / 'duplicate-media.db'}"
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    migrate("upgrade", "0008")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products "
                "(name, description, price, currency, stock, category_id) "
                "VALUES "
                "('Task Light', 'Admin copy', 4.00, 'GBP', 2, "
                "(SELECT id FROM categories WHERE slug = 'lighting')), "
                "('Task Light', 'Other copy', 9.00, 'GBP', 4, "
                "(SELECT id FROM categories WHERE slug = 'lighting')), "
                "('Felt Desk Mat', 'Kept', 29.50, 'GBP', 1, "
                "(SELECT id FROM categories WHERE slug = 'uncategorized'))"
            )
        )
    migrate("upgrade", "head")
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    "SELECT name, description, image_key, material "
                    "FROM products ORDER BY id"
                )
            )
            .mappings()
            .all()
        )
    assert [row["image_key"] for row in rows[:2]] == [None, None]
    assert [row["material"] for row in rows[:2]] == [None, None]
    assert rows[0]["description"] == "Admin copy"
    assert rows[1]["description"] == "Other copy"
    assert rows[2]["name"] == "Felt Desk Mat"
    assert rows[2]["image_key"] == "mat"
    assert rows[2]["material"] == "Felt"
    migrate("downgrade", "base")
    engine.dispose()


def test_media_migration_freezes_its_allowlist():
    """Revision 0009 must not follow later edits to the live catalog constants."""
    source = (BACKEND / "alembic/versions/0009_product_media_and_facts.py").read_text()
    assert "catalog_media" not in source
    assert "image_alt IS NOT NULL" in source
    assert '"Task Light"' in source
    assert '"lamp"' in source


def test_catalog_identity_migration_adds_schema_only(tmp_path):
    """Revision 0010 must not copy, edit, or delete product rows."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError

    source = (BACKEND / "alembic/versions/0010_catalog_import_identity.py").read_text()
    assert "catalog_manifest" not in source
    assert "catalog_media" not in source
    assert "UPDATE" not in source.upper()
    assert "catalog_key IS NULL OR" in source
    url = f"sqlite:///{tmp_path / 'catalog-identity.db'}"
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    migrate("upgrade", "0009")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO products "
                "(name, description, price, currency, stock, category_id) "
                "VALUES ('Kept name', 'Kept copy', 4.50, 'GBP', 2, "
                "(SELECT id FROM categories WHERE slug = 'lighting'))"
            )
        )
    migrate("upgrade", "head")
    migrate("check")
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    "SELECT name, description, price, stock, catalog_key FROM products"
                )
            )
            .mappings()
            .one()
        )
        ledger = connection.execute(
            text("SELECT COUNT(*) FROM imported_catalog_items")
        ).scalar_one()
    assert row["name"] == "Kept name"
    assert row["description"] == "Kept copy"
    assert row["stock"] == 2
    assert row["catalog_key"] is None
    assert ledger == 0
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO products "
                    "(name, price, currency, stock, category_id, catalog_key) "
                    "VALUES ('Blank key', 1.00, 'GBP', 1, "
                    "(SELECT id FROM categories WHERE slug = 'lighting'), '')"
                )
            )
    migrate("downgrade", "0009")
    assert "catalog_key" not in {
        column["name"] for column in inspect(engine).get_columns("products")
    }
    assert "imported_catalog_items" not in inspect(engine).get_table_names()
    migrate("downgrade", "base")
    engine.dispose()


def test_catalog_identity_migration_preserves_cart_lines(tmp_path):
    """Rebuilding products for the catalog key must not cascade-delete carts."""
    from sqlalchemy import create_engine, text

    url = f"sqlite:///{tmp_path / 'catalog-carts.db'}"
    env = dict(os.environ, DATABASE_URL=url)

    def migrate(*args):
        completed = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed

    migrate("upgrade", "0009")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(
            text(
                "INSERT INTO users (email, hashed_password, is_active, is_superuser) "
                "VALUES ('cart@example.com', 'hash', 1, 0)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO products "
                "(name, description, price, currency, stock, category_id) "
                "VALUES ('Kept', 'Kept copy', 4.50, 'GBP', 2, "
                "(SELECT id FROM categories WHERE slug = 'lighting'))"
            )
        )
        connection.execute(
            text(
                "INSERT INTO cart_lines (user_id, product_id, quantity) "
                "VALUES ("
                "(SELECT id FROM users WHERE email = 'cart@example.com'), "
                "(SELECT id FROM products WHERE name = 'Kept'), 2)"
            )
        )
    migrate("upgrade", "head")
    with engine.connect() as connection:
        cart = (
            connection.execute(
                text(
                    "SELECT cart_lines.quantity, products.name, products.catalog_key "
                    "FROM cart_lines JOIN products ON products.id = cart_lines.product_id"
                )
            )
            .mappings()
            .one()
        )
        parked = connection.execute(
            text(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE name = 'cart_lines_import_park'"
            )
        ).scalar_one()
    assert cart["quantity"] == 2
    assert cart["name"] == "Kept"
    assert cart["catalog_key"] is None
    assert parked == 0
    migrate("downgrade", "0009")
    with engine.connect() as connection:
        quantity = connection.execute(
            text("SELECT quantity FROM cart_lines")
        ).scalar_one()
    assert quantity == 2
    migrate("downgrade", "base")
    engine.dispose()
