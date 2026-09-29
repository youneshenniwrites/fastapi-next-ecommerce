"""Sentry observability: errors, traces, logs and metrics (issue #121)."""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

FILTERED = "[Filtered]"


SAFE_TRANSACTIONS = {
    "/api/v1/cart/items/{product_id}": "cart_write",
    "/api/v1/orders/{order_id}/place": "order_placement",
    "/api/v1/orders/{order_id}/payment": "payment_session",
    "/api/v1/payments/webhook": "webhook",
}


def _pick(value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: item
        for key, item in value.items()
        if key in fields and isinstance(item, (str, int, float, bool))
    }


def _filename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    # Preserve Next artifact paths for source-map matching; discard local roots.
    try:
        path = urlsplit(value).path.replace("\\", "/")
    except ValueError:
        return None
    path = (
        path[path.index("/_next/static/") :]
        if "/_next/static/" in path
        else path.rsplit("/", 1)[-1]
    )
    return (
        path
        if re.fullmatch(r"[A-Za-z0-9_./-]+\.(?:py|js|mjs|cjs|ts|tsx|jsx)", path)
        else None
    )


def _frames(stack: Any) -> dict[str, Any]:
    frames = stack.get("frames", []) if isinstance(stack, dict) else []
    cleaned = []
    for frame in frames if isinstance(frames, list) else []:
        item = _pick(frame, {"lineno", "colno", "in_app"})
        if isinstance(frame, dict):
            filename = _filename(frame.get("filename"))
            if filename:
                item["filename"] = filename
            for key in ("function", "module"):
                identifier = frame.get(key)
                if isinstance(identifier, str) and re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_.<>-]{0,120}", identifier
                ):
                    item[key] = identifier
        cleaned.append(item)
    return {"frames": cleaned}


def scrub_event(event: dict[str, Any], hint: Any) -> dict[str, Any]:
    """Allowlist SDK structure by context; discard all application payloads."""
    result = _pick(
        event,
        {
            "event_id",
            "type",
            "level",
            "platform",
            "timestamp",
            "start_timestamp",
            "release",
            "environment",
        },
    )
    for key in ("message", "transaction"):
        if key in event:
            result[key] = (
                SAFE_TRANSACTIONS.get(event[key], FILTERED)
                if key == "transaction" and isinstance(event[key], str)
                else FILTERED
            )
    exception = event.get("exception")
    if isinstance(exception, dict):
        values = exception.get("values", [])
        result["exception"] = (
            {
                "values": [
                    {
                        **_pick(value, {"type", "module"}),
                        "value": FILTERED,
                        "stacktrace": _frames(value.get("stacktrace")),
                    }
                    for value in values
                    if isinstance(value, dict)
                ]
            }
            if isinstance(values, list)
            else {"values": []}
        )
    contexts = event.get("contexts")
    trace_fields = {"trace_id", "span_id", "parent_span_id", "op", "status", "origin"}
    if isinstance(contexts, dict):
        result["contexts"] = {"trace": _pick(contexts.get("trace"), trace_fields)}
    if isinstance(event.get("spans"), list):
        result["spans"] = [
            {
                **_pick(span, trace_fields | {"start_timestamp", "timestamp"}),
                "description": FILTERED,
            }
            for span in event["spans"]
        ]
    return result


def scrub_log(log: dict[str, Any], hint: Any) -> dict[str, Any]:
    """Preserve log severity and correlation, never interpolated text/attributes."""
    result = {
        key: value
        for key, value in log.items()
        if key
        in {
            "time_unix_nano",
            "timestamp",
            "trace_id",
            "span_id",
            "severity_text",
            "severity_number",
        }
    }
    result["body"] = FILTERED
    result["attributes"] = _pick(
        log.get("attributes"), {"sentry.release", "sentry.environment"}
    )
    result["attributes"].update(_signal_attributes(log.get("attributes")))
    return result


def scrub_metric(metric: dict[str, Any], hint: Any) -> dict[str, Any] | None:
    """Only the application's fixed counter is enabled; routes are server templates."""
    if metric.get("name") not in {
        "rate_limit.rejected",
        "commerce.requests",
        "commerce.duration",
        "payment.confirmation_delay",
        "payment.confirmation_timing",
    }:
        return None
    result = _pick(
        metric, {"timestamp", "trace_id", "span_id", "name", "type", "value", "unit"}
    )
    result["attributes"] = _pick(
        metric.get("attributes"), {"sentry.release", "sentry.environment", "route"}
    )
    result["attributes"].update(_signal_attributes(metric.get("attributes")))
    return result


def count_rate_limit_rejection(route: str) -> None:
    """Record a throttled request for abuse dashboards. Safe without init."""
    sentry_sdk.metrics.count("rate_limit.rejected", 1, attributes={"route": route})


def init_observability(settings: Any) -> bool:
    """Initialize Sentry when a DSN is configured; otherwise stay silent."""
    if not settings.SENTRY_DSN:
        return False
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=settings.SENTRY_RELEASE or None,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        before_send=scrub_event,
        before_send_transaction=scrub_event,
        before_send_log=scrub_log,
        before_send_metric=scrub_metric,
        include_local_variables=False,
        enable_logs=True,
    )
    return True


OPERATIONS = {
    "cart_write",
    "order_placement",
    "payment_session",
    "webhook",
    "payment_confirmation",
    "inventory_release",
}
OUTCOMES = {
    "success",
    "expected_error",
    "technical_error",
    "valid",
    "invalid",
    "clock_skew",
    "released",
    "duplicate",
}


REASONS = {
    "completed",
    "rejected",
    "server_failure",
    "reconciliation_required",
    "duplicate_event",
    "processed_event",
}


def _signal_attributes(attributes: Any) -> dict[str, str]:
    if not isinstance(attributes, dict):
        return {}
    return {
        key: value
        for key, allowed in (
            ("operation", OPERATIONS),
            ("outcome", OUTCOMES),
            ("reason", REASONS),
        )
        if isinstance(value := attributes.get(key), str) and value in allowed
    }


def record_request(operation: str, status: int, duration_ms: float) -> None:
    """Unsampled completed attempts; expected 4xx are not technical failures."""
    outcome = (
        "technical_error"
        if status >= 500 or (operation == "webhook" and status == 409)
        else "expected_error"
        if status >= 400
        else "success"
    )
    attributes = {
        "operation": operation,
        "outcome": outcome,
        "reason": "reconciliation_required"
        if operation == "webhook" and status == 409
        else "server_failure"
        if status >= 500
        else "rejected"
        if status >= 400
        else "completed",
    }
    try:
        sentry_sdk.metrics.count("commerce.requests", 1, attributes=attributes)
        sentry_sdk.metrics.distribution(
            "commerce.duration", duration_ms, unit="millisecond", attributes=attributes
        )
        sentry_sdk.logger.info("Commerce request completed", attributes=attributes)
    except Exception:
        # Instrumentation must never change a commerce response or transaction.
        pass


class CommerceMetricsMiddleware:
    """Measure full HTTP attempts, including dependency/validation failures."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = time.perf_counter()
        status = 500
        try:

            async def capture(message):
                nonlocal status
                if message["type"] == "http.response.start":
                    status = message["status"]
                await send(message)

            await self.app(scope, receive, capture)
        finally:
            route = scope.get("path", "")
            route = re.sub(r"/items/[^/]+$", "/items/{product_id}", route)
            route = re.sub(
                r"/orders/[^/]+/(place|payment)$", r"/orders/{order_id}/\1", route
            )
            method = scope.get("method")
            operation = None
            if route == "/api/v1/cart/items/{product_id}" and method in {
                "PUT",
                "DELETE",
            }:
                operation = "cart_write"
            elif method == "POST":
                operation = {
                    "/api/v1/orders/{order_id}/place": "order_placement",
                    "/api/v1/orders/{order_id}/payment": "payment_session",
                    "/api/v1/payments/webhook": "webhook",
                }.get(route)
            if operation:
                record_request(
                    operation, status, (time.perf_counter() - started) * 1000
                )


def record_confirmation(provider_created: Any, persisted_at: datetime) -> None:
    """Signed event creation to committed local event time, once per paid transition."""
    attributes = {"operation": "payment_confirmation", "outcome": "invalid"}
    delay = None
    if (
        isinstance(provider_created, int)
        and not isinstance(provider_created, bool)
        and 0 < provider_created < 253402300800
    ):
        local = (
            persisted_at.replace(tzinfo=timezone.utc)
            if persisted_at.tzinfo is None
            else persisted_at
        )
        delay = (local.timestamp() - provider_created) * 1000
        attributes["outcome"] = "clock_skew" if delay < 0 else "valid"
    try:
        sentry_sdk.metrics.count(
            "payment.confirmation_timing", 1, attributes=attributes
        )
        if attributes["outcome"] == "valid":
            sentry_sdk.metrics.distribution(
                "payment.confirmation_delay",
                delay,
                unit="millisecond",
                attributes=attributes,
            )
        sentry_sdk.logger.info("Payment confirmation timing", attributes=attributes)
    except Exception:
        pass


def record_inventory_release(outcome: str) -> None:
    try:
        sentry_sdk.logger.info(
            "Inventory release completed",
            attributes={"operation": "inventory_release", "outcome": outcome},
        )
    except Exception:
        pass


def record_webhook_processed(duplicate: bool) -> None:
    try:
        sentry_sdk.logger.info(
            "Webhook delivery processed",
            attributes={
                "operation": "webhook",
                "outcome": "duplicate" if duplicate else "success",
                "reason": "duplicate_event" if duplicate else "processed_event",
            },
        )
    except Exception:
        pass
