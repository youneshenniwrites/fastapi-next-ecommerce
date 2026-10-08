import os

from sqlalchemy import create_engine, event, pool

from alembic import context
from app.core.settings import settings
from app.models import Product, User  # noqa: F401
from app.models.base import Base

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    def _sqlite_foreign_keys(dbapi_connection, _connection_record):
        if engine.dialect.name != "sqlite":
            return
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Off by default. Revision 0009 rebuilds products and does not preserve
    # carts, so a migration connection must not start enforcing foreign keys.
    # Tests opt in after 0009 to prove revision 0010 parks cart lines.
    if os.environ.get("ALEMBIC_SQLITE_FOREIGN_KEYS") == "on":
        event.listen(engine, "connect", _sqlite_foreign_keys)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
