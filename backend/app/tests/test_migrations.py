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
    assert {"users", "products", "cart_lines"} <= set(inspect(engine).get_table_names())
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
