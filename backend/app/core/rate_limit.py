"""Fixed-window abuse throttling for the public demo (issue #109).

Abuse protection without paid services: per-client fixed windows enforced as
FastAPI dependencies on auth and write routes. Exceeding a window returns 429
with a Retry-After delay plus X-RateLimit-Limit/X-RateLimit-Remaining headers
and the standard {"detail": ...} error body.

Enforced limits (per client, 60-second fixed windows):

- POST /api/v1/auth/register: 60 requests. Registration is single-shot for
  legitimate visitors; this blunts registration spam while leaving headroom
  for suites that register many accounts from one shared origin. Do not
  tighten below proven suite volume: CI failed at 20/min (PR #110).
- POST /api/v1/auth/login: 60 requests. Normal sign-in is single-shot and the
  headroom covers test and browser suites sharing one origin.
- Cart and product writes: 300 requests. Flood protection; genuine customer
  bursts and retry scenarios stay far below it.

Deliberate limitations, recorded so they are not mistaken for guarantees:

- Counters live in process memory, so they are per-instance and ephemeral on
  serverless hosts. This resists casual abuse on the Hobby demo; it is not a
  distributed WAF.
- Client identity is the first X-Forwarded-For entry (the platform terminates
  TLS upstream) falling back to the peer address. That header is spoofable, so
  buckets are best-effort fairness, not a security boundary.
- Public catalog reads are intentionally unthrottled in this increment:
  throttling reads risked harming legitimate visitors, which #109 forbids.
- Bucket keys hold IP strings in memory only. They are never logged,
  persisted, or returned, and 429 bodies carry no client data.
"""

import math
import threading
import time
from collections.abc import Callable

from fastapi import Request, status
from fastapi.exceptions import HTTPException

from app.core.observability import count_rate_limit_rejection

AUTH_REGISTER_LIMIT = 60
AUTH_LOGIN_LIMIT = 60
WRITE_LIMIT = 300
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
    forwarded = request.headers.get("x-forwarded-for", "")
    candidate = forwarded.split(",")[0].strip()
    if candidate:
        return candidate
    return getattr(request.client, "host", "unknown")


def _enforce(request: Request, limiter: RateLimiter) -> None:
    """Reject over-limit requests with 429 and standard throttling headers."""
    allowed, retry_after = limiter.consume(client_key(request))
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


def enforce_write_limit(request: Request) -> None:
    """Throttle cart and product writes per client (flood protection)."""
    _enforce(request, write_limiter)


def reset_rate_limit_state() -> None:
    """Clear every limiter bucket. Test isolation only; never route through."""
    auth_register_limiter.reset()
    auth_login_limiter.reset()
    write_limiter.reset()
