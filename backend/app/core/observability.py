"""Sentry observability: errors, traces, logs and metrics (issue #121)."""

import logging
from typing import Any
from urllib.parse import parse_qsl, urlencode

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "current_password",
        "new_password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "email",
    }
)
SCRUBBED_HEADERS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-vercel-protection-bypass",
        "x-vindor-client-context",
    }
)
FILTERED = "[Filtered]"


def _scrub_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Filter sensitive keys from nested mappings without mutating the input."""
    scrubbed: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(key, str) and key.lower() in SENSITIVE_KEYS:
            scrubbed[key] = FILTERED
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_mapping(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                _scrub_mapping(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            scrubbed[key] = value
    return scrubbed


def _scrub_query_string(raw: Any) -> Any:
    """Filter sensitive parameters while preserving the query shape."""
    if not isinstance(raw, str) or not raw:
        return raw
    pairs = [
        (key, FILTERED if key.lower() in SENSITIVE_KEYS else value)
        for key, value in parse_qsl(raw, keep_blank_values=True)
    ]
    return urlencode(pairs)


def scrub_event(event: dict[str, Any], hint: Any) -> dict[str, Any]:
    """Remove credentials and PII before any payload leaves the process."""
    event = dict(event)
    request = event.get("request")
    if isinstance(request, dict):
        request = dict(request)
        event["request"] = request
        headers = request.get("headers")
        if isinstance(headers, dict):
            request["headers"] = {
                name: (
                    FILTERED
                    if isinstance(name, str) and name.lower() in SCRUBBED_HEADERS
                    else value
                )
                for name, value in headers.items()
            }
        data = request.get("data")
        if isinstance(data, dict):
            request["data"] = _scrub_mapping(data)
        if "query_string" in request:
            request["query_string"] = _scrub_query_string(request["query_string"])
    user = event.get("user")
    if isinstance(user, dict):
        event["user"] = {"id": user["id"]} if "id" in user else {}
    return event


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
        enable_logs=True,
    )
    return True
