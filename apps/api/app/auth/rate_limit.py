"""Redis-backed atomic authentication rate limits."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Protocol

from .errors import AuthError

_CONSUME_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""

_CHECK_SCRIPT = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class RedisClient(Protocol):
    def eval(self, script: str, numkeys: int, *keys_and_args: Any) -> Any: ...
    def delete(self, *names: str) -> int: ...
    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RateDecision:
    allowed: bool
    retry_after_seconds: int


class LoginRateLimiter:
    def __init__(self, client: RedisClient, hmac_key: str) -> None:
        key = hmac_key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("rate-limit HMAC key must be at least 32 UTF-8 bytes")
        self._client = client
        self._hmac_key = key

    def _account_key(self, email: str) -> str:
        digest = hmac.new(self._hmac_key, email.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"auth:login:account:{digest}"

    @staticmethod
    def _ip_key(ip: str) -> str:
        truncated = ip.rsplit(".", 1)[0] if "." in ip else ip[:19]
        return f"auth:login:ip:{truncated}"

    def _consume(self, key: str, block_at: int, window_seconds: int) -> RateDecision:
        try:
            current, ttl = self._client.eval(_CONSUME_SCRIPT, 1, key, window_seconds)
        except Exception as error:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limit unavailable",
                "Authentication is temporarily unavailable",
                1,
            ) from error
        return RateDecision(current < block_at, max(int(ttl), 1))

    def check_ip(self, ip: str) -> None:
        decision = self._consume(self._ip_key(ip), 11, 60)
        if not decision.allowed:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limited",
                "Try again later",
                decision.retry_after_seconds,
            )

    def record_failure(self, email: str) -> None:
        decision = self._consume(self._account_key(email), 5, 900)
        if decision.allowed:
            return
        self._raise_limited(decision.retry_after_seconds)

    def check_account(self, email: str) -> None:
        try:
            current, ttl = self._client.eval(_CHECK_SCRIPT, 1, self._account_key(email))
        except Exception as error:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limit unavailable",
                "Authentication is temporarily unavailable",
                1,
            ) from error
        if int(current) >= 5:
            self._raise_limited(max(int(ttl), 1))

    @staticmethod
    def _raise_limited(retry_after_seconds: int) -> None:
        raise AuthError(
            "RATE_LIMITED",
            429,
            "Rate limited",
            "Try again later",
            retry_after_seconds,
        )

    def clear_failures(self, email: str) -> None:
        try:
            self._client.delete(self._account_key(email))
        except Exception as error:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limit unavailable",
                "Authentication is temporarily unavailable",
                1,
            ) from error
