"""Fixed-window abuse throttling for the public demo (issue #109).

Abuse protection without paid services: fixed windows enforced as
FastAPI dependencies on auth and write routes. Exceeding a window returns 429
with a Retry-After delay plus X-RateLimit-Limit/X-RateLimit-Remaining headers
and the standard {"detail": ...} error body.

Defaults: registration 60/minute and login 60/minute per anonymous identity;
cart/order/admin writes 300/minute per verified active user. Validated environment
settings can override them; disposable browser fixtures set their own thresholds.

Signed storefront context preserves anonymous visitor buckets across shared
frontend egress. Unsigned/direct requests use trusted Vercel ingress IP, or peer
address locally. No raw forwarded header is trusted outside Vercel. Configuring
the paired dedicated signing key is required for storefront isolation.

Counters remain process-local, bounded and ephemeral: restarts, multiple
instances and eviction weaken protection. Shared NAT users still share anonymous
budgets. Keys are never logged, persisted or returned. This is not a distributed
WAF. Public reads remain unthrottled.
"""

import ipaddress
import math
import os
import threading
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException

from app.api.deps import get_current_user
from app.core.observability import count_rate_limit_rejection
from app.core.proxy_identity import verified_proxy_key
from app.core.settings import settings
from app.models.user import User

AUTH_REGISTER_LIMIT = settings.RATE_LIMIT_AUTH_REGISTER
AUTH_LOGIN_LIMIT = settings.RATE_LIMIT_AUTH_LOGIN
WRITE_LIMIT = settings.RATE_LIMIT_WRITE
WINDOW_SECONDS = 60
MAX_BUCKETS = 10_000
OVERFLOW_SWEEP_EVERY = 64


class RateLimiter:
    """Thread-safe fixed-window counter with a bounded bucket table."""

    def __init__(
        self,
        limit: int,
        window_seconds: int = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._buckets: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()
        self._overflow_count = 0

    def consume(self, key: str) -> tuple[bool, int]:
        """Record one request. Return (allowed, retry_after_seconds)."""
        now = self.clock()
        with self._lock:
            start, count = self._buckets.get(key, (now, 0))
            if now - start >= self.window_seconds:
                start, count = now, 0
            if count >= self.limit:
                retry_after = math.ceil(start + self.window_seconds - now)
                return False, max(retry_after, 1)
            self._buckets[key] = (start, count + 1)
            if len(self._buckets) > MAX_BUCKETS:
                self._overflow_count += 1
                # Amortized bound: evict oldest first (cheap, no scan), and run
                # the full expired sweep only periodically so a distinct-key
                # flood cannot keep the lock busy scanning.
                overflow = len(self._buckets) - MAX_BUCKETS
                for _ in range(overflow):
                    del self._buckets[next(iter(self._buckets))]
                if self._overflow_count % OVERFLOW_SWEEP_EVERY == 0:
                    self._purge_expired(now)
            return True, 0

    def reset(self) -> None:
        """Drop all counters. Test isolation seam; not part of any endpoint."""
        with self._lock:
            self._buckets.clear()

    def _purge_expired(self, now: float) -> None:
        """Evict closed windows. Called periodically, never on every overflow."""
        expired = [
            key
            for key, (start, _) in self._buckets.items()
            if now - start >= self.window_seconds
        ]
        for key in expired:
            del self._buckets[key]


auth_register_limiter = RateLimiter(AUTH_REGISTER_LIMIT)
auth_login_limiter = RateLimiter(AUTH_LOGIN_LIMIT)
write_limiter = RateLimiter(WRITE_LIMIT)


def client_key(request: Request) -> str:
    """Identify a throttling bucket without storing personal data elsewhere."""
    signed = verified_proxy_key(request)
    if signed is not None:
        return signed
    # Only trust platform-overwritten forwarding metadata inside Vercel runtime.
    # Local/direct clients cannot opt in by supplying a request header.
    if os.environ.get("VERCEL") == "1":
        try:
            address = ipaddress.ip_address(request.headers.get("x-forwarded-for", ""))
            return f"ip:{address.compressed}"
        except ValueError:
            pass
    return f"peer:{getattr(request.client, 'host', 'unknown')}"


def _enforce(request: Request, limiter: RateLimiter, key: str | None = None) -> None:
    """Reject over-limit requests with 429 and standard throttling headers."""
    allowed, retry_after = limiter.consume(client_key(request) if key is None else key)
    if not allowed:
        count_rate_limit_rejection(request.url.path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Wait briefly, then try again.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limiter.limit),
                "X-RateLimit-Remaining": "0",
            },
        )


def enforce_auth_register_limit(request: Request) -> None:
    """Throttle account creation per client (anti registration-spam)."""
    _enforce(request, auth_register_limiter)


def enforce_auth_login_limit(request: Request) -> None:
    """Throttle password login per client (anti credential-stuffing)."""
    _enforce(request, auth_login_limiter)


def enforce_write_limit(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> None:
    """Throttle writes per verified active customer, independent of network egress."""
    _enforce(request, write_limiter, key=f"user:{user.id}")


def reset_rate_limit_state() -> None:
    """Clear every limiter bucket. Test isolation only; never route through."""
    auth_register_limiter.reset()
    auth_login_limiter.reset()
    write_limiter.reset()
