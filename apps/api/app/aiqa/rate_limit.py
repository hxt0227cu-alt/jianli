"""In-memory fixed-window rate limiter for public (anonymous) answers, M6 round 1.

Contract: ``POST /answers:stream`` stays subject to public answer rate limiting even for
anonymous callers (docs/api/sse.md §3). Round 1 uses a single-process in-memory window
keyed by truncated IP, so no Redis dependency is introduced.

Handoff note for Codex: promote this to a Redis-backed limiter (like
``app/auth/rate_limit.py``) when running more than one instance. The ``consume``
contract — raising ``AuthError("RATE_LIMITED", 429, ...)`` — is what the router relies on.
"""

from __future__ import annotations

import threading
import time

from app.auth.errors import AuthError


class AnswerRateLimiter:
    """Fixed-window limiter: at most ``max_requests`` per ``window_seconds`` per IP."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60) -> None:
        if max_requests < 1 or window_seconds < 1:
            raise ValueError("rate limit bounds must be positive")
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _ip_key(ip: str) -> str:
        return ip.rsplit(".", 1)[0] if "." in ip else ip[:19]

    def consume(self, ip: str) -> None:
        """Record one answer from ``ip``; raise 429 when the window budget is exhausted."""

        key = self._ip_key(ip)
        now = time.monotonic()
        with self._lock:
            stamps = [t for t in self._buckets.get(key, []) if now - t < self._window_seconds]
            if len(stamps) >= self._max_requests:
                retry = int(self._window_seconds - (now - stamps[0])) + 1
                raise AuthError(
                    "RATE_LIMITED",
                    429,
                    "Rate limited",
                    "Try again later",
                    max(retry, 1),
                )
            stamps.append(now)
            self._buckets[key] = stamps
