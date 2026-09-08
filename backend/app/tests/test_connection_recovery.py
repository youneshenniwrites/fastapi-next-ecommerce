import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.db.session import create_db_engine


def test_replaces_connection_closed_while_idle():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip("Requires disposable PostgreSQL TEST_DATABASE_URL")

    engine = create_db_engine(url)
    control = create_engine(url, poolclass=NullPool)
    try:
        with engine.connect() as connection:
            old_pid = connection.scalar(text("SELECT pg_backend_pid()"))
        # Only terminate the connection this test opened, after returning it
        # to the pool. This models suspended hosting, without restarting a DB.
        with control.connect() as connection:
            assert connection.scalar(
                text("SELECT pg_terminate_backend(:pid)"), {"pid": old_pid}
            )
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
            assert connection.scalar(text("SELECT pg_backend_pid()")) != old_pid
    finally:
        engine.dispose()
        control.dispose()
