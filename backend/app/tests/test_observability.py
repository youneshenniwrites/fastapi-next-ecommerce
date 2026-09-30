"""Sentry observability init, scrubbing and metrics (issue #121)."""

import pytest
import sentry_sdk
from starlette.requests import Request

import app.core.rate_limit as rate_limit
from app.core.observability import (
    count_rate_limit_rejection,
    init_observability,
    scrub_event,
    scrub_log,
    scrub_metric,
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
    assert recorded["before_send_transaction"] is scrub_event
    assert recorded["before_send_log"] is scrub_log
    assert recorded["include_local_variables"] is False
    assert len(recorded["integrations"]) == 2


def test_settings_reject_out_of_range_sample_rate():
    """Sample rates stay within the free-tier guardrail bounds."""
    with pytest.raises(ValueError):
        _settings(SENTRY_TRACES_SAMPLE_RATE=1.5)


def test_scrub_event_keeps_only_diagnostic_structure():
    event = {
        "event_id": "a" * 32,
        "release": "demo@1",
        "environment": "test",
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "fictional-secret",
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "orders.py",
                                "function": "place_order",
                                "lineno": 42,
                                "vars": {"password": "fictional-secret"},
                            }
                        ]
                    },
                }
            ]
        },
        "request": {"data": {"username": "fictional-secret"}},
        "extra": {"nested": [[{"password": "fictional-secret"}]]},
        "breadcrumbs": {"values": [{"message": "fictional-secret"}]},
    }
    clean = scrub_event(event, {})
    assert "fictional-secret" not in str(clean)
    assert clean["release"] == "demo@1"
    frame = clean["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert frame == {"filename": "orders.py", "function": "place_order", "lineno": 42}
    assert event["exception"]["values"][0]["value"] == "fictional-secret"


def test_serialized_sdk_envelopes_are_private():
    """Exercise real SDK serialization, not just the callback or init options."""
    from sentry_sdk.transport import Transport

    from app.core.observability import scrub_log

    class MemoryTransport(Transport):
        def capture_envelope(self, envelope):
            envelopes.append(envelope)

    envelopes = []
    with sentry_sdk.init(
        dsn="https://key@o0.ingest.sentry.io/0",
        transport=MemoryTransport,
        default_integrations=False,
        traces_sample_rate=1,
        enable_logs=True,
        before_send=scrub_event,
        before_send_transaction=scrub_event,
        before_send_log=scrub_log,
        before_send_metric=scrub_metric,
        include_local_variables=False,
        release="demo@1",
        environment="privacy-test",
    ):
        try:
            raise ValueError("fictional-secret")
        except ValueError:
            sentry_sdk.capture_exception()
        sentry_sdk.capture_event(
            {
                "exception": {
                    "values": [{"type": "ValueError", "value": "fictional-secret"}]
                },
                "request": {
                    "url": "https://shop.invalid/?token=fictional-secret",
                    "data": "username=fictional-secret&password=fictional-secret",
                },
                "extra": {"nested": [[{"token": "fictional-secret"}]]},
            }
        )
        with sentry_sdk.start_transaction(
            name="/api/v1/orders/{order_id}/payment", op="http.server"
        ):
            pass
        with sentry_sdk.start_transaction(name="fictional-secret", op="test"):
            sentry_sdk.set_context("private", {"password": "fictional-secret"})
        sentry_sdk.logger.error(
            "fictional-secret", attributes={"password": "fictional-secret"}
        )
        from datetime import datetime, timezone

        from app.core.observability import record_confirmation, record_request

        record_request("cart_write", 200, 12)
        record_confirmation(
            1700000000, datetime.fromtimestamp(1700000001, timezone.utc)
        )
        sentry_sdk.logger.info(
            "fictional-secret",
            attributes={
                "operation": "fictional-secret",
                "outcome": "fictional-secret",
                "reason": "fictional-secret",
            },
        )
        count_rate_limit_rejection("/api/v1/orders/{order_id}/payment")
        sentry_sdk.flush()
    serialized = b"\n".join(envelope.serialize() for envelope in envelopes)
    assert b"fictional-secret" not in serialized
    kinds = {item.headers["type"] for envelope in envelopes for item in envelope.items}
    assert {"event", "transaction", "log", "trace_metric"} <= kinds
    assert b"test_observability.py" in serialized
    assert b"ValueError" in serialized
    assert b"privacy-test" in serialized
    assert b"demo@1" in serialized
    assert b"payment_session" in serialized
    assert b"commerce.requests" in serialized
    assert b"cart_write" in serialized
    assert b"completed" in serialized
    assert b"payment.confirmation_delay" in serialized
    assert b"trace_id" in serialized
    logs = [
        item.payload.json
        for envelope in envelopes
        for item in envelope.items
        if item.headers["type"] == "log"
    ]
    assert "privacy-test" in str(logs)
    assert "demo@1" in str(logs)


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
            "path": "/api/v1/orders/fictional-private@example.invalid/payment",
            "route": type("Route", (), {"path": "/api/v1/orders/{order_id}/payment"})(),
            "headers": [],
            "query_string": b"",
        }
    )
    limiter = RateLimiter(1)
    limiter.consume(client_key(request))
    with pytest.raises(Exception, match="Too many requests"):
        _enforce(request, limiter)
    assert recorded == ["/api/v1/orders/{order_id}/payment"]


@pytest.mark.parametrize(
    "filename",
    [None, "https://[invalid/path.py", "private@example.invalid", "secrets.txt"],
)
def test_untrusted_stack_locations_are_discarded(filename):
    """Malformed or non-code paths must not disclose request-derived values."""
    event = {
        "exception": {
            "values": [
                {
                    "type": "Error",
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": filename,
                                "function": "private@example.invalid",
                            },
                            None,
                        ]
                    },
                }
            ]
        },
        "contexts": {"trace": None},
    }
    clean = scrub_event(event, {})
    assert clean["exception"]["values"][0]["stacktrace"] == {"frames": [{}, {}]}
    assert clean["contexts"]["trace"] == {}


def test_code_artifact_location_keeps_only_source_map_path():
    event = {
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "https://shop.invalid/_next/static/chunks/app.js?token=private",
                                "function": "render_page",
                            }
                        ]
                    }
                }
            ]
        }
    }
    frame = scrub_event(event, {})["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert frame == {
        "filename": "/_next/static/chunks/app.js",
        "function": "render_page",
    }


def test_unknown_metric_is_dropped():
    assert scrub_metric({"name": "private@example.invalid", "value": 1}, {}) is None


def test_malformed_exception_and_span_context_do_not_escape_filter():
    clean = scrub_event({"exception": {"values": "private"}, "spans": [None]}, {})
    assert clean["exception"] == {"values": []}
    assert clean["spans"] == [{"description": "[Filtered]"}]


def test_request_outcomes_and_telemetry_failure_do_not_escape(monkeypatch):
    from app.core.observability import record_request

    calls = []
    monkeypatch.setattr(sentry_sdk.metrics, "count", lambda *a, **kw: calls.append(kw))
    for status in (200, 409, 422, 503):
        record_request("order_placement", status, 10)
    assert [c["attributes"]["outcome"] for c in calls] == [
        "success",
        "expected_error",
        "expected_error",
        "technical_error",
    ]
    monkeypatch.setattr(
        sentry_sdk.metrics,
        "count",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    record_request("order_placement", 200, 10)


def test_confirmation_invalid_and_skew_are_not_latency_samples(monkeypatch):
    from datetime import datetime, timezone

    from app.core.observability import record_confirmation

    counts, samples = [], []
    monkeypatch.setattr(
        sentry_sdk.metrics,
        "count",
        lambda *a, **kw: counts.append(kw["attributes"]["outcome"]),
    )
    monkeypatch.setattr(
        sentry_sdk.metrics, "distribution", lambda *a, **kw: samples.append(a[1])
    )
    for created in (None, True, -1, 10**1000, 1700000002, 1700000000):
        record_confirmation(created, datetime.fromtimestamp(1700000001, timezone.utc))
    assert counts == ["invalid", "invalid", "invalid", "invalid", "clock_skew", "valid"]
    assert samples == [1000]


def test_cart_denominator_includes_rejected_requests(client, monkeypatch):
    from app.core import observability

    observed = []
    monkeypatch.setattr(
        observability, "record_request", lambda *args: observed.append(args)
    )
    response = client.put("/api/v1/cart/items/1", json={"quantity": 1})
    assert response.status_code == 401
    assert len(observed) == 1
    assert observed[0][:2] == ("cart_write", 401)
    assert observed[0][2] >= 0


def test_diagnostic_default_off_and_admin_only(client, user, token, db, monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.settings import settings
    from app.main import app

    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/diagnostics/sentry", headers=headers).status_code == 404
    monkeypatch.setattr(settings, "SENTRY_DIAGNOSTICS_ENABLED", True)
    monkeypatch.setattr(settings, "SENTRY_ENVIRONMENT", "development")
    assert client.post("/api/v1/diagnostics/sentry", headers=headers).status_code == 403
    user.is_superuser = True
    db.commit()
    with TestClient(app, raise_server_exceptions=False) as diagnostic_client:
        assert (
            diagnostic_client.post(
                "/api/v1/diagnostics/sentry", headers=headers
            ).status_code
            == 500
        )
    monkeypatch.setattr(settings, "SENTRY_ENVIRONMENT", "production")
    assert client.post("/api/v1/diagnostics/sentry", headers=headers).status_code == 404


def test_transaction_names_are_bounded():
    assert (
        scrub_event({"transaction": "/api/v1/orders/{order_id}/payment"}, {})[
            "transaction"
        ]
        == "payment_session"
    )
    assert (
        scrub_event({"transaction": "/api/v1/orders/secret/payment?token=secret"}, {})[
            "transaction"
        ]
        == "[Filtered]"
    )


def test_webhook_reconciliation_is_technical_and_reasons_are_bounded(monkeypatch):
    from app.core.observability import record_request, scrub_log

    counts = []
    monkeypatch.setattr(
        sentry_sdk.metrics, "count", lambda *a, **kw: counts.append(kw["attributes"])
    )
    record_request("webhook", 409, 10)
    assert counts == [
        {
            "operation": "webhook",
            "outcome": "technical_error",
            "reason": "reconciliation_required",
        }
    ]
    assert (
        scrub_log({"attributes": {"reason": "fictional-secret"}}, {})["attributes"]
        == {}
    )
    assert scrub_log({"attributes": {"reason": "duplicate_event"}}, {})[
        "attributes"
    ] == {"reason": "duplicate_event"}


def test_real_fastapi_transaction_has_safe_operation(client):
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.transport import Transport

    envelopes = []

    class MemoryTransport(Transport):
        def capture_envelope(self, envelope):
            envelopes.append(envelope)

    with sentry_sdk.init(
        dsn="https://key@o0.ingest.sentry.io/0",
        transport=MemoryTransport,
        integrations=[FastApiIntegration(transaction_style="url")],
        traces_sample_rate=1,
        before_send_transaction=scrub_event,
    ):
        client.put("/api/v1/cart/items/1", json={"quantity": 1})
        sentry_sdk.flush()
    transactions = [
        item.payload.json
        for envelope in envelopes
        for item in envelope.items
        if item.headers["type"] == "transaction"
    ]
    assert any(item["transaction"] == "cart_write" for item in transactions), (
        transactions
    )
