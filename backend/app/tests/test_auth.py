from datetime import timedelta

import jwt
import pytest
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.security import create_access_token, decode_access_token
from app.core.settings import settings


def test_register_login_and_me(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "is_superuser": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["is_superuser"] is False
    assert "hashed_password" not in response.json()
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "new@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert login.json()["expires_in"] > 0
    token = login.json()["access_token"]
    claims = decode_access_token(token)
    assert claims["sub"] == str(response.json()["id"])
    assert claims["exp"] - claims["iat"] == login.json()["expires_in"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"


@pytest.mark.parametrize(
    "email,password",
    [("test@example.com", "wrongpassword"), ("absent@example.com", "password123")],
)
def test_invalid_login(client, user, email, password):
    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_duplicate_registration(client, user):
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": user.email, "password": "password123"},
        ).status_code
        == 400
    )


@pytest.mark.parametrize("password", ["short", "a" * 129])
def test_password_length(client, password):
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": password},
        ).status_code
        == 422
    )


def test_disabled_user_cannot_login_or_use_token(client, user, token, db):
    user.is_active = False
    db.commit()
    assert (
        client.post(
            "/api/v1/auth/login",
            data={"username": user.email, "password": "password123"},
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_legacy_bcrypt_password_upgrades(client, user, db):
    user.hashed_password = BcryptHasher().hash("password123")
    db.commit()
    response = client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "password123"}
    )
    assert response.status_code == 200
    db.refresh(user)
    assert user.hashed_password.startswith("$argon2id$")


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "garbage",
        "expired",
        "wrong-signature",
        "missing-exp",
        "bad-sub",
        "unknown-user",
    ],
)
def test_invalid_bearer_tokens(client, user, kind):
    token = {
        "missing": "",
        "garbage": "not-a-token",
        "expired": create_access_token(user.id, timedelta(seconds=-1)),
        "wrong-signature": jwt.encode(
            {"sub": str(user.id), "iat": 1, "exp": 9999999999},
            "a-different-secret-with-at-least-32-characters",
            algorithm="HS256",
        ),
        "missing-exp": jwt.encode(
            {"sub": str(user.id), "iat": 1}, settings.SECRET_KEY, algorithm="HS256"
        ),
        "bad-sub": jwt.encode(
            {"sub": "abc", "iat": 1, "exp": 9999999999},
            settings.SECRET_KEY,
            algorithm="HS256",
        ),
        "unknown-user": create_access_token(99999),
    }[kind]
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"} if token else {}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("password", ["a" * 90, "é" * 50])
def test_long_legacy_bcrypt_password_upgrades(client, user, db, password):
    user.hashed_password = BcryptHasher().hash(password.encode("utf-8")[:72])
    db.commit()
    response = client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": password}
    )
    assert response.status_code == 200
    db.refresh(user)
    assert user.hashed_password.startswith("$argon2id$")
    assert (
        client.post(
            "/api/v1/auth/login", data={"username": user.email, "password": password}
        ).status_code
        == 200
    )
