import os
import subprocess
import sys
from pathlib import Path

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
