"""Verify short-lived, route-bound anonymous identity from the storefront."""

import hashlib
import hmac
import re
import time

from fastapi import Request

from app.core.settings import settings

CONTEXT_HEADER = "x-vindor-client-context"
AUTH_PATHS = frozenset({"/api/v1/auth/login", "/api/v1/auth/register"})
CONTEXT_PATTERN = re.compile(r"([0-9]{1,12})\.([0-9a-f]{64})\.([0-9a-f]{64})")


def verified_proxy_key(request: Request) -> str | None:
    """Return only a signed bucket; invalid assertions never bypass fallback limits."""
    secret = settings.RATE_LIMIT_PROXY_SECRET.get_secret_value()
    if not secret or request.method != "POST" or request.url.path not in AUTH_PATHS:
        return None
    match = CONTEXT_PATTERN.fullmatch(request.headers.get(CONTEXT_HEADER, ""))
    if match is None:
        return None
    timestamp, bucket, signature = match.groups()
    age = time.time() - int(timestamp)
    if age < -5 or age > 60:
        return None
    message = f"{timestamp}\n{bucket}\nPOST\n{request.url.path}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    return f"proxy:{bucket}"
