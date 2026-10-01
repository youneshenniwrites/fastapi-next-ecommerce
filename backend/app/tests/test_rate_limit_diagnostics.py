"""Development-only, privacy-safe evidence of same-instance visitor isolation."""

import hashlib
import hmac
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import SecretStr

from app.core import proxy_identity, rate_limit
from app.core.rate_limit import RateLimiter, enforce_auth_login_limit
from app.core.settings import Settings, settings
from app.main import app

KEY = "fictional-diagnostic-signing-key-123456789"
RELEASE = "1a" * 20
PAYLOAD = {"username": "fictional@example.test", "password": "invalid-password"}
PREFIX = "x-vindor-limiter-"


def signed(bucket):
    signature = hmac.new(
        KEY.encode(),
        f"1000\n{bucket}\nPOST\n/api/v1/auth/login".encode(),
        hashlib.sha256,
    ).hexdigest()
    return {"x-vindor-client-context": f"1000.{bucket}.{signature}"}


def evidence(response):
    return {
        name: value
        for name, value in response.headers.items()
        if name.startswith(PREFIX)
    }


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_DIAGNOSTICS_ENABLED", True)
    monkeypatch.setattr(settings, "SENTRY_ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SENTRY_RELEASE", RELEASE)
    monkeypatch.setattr(settings, "RATE_LIMIT_PROXY_SECRET", SecretStr(KEY))
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(proxy_identity.time, "time", lambda: 1000)
    monkeypatch.setattr(rate_limit, "auth_login_limiter", RateLimiter(1))


def test_same_instance_orders_isolated_signed_decisions(client, enabled):
    first, second = signed("a" * 64), signed("b" * 64)
    initial = client.post("/api/v1/auth/login", data=PAYLOAD, headers=first)
    denied = client.post("/api/v1/auth/login", data=PAYLOAD, headers=first)
    other = client.post("/api/v1/auth/login", data=PAYLOAD, headers=second)
    still_denied = client.post("/api/v1/auth/login", data=PAYLOAD, headers=first)
    responses = (initial, denied, other, still_denied)
    assert [response.status_code for response in responses] == [401, 429, 401, 429]
    proofs = [evidence(response) for response in responses]
    assert len({proof[PREFIX + "instance"] for proof in proofs}) == 1
    assert re.fullmatch(r"[0-9a-f]{32}", proofs[0][PREFIX + "instance"])
    assert [int(proof[PREFIX + "sequence"]) for proof in proofs] == [1, 2, 3, 4]
    for response, proof in zip(responses, proofs, strict=True):
        assert set(proof) == {
            PREFIX + name
            for name in ("instance", "context", "release", "sequence", "limit")
        }
        assert proof[PREFIX + "context"] == "verified"
        assert proof[PREFIX + "release"] == RELEASE
        assert proof[PREFIX + "limit"] == "1"
        assert response.headers["cache-control"] == "no-store"
        for forbidden in (
            KEY,
            first["x-vindor-client-context"],
            "a" * 64,
            "b" * 64,
            "proxy:",
            "peer:",
        ):
            assert forbidden not in str(proof)


def test_invalid_signature_cannot_claim_verified_context(client, enabled):
    response = client.post(
        "/api/v1/auth/login",
        data=PAYLOAD,
        headers={"x-vindor-client-context": "invalid", "x-forwarded-for": "192.0.2.25"},
    )
    assert response.status_code == 401
    assert evidence(response)[PREFIX + "context"] == "fallback"
    assert "192.0.2.25" not in str(evidence(response))


def test_signature_provenance_is_not_recomputed_at_response(
    client, enabled, monkeypatch
):
    verifier = rate_limit.verified_proxy_key
    calls = []

    def expire_after_selection(request):
        calls.append(1)
        key = verifier(request)
        monkeypatch.setattr(proxy_identity.time, "time", lambda: 1061)
        return key

    monkeypatch.setattr(rate_limit, "verified_proxy_key", expire_after_selection)
    response = client.post("/api/v1/auth/login", data=PAYLOAD, headers=signed("a" * 64))
    assert response.status_code == 401
    assert evidence(response)[PREFIX + "context"] == "verified"
    assert len(calls) == 1


@pytest.mark.parametrize(
    "name,value",
    [
        ("RATE_LIMIT_DIAGNOSTICS_ENABLED", False),
        ("SENTRY_ENVIRONMENT", "production"),
        ("SENTRY_ENVIRONMENT", "local"),
        ("SENTRY_RELEASE", ""),
        ("SENTRY_RELEASE", "SECRET arbitrary release"),
        ("SENTRY_RELEASE", "A" * 40),
    ],
)
def test_suppresses_all_diagnostics_unless_explicit_development_release(
    client, enabled, monkeypatch, name, value
):
    monkeypatch.setattr(settings, name, value)
    response = client.post("/api/v1/auth/login", data=PAYLOAD)
    assert response.status_code == 401
    assert evidence(response) == {}


def test_local_runtime_suppresses_diagnostics(client, enabled, monkeypatch):
    monkeypatch.delenv("VERCEL")
    assert evidence(client.post("/api/v1/auth/login", data=PAYLOAD)) == {}


def test_only_enforced_login_errors_have_diagnostics(client, user, enabled):
    success = client.post(
        "/api/v1/auth/login", data={"username": user.email, "password": "password123"}
    )
    assert success.status_code == 200
    assert evidence(success) == {}
    assert evidence(client.get("/health")) == {}
    assert (
        evidence(
            client.post(
                "/api/v1/auth/register",
                json={"email": "another@example.test", "password": "password123"},
            )
        )
        == {}
    )
    app.dependency_overrides[enforce_auth_login_limit] = lambda: None
    try:
        response = client.post("/api/v1/auth/login", data=PAYLOAD)
        assert response.status_code == 401
        assert evidence(response) == {}
    finally:
        app.dependency_overrides.pop(enforce_auth_login_limit)


def test_witness_is_per_object_and_stable_across_counter_reset():
    first, second = RateLimiter(1), RateLimiter(1)
    witness = first.witness
    assert first.witness == witness != second.witness
    first.reset()
    assert first.witness == witness


def test_concurrent_decisions_capture_one_distinct_sequence_each():
    limiter = RateLimiter(1)

    def consume(_):
        proof = {}
        allowed, _ = limiter.consume("fictional", evidence=proof)
        return allowed, proof

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(consume, range(12)))
    assert sum(allowed for allowed, _ in results) == 1
    assert sorted(int(proof["sequence"]) for _, proof in results) == list(range(1, 13))
    assert {proof["instance"] for _, proof in results} == {limiter.witness}


def test_sequence_rollover_renews_witness_before_unsafe_integer():
    limiter = RateLimiter(1)
    witness = limiter.witness
    limiter._sequence = 2**53 - 1
    proof = {}
    limiter.consume("fictional", evidence=proof)
    assert proof["sequence"] == "1"
    assert proof["instance"] != witness


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork is unavailable")
def test_inherited_limiter_gets_distinct_process_witness():
    limiter = RateLimiter(1)
    parent = {}
    limiter.consume("fictional", evidence=parent)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        child = {}
        limiter.consume("fictional", evidence=child)
        os.write(write_fd, json.dumps(child).encode())
        os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    child = json.loads(os.read(read_fd, 1024))
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    assert status == 0
    assert child["instance"] != parent["instance"]
    assert child["sequence"] == "1"
    assert limiter.witness == parent["instance"]


def test_diagnostics_default_disabled():
    config = Settings(
        _env_file=None,
        DATABASE_URL="sqlite://",
        SECRET_KEY="fictional-key-that-is-at-least-32-characters",
    )
    assert config.RATE_LIMIT_DIAGNOSTICS_ENABLED is False
