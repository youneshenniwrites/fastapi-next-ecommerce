import os

# Set test-only configuration before importing the application. Never use a developer DB.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret-key-that-is-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture
def db():
    """Provide an isolated disposable database, with foreign keys enabled on SQLite."""
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    options = (
        {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        if url == "sqlite://"
        else {}
    )
    engine = create_engine(url, **options)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            """Enforce SQLite foreign keys so cascade tests cannot pass with orphaned rows."""
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db):
    """Route test requests to the disposable session and restore dependencies afterward."""

    def override_get_db():
        """Supply the test session instead of the application database."""
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def user(client, db):
    """Register a fictional active customer through the public endpoint."""
    from app.models.user import User

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    return db.get(User, response.json()["id"])


@pytest.fixture
def token(user):
    """Issue a test bearer token for the fixture customer."""
    from app.core.security import create_access_token

    return create_access_token(user.id)
