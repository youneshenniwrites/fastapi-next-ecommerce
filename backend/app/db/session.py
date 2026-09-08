# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

# Example connection string for local Postgres
# postgres://username:password@localhost:5432/dbname
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


def create_db_engine(database_url: str):
    # Hosted PostgreSQL may close idle connections when compute suspends.
    # Validate at checkout; do not replay transactions or mutations on failure.
    return create_engine(database_url, echo=False, future=True, pool_pre_ping=True)


engine = create_db_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
