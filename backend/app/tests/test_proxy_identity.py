"""Anonymous proxy identity trust and configuration, using fictional data only."""

import hashlib
import hmac

import pytest
from pydantic import SecretStr, ValidationError
from starlette.requests import Request

from app.core import proxy_identity, rate_limit
from app.core.settings import Settings, settings

KEY = "fictional-proxy-key-for-tests-123456789"


def signed(bucket="a" * 64, timestamp="1000", path="/api/v1/auth/login", key=KEY):
    """Build fictional signed context independently of the verifier."""
    signature = hmac.new(
        key.encode(), f"{timestamp}\n{bucket}\nPOST\n{path}".encode(), hashlib.sha256
    ).hexdigest()
    return f"{timestamp}.{bucket}.{signature}"


def request(context="", path="/api/v1/auth/login", method="POST", forwarded=""):
    """Create an ASGI request without a network or real customer data."""
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [
                (b"x-vindor-client-context", context.encode()),
                (b"x-forwarded-for", forwarded.encode()),
            ],
            "client": ("192.0.2.10", 1234),
        }
    )


@pytest.fixture
def configured(monkeypatch):
    """Supply a dedicated fictional key and deterministic server clock."""
    monkeypatch.setattr(settings, "RATE_LIMIT_PROXY_SECRET", SecretStr(KEY))
    monkeypatch.setattr(proxy_identity.time, "time", lambda: 1000)
    monkeypatch.delenv("VERCEL", raising=False)


def test_two_signed_visitors_are_isolated_behind_one_egress(configured):
    limiter = rate_limit.RateLimiter(1)
    first = request(signed())
    second = request(signed(bucket="b" * 64))
    assert limiter.consume(rate_limit.client_key(first))[0]
    assert not limiter.consume(rate_limit.client_key(first))[0]
    assert limiter.consume(rate_limit.client_key(second))[0]
    assert rate_limit.client_key(
        request(signed(timestamp="999"))
    ) == rate_limit.client_key(first)


@pytest.mark.parametrize(
    "context,path,method",
    [
        ("invalid", "/api/v1/auth/login", "POST"),
        (signed(key="wrong"), "/api/v1/auth/login", "POST"),
        (signed(timestamp="939"), "/api/v1/auth/login", "POST"),
        (signed(timestamp="1006"), "/api/v1/auth/login", "POST"),
        (signed(), "/api/v1/auth/register", "POST"),
        (signed(), "/api/v1/auth/login", "GET"),
        (signed(path="/api/v1/cart/"), "/api/v1/cart/", "POST"),
        (signed(bucket="A" * 64), "/api/v1/auth/login", "POST"),
    ],
)
def test_invalid_assertions_keep_fallback_limit(configured, context, path, method):
    req = request(context, path, method, forwarded="198.51.100.20")
    assert rate_limit.client_key(req) == "peer:192.0.2.10"
    limiter = rate_limit.RateLimiter(1)
    assert limiter.consume(rate_limit.client_key(req))[0]
    assert not limiter.consume(rate_limit.client_key(req))[0]


def test_missing_configuration_does_not_trust_signed_claim(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PROXY_SECRET", SecretStr(""))
    monkeypatch.delenv("VERCEL", raising=False)
    assert rate_limit.client_key(request(signed())) == "peer:192.0.2.10"


def test_vercel_uses_only_a_single_valid_platform_ip(configured, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert (
        rate_limit.client_key(request(forwarded="2001:db8:0:0::1")) == "ip:2001:db8::1"
    )
    assert (
        rate_limit.client_key(request(forwarded="203.0.113.1, 203.0.113.2"))
        == "peer:192.0.2.10"
    )
    assert rate_limit.client_key(request(forwarded="malformed")) == "peer:192.0.2.10"


def test_settings_validate_limits_and_secret():
    config = {
        "DATABASE_URL": "sqlite://",
        "SECRET_KEY": "fictional-setting-key-123456789012345",
    }
    assert Settings(_env_file=None, **config).RATE_LIMIT_AUTH_REGISTER == 60
    for name in (
        "RATE_LIMIT_AUTH_REGISTER",
        "RATE_LIMIT_AUTH_LOGIN",
        "RATE_LIMIT_WRITE",
    ):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **config, **{name: 0})
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None, **config, RATE_LIMIT_PROXY_SECRET="short-fictional-value"
        )
    assert "short-fictional-value" not in str(error.value)


def test_login_route_preserves_signed_visitor_isolation(
    client, user, configured, monkeypatch
):
    monkeypatch.setattr(rate_limit, "auth_login_limiter", rate_limit.RateLimiter(1))
    data = {"username": user.email, "password": "wrong-password"}
    first = {"x-vindor-client-context": signed()}
    second = {"x-vindor-client-context": signed(bucket="b" * 64)}
    assert (
        client.post("/api/v1/auth/login", data=data, headers=first).status_code == 401
    )
    assert (
        client.post("/api/v1/auth/login", data=data, headers=first).status_code == 429
    )
    assert (
        client.post("/api/v1/auth/login", data=data, headers=second).status_code == 401
    )


def test_proxy_key_cannot_reuse_authentication_key():
    key = "fictional-key-with-at-least-32-characters"
    with pytest.raises(ValidationError, match="separate from authentication"):
        Settings(
            _env_file=None,
            DATABASE_URL="sqlite://",
            SECRET_KEY=key,
            RATE_LIMIT_PROXY_SECRET=key,
        )


def test_frontend_literal_signature_fixture(monkeypatch):
    """Verify the same literal vector as the Node signing test."""
    monkeypatch.setattr(
        settings,
        "RATE_LIMIT_PROXY_SECRET",
        SecretStr("fictional-proxy-key-for-tests-only-123456"),
    )
    monkeypatch.setattr(proxy_identity.time, "time", lambda: 1800000000)
    context = "1800000000.55b19a7aed1fa105f88a285ebd06541f859396e72dd886ce556c7d8e75f426b8.e5c9832120ac751fd7ecd04563f9cba444539e8164840ec8180356b490c76dc0"
    assert (
        proxy_identity.verified_proxy_key(request(context))
        == "proxy:55b19a7aed1fa105f88a285ebd06541f859396e72dd886ce556c7d8e75f426b8"
    )


def test_assertion_is_redacted_from_error_request_headers():
    """The existing error scrubber must not export reusable signed context."""
    from app.core.observability import scrub_event

    event = {"request": {"headers": {"X-Vindor-Client-Context": signed()}}}
    assert (
        scrub_event(event, {})["request"]["headers"]["X-Vindor-Client-Context"]
        == "[Filtered]"
    )
