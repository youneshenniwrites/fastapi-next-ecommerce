"""Sentry observability init, scrubbing and metrics (issue #121)."""

import pytest
import sentry_sdk
from starlette.requests import Request

import app.core.rate_limit as rate_limit
from app.core.observability import (
    FILTERED,
    count_rate_limit_rejection,
    init_observability,
    scrub_event,
)
from app.core.rate_limit import RateLimiter, _enforce, client_key
from app.core.settings import Settings


def _settings(**overrides):
    """Build settings with the required secrets for unit tests."""
    base = {
        "DATABASE_URL": "sqlite://",
        "SECRET_KEY": "test-only-secret-key-that-is-at-least-32-characters",
    }
    base.update(overrides)
    return Settings(**base)


def test_init_stays_silent_without_dsn(monkeypatch):
    """Missing DSN must never initialize the SDK or send data."""
    called = []
    monkeypatch.setattr(sentry_sdk, "init", lambda *a, **k: called.append(k))
    assert init_observability(_settings()) is False
    assert called == []


def test_init_configures_scrubbing_and_sampling(monkeypatch):
    """A configured DSN wires scrubbing, tracing and logs exactly once."""
    recorded = {}

    def fake_init(*args, **kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(sentry_sdk, "init", fake_init)
    settings = _settings(
        SENTRY_DSN="https://key@o0.ingest.sentry.io/0",
        SENTRY_ENVIRONMENT="test",
        SENTRY_TRACES_SAMPLE_RATE=0.25,
    )
    assert init_observability(settings) is True
    assert recorded["dsn"] == "https://key@o0.ingest.sentry.io/0"
    assert recorded["environment"] == "test"
    assert recorded["traces_sample_rate"] == 0.25
    assert recorded["send_default_pii"] is False
    assert recorded["enable_logs"] is True
    assert recorded["before_send"] is scrub_event
    assert len(recorded["integrations"]) == 2


def test_settings_reject_out_of_range_sample_rate():
    """Sample rates stay within the free-tier guardrail bounds."""
    with pytest.raises(ValueError):
        _settings(SENTRY_TRACES_SAMPLE_RATE=1.5)


def test_scrub_event_removes_credentials_and_pii():
    """Auth headers, secrets, query tokens and user PII never leave."""
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer abc",
                "Cookie": "session=xyz",
                "Content-Type": "application/json",
            },
            "data": {
                "email": "user@example.com",
                "password": "hunter2",
                "nested": {"token": "t", "items": [{"secret": "s"}, "keep"]},
            },
            "query_string": "next=%2F&token=abc&code=123",
        },
        "user": {"id": "42", "email": "user@example.com"},
    }
    original_headers = event["request"]["headers"]
    original_data = event["request"]["data"]
    scrubbed = scrub_event(event, {})
    headers = scrubbed["request"]["headers"]
    assert headers["Authorization"] == FILTERED
    assert headers["Cookie"] == FILTERED
    assert headers["Content-Type"] == "application/json"
    data = scrubbed["request"]["data"]
    assert data["email"] == FILTERED
    assert data["password"] == FILTERED
    assert data["nested"]["token"] == FILTERED
    assert data["nested"]["items"] == [{"secret": FILTERED}, "keep"]
    query = scrubbed["request"]["query_string"]
    assert "token=abc" not in query
    assert "code=123" in query
    assert scrubbed["user"] == {"id": "42"}
    assert original_headers["Authorization"] == "Bearer abc"
    assert original_data["password"] == "hunter2"


def test_scrub_event_tolerates_unexpected_shapes():
    """Missing or non-mapping payloads pass through unchanged."""
    assert scrub_event({}, {}) == {}
    event = {"request": "not-a-mapping", "user": "not-a-mapping"}
    assert scrub_event(event, {}) == event
    assert scrub_event({"request": {"headers": {"X": 1}}}, {})["request"] == {
        "headers": {"X": 1}
    }


def test_scrub_event_keeps_benign_scalars_and_shapes():
    """Harmless values and odd shapes survive scrubbing intact."""
    event = {"request": {"data": {"route": "/x", "count": 3}}}
    scrubbed = scrub_event(event, {})
    assert scrubbed["request"]["data"] == {"route": "/x", "count": 3}
    assert "query_string" not in scrubbed["request"]
    event = {"request": {"query_string": None}}
    assert scrub_event(event, {})["request"]["query_string"] is None
    event = {"request": {"headers": [("Authorization", "Bearer x")]}}
    scrubbed = scrub_event(event, {})
    assert scrubbed["request"]["headers"] == [("Authorization", "Bearer x")]


def test_metrics_are_safe_without_sdk_init():
    """Metric helpers must never raise when Sentry is unconfigured."""
    count_rate_limit_rejection("/api/v1/auth/login")


def test_rejection_records_route_metric(monkeypatch):
    """429 responses count per-route rejections for abuse dashboards."""
    recorded = []
    monkeypatch.setattr(rate_limit, "count_rate_limit_rejection", recorded.append)
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": [],
            "query_string": b"",
        }
    )
    limiter = RateLimiter(1)
    limiter.consume(client_key(request))
    with pytest.raises(Exception, match="Too many requests"):
        _enforce(request, limiter)
    assert recorded == ["/api/v1/auth/login"]
