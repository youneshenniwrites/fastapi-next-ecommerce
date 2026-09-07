"""Apply migrations; retained for compatibility with the old init-db command."""

from pathlib import Path

from alembic.config import Config

from alembic import command


def init_db():
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")


if __name__ == "__main__":
    init_db()
