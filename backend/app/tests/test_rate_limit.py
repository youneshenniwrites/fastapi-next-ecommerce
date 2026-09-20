"""Abuse-throttling behavior for auth and write endpoints (issue #109)."""

import pytest
from starlette.requests import Request

import app.core.rate_limit as rate_limit
from app.core.rate_limit import (
    AUTH_LOGIN_LIMIT,
    AUTH_REGISTER_LIMIT,
    RateLimiter,
    client_key,
    reset_rate_limit_state,
)


def test_rejects_non_positive_configuration():
    with pytest.raises(ValueError, match="limit must be positive"):
        RateLimiter(0)
    with pytest.raises(ValueError, match="window_seconds must be positive"):
        RateLimiter(1, window_seconds=0)


def test_allows_burst_then_rejects_with_retry_after():
    now = [1000.0]
    limiter = RateLimiter(2, window_seconds=60, clock=lambda: now[0])
    assert limiter.consume("client") == (True, 0)
    assert limiter.consume("client") == (True, 0)
    assert limiter.consume("client") == (False, 60)


def test_retry_after_counts_down_within_window():
    now = [1000.0]
    limiter = RateLimiter(1, window_seconds=60, clock=lambda: now[0])
    assert limiter.consume("client") == (True, 0)
    now[0] += 45
    assert limiter.consume("client") == (False, 15)


def test_window_reset_restores_allowance():
    now = [1000.0]
    limiter = RateLimiter(1, window_seconds=60, clock=lambda: now[0])
    assert limiter.consume("client") == (True, 0)
    assert limiter.consume("client") == (False, 60)
    now[0] += 60
    assert limiter.consume("client") == (True, 0)


def test_buckets_are_per_key():
    limiter = RateLimiter(1)
    assert limiter.consume("first") == (True, 0)
    assert limiter.consume("second") == (True, 0)
    assert limiter.consume("first")[0] is False


def test_expired_buckets_are_purged_to_bound_memory(monkeypatch):
    monkeypatch.setattr(rate_limit, "MAX_BUCKETS", 2)
    now = [1000.0]
    limiter = RateLimiter(100, window_seconds=60, clock=lambda: now[0])
    limiter.consume("stale")
    now[0] += 61
    limiter.consume("fresh-a")
    limiter.consume("fresh-b")
    assert len(limiter._buckets) == 2
    assert "stale" not in limiter._buckets


def test_active_flood_cannot_grow_memory_without_bound(monkeypatch):
    monkeypatch.setattr(rate_limit, "MAX_BUCKETS", 2)
    limiter = RateLimiter(100, window_seconds=3600)
    for index in range(10):
        assert limiter.consume(f"spoofed-{index}") == (True, 0)
    assert len(limiter._buckets) == 2


def test_periodic_sweep_clears_expired_keys_but_keeps_active_ones(monkeypatch):
    monkeypatch.setattr(rate_limit, "MAX_BUCKETS", 3)
    now = [1000.0]
    limiter = RateLimiter(100, window_seconds=60, clock=lambda: now[0])
    limiter.consume("expired-a")
    limiter.consume("expired-b")
    now[0] += 61
    limiter.consume("active")
    limiter._overflow_count = 63
    limiter.consume("fresh")
    assert "expired-a" not in limiter._buckets
    assert "expired-b" not in limiter._buckets
    assert "active" in limiter._buckets
    assert "fresh" in limiter._buckets


def test_client_key_prefers_first_forwarded_address():
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.7, 70.41.3.18")],
        }
    )
    assert client_key(request) == "203.0.113.7"


def test_client_key_falls_back_to_unknown_without_source():
    request = Request({"type": "http", "headers": []})
    assert client_key(request) == "unknown"


def test_register_returns_429_after_limit(client):
    for index in range(AUTH_REGISTER_LIMIT):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": f"bulk{index}@example.com", "password": "password123"},
        )
        assert response.status_code == 201
    throttled = client.post(
        "/api/v1/auth/register",
        json={"email": "bulk-overflow@example.com", "password": "password123"},
    )
    assert throttled.status_code == 429
    assert throttled.json() == {
        "detail": "Too many requests. Wait briefly, then try again."
    }
    assert int(throttled.headers["Retry-After"]) >= 1
    assert throttled.headers["X-RateLimit-Limit"] == str(AUTH_REGISTER_LIMIT)
    assert throttled.headers["X-RateLimit-Remaining"] == "0"


def test_login_returns_429_and_recovers_after_window(client, user, monkeypatch):
    now = [2000.0]
    monkeypatch.setattr(
        rate_limit,
        "auth_login_limiter",
        RateLimiter(2, window_seconds=60, clock=lambda: now[0]),
    )
    payload = {"username": user.email, "password": "password123"}
    assert client.post("/api/v1/auth/login", data=payload).status_code == 200
    assert client.post("/api/v1/auth/login", data=payload).status_code == 200
    throttled = client.post("/api/v1/auth/login", data=payload)
    assert throttled.status_code == 429
    assert int(throttled.headers["Retry-After"]) == 60
    now[0] += 60
    assert client.post("/api/v1/auth/login", data=payload).status_code == 200


def test_login_buckets_are_per_client_ip(client, user, monkeypatch):
    monkeypatch.setattr(rate_limit, "auth_login_limiter", RateLimiter(1))
    wrong = {"username": user.email, "password": "wrongpassword"}
    assert client.post("/api/v1/auth/login", data=wrong).status_code == 401
    assert client.post("/api/v1/auth/login", data=wrong).status_code == 429
    other_origin = {"X-Forwarded-For": "203.0.113.9"}
    assert (
        client.post("/api/v1/auth/login", data=wrong, headers=other_origin).status_code
        == 401
    )


def test_write_endpoints_share_one_bucket(client, user, token, db, monkeypatch):
    monkeypatch.setattr(rate_limit, "write_limiter", RateLimiter(2))
    user.is_superuser = True
    db.commit()
    headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.put(
            "/api/v1/cart/items/1", json={"quantity": 1}, headers=headers
        ).status_code
        != 429
    )
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code != 429
    assert (
        client.put(
            "/api/v1/cart/items/1", json={"quantity": 1}, headers=headers
        ).status_code
        == 429
    )
    throttled = client.post(
        "/api/v1/products/",
        json={"name": "Throttled", "price": 5, "stock": 1},
        headers=headers,
    )
    assert throttled.status_code == 429
    assert throttled.headers["X-RateLimit-Limit"] == "2"


def test_normal_use_below_limits_is_unaffected(client, user, token):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "password123"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/products/").status_code == 200
    assert (
        client.put(
            "/api/v1/cart/items/1", json={"quantity": 1}, headers=headers
        ).status_code
        != 429
    )
    assert login.headers.get("X-RateLimit-Limit") is None


def test_reset_rate_limit_state_clears_all_buckets():
    for _ in range(AUTH_REGISTER_LIMIT):
        assert rate_limit.auth_register_limiter.consume("reset-probe") == (True, 0)
    assert rate_limit.auth_register_limiter.consume("reset-probe")[0] is False
    for _ in range(AUTH_LOGIN_LIMIT):
        rate_limit.auth_login_limiter.consume("reset-probe")
    reset_rate_limit_state()
    assert rate_limit.auth_register_limiter.consume("reset-probe") == (True, 0)
    assert rate_limit.auth_login_limiter.consume("reset-probe") == (True, 0)


def test_authenticated_write_budgets_isolate_customers(
    client, user, token, db, monkeypatch
):
    """Customers sharing egress cannot consume one another's write allowance."""
    from app.core.security import create_access_token
    from app.models.user import User

    other = User(email="second@example.com", hashed_password="unused", is_active=True)
    db.add(other)
    db.commit()
    monkeypatch.setattr(rate_limit, "write_limiter", RateLimiter(1))
    first_headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.delete("/api/v1/cart/items/1", headers=first_headers).status_code == 204
    )
    assert (
        client.delete("/api/v1/cart/items/1", headers=first_headers).status_code == 429
    )
    second_headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
    assert (
        client.delete("/api/v1/cart/items/1", headers=second_headers).status_code == 204
    )
    forged = {
        **first_headers,
        "X-Forwarded-For": "203.0.113.99",
        "X-User-ID": str(other.id),
    }
    assert client.delete("/api/v1/cart/items/1", headers=forged).status_code == 429
    renewed = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    assert client.delete("/api/v1/cart/items/1", headers=renewed).status_code == 429


def test_invalid_identity_cannot_consume_customer_write_budget(
    client, user, token, db, monkeypatch
):
    """Authentication and admin authorization remain distinct from throttling."""
    limiter = RateLimiter(1)
    monkeypatch.setattr(rate_limit, "write_limiter", limiter)
    assert client.delete("/api/v1/cart/items/1").status_code == 401
    assert (
        client.delete(
            "/api/v1/cart/items/1", headers={"Authorization": "Bearer invalid"}
        ).status_code
        == 401
    )
    headers = {"Authorization": f"Bearer {token}"}
    assert client.delete("/api/v1/products/1", headers=headers).status_code == 403
    assert limiter._buckets == {}
    user.is_active = False
    db.commit()
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code == 401
    assert limiter._buckets == {}
    user.is_active = True
    db.commit()
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code == 204


def test_authenticated_write_retry_and_process_reset(client, token, monkeypatch):
    """A legitimate retry recovers, while a new process loses its local counters."""
    now = [1000.0]
    monkeypatch.setattr(
        rate_limit, "write_limiter", RateLimiter(1, clock=lambda: now[0])
    )
    headers = {"Authorization": f"Bearer {token}"}
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code == 204
    denied = client.delete("/api/v1/cart/items/1", headers=headers)
    assert denied.status_code == 429
    assert denied.headers["Retry-After"] == "60"
    now[0] += 60
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code == 204
    monkeypatch.setattr(rate_limit, "write_limiter", RateLimiter(1))
    assert client.delete("/api/v1/cart/items/1", headers=headers).status_code == 204
