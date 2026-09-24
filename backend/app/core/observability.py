"""Sentry observability: errors, traces, logs and metrics (issue #121)."""

import logging
import re
from typing import Any
from urllib.parse import urlsplit

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

FILTERED = "[Filtered]"


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
            result[key] = FILTERED
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
    return result


def scrub_metric(metric: dict[str, Any], hint: Any) -> dict[str, Any] | None:
    """Only the application's fixed counter is enabled; routes are server templates."""
    if metric.get("name") != "rate_limit.rejected":
        return None
    result = _pick(
        metric, {"timestamp", "trace_id", "span_id", "name", "type", "value", "unit"}
    )
    result["attributes"] = _pick(
        metric.get("attributes"), {"sentry.release", "sentry.environment", "route"}
    )
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
