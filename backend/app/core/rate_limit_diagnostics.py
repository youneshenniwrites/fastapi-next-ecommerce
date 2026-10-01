"""Opt-in development evidence for process-local login throttling, not telemetry."""

import os
import re

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.settings import settings


def diagnostics_enabled() -> bool:
    """Never expose witnesses locally, in production, or without a valid release."""
    return (
        settings.RATE_LIMIT_DIAGNOSTICS_ENABLED
        and settings.SENTRY_ENVIRONMENT == "development"
        and os.environ.get("VERCEL") == "1"
        and re.fullmatch(r"[0-9a-f]{40}", settings.SENTRY_RELEASE) is not None
    )


class RateLimitDiagnosticsMiddleware:
    """Preserve dependency-produced evidence through handled 401/429 errors."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_response(message: Message) -> None:
            diagnostic = scope.get("state", {}).get("rate_limit_diagnostic")
            if (
                scope["type"] == "http"
                and scope.get("method") == "POST"
                and scope.get("path") == "/api/v1/auth/login"
                and message["type"] == "http.response.start"
                and message["status"] in (401, 429)
                and diagnostic is not None
                and diagnostics_enabled()
            ):
                headers = MutableHeaders(scope=message)
                for name, value in diagnostic.items():
                    headers[f"X-Vindor-Limiter-{name}"] = value
                headers["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, send_response)
