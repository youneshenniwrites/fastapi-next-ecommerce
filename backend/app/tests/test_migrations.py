import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

BACKEND = Path(__file__).resolve().parents[2]


def test_migration_upgrade_downgrade_and_metadata(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    env = dict(os.environ, DATABASE_URL=database_url)

    def alembic(*args):
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
    assert {"users", "products"} <= set(inspect(engine).get_table_names())
    alembic("downgrade", "base")
    assert "users" not in inspect(engine).get_table_names()
    alembic("upgrade", "head")
    alembic("check")
    engine.dispose()
