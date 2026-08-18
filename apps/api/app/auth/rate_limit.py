"""Redis-backed atomic authentication rate limits."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Protocol

from .errors import AuthError

_CONSUME_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 or current == tonumber(ARGV[2]) then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
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
        return f"auth:login:account:{self.account_tag(email)}"

    def account_tag(self, email: str) -> str:
        return hmac.new(self._hmac_key, email.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _ip_key(ip: str) -> str:
        truncated = ip.rsplit(".", 1)[0] if "." in ip else ip[:19]
        return f"auth:login:ip:{truncated}"

    def _consume(self, key: str, block_at: int, window_seconds: int) -> RateDecision:
        try:
            current, ttl = self._client.eval(_CONSUME_SCRIPT, 1, key, window_seconds, block_at)
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

    # --- Verification-code issuance / verify throttling (TASK-AUTH-VERIFY-CODE-001) ---
    # PRD §5: registration code send = 60s/1 per email, ≤3 per hour per email,
    #         ≤5 per hour per IP (SRS §5.6). Brute force on the 6-digit code is
    #         additionally throttled per IP (≤10 verify attempts / min).

    @staticmethod
    def _code_send_email_key(email: str, kind: str) -> str:
        return f"auth:code:send:{kind}:email:{email}"

    @staticmethod
    def _code_send_email_hour_key(email: str, kind: str) -> str:
        return f"auth:code:send:{kind}:email:{email}:hour"

    @staticmethod
    def _code_send_ip_hour_key(ip: str) -> str:
        truncated = ip.rsplit(".", 1)[0] if "." in ip else ip[:19]
        return f"auth:code:send:ip:{truncated}:hour"

    @staticmethod
    def _verify_ip_key(ip: str) -> str:
        truncated = ip.rsplit(".", 1)[0] if "." in ip else ip[:19]
        return f"auth:code:verify:ip:{truncated}"

    def check_verify_code_send(self, email: str, ip: str, kind: str) -> None:
        """Enforce issuance limits before emailing a code (register / reset request).

        ``kind`` ("verify" | "reset") keeps the two code streams counted
        independently (PRD §5 throttles the registration stream; the reset stream
        gets the same thresholds so abuse of either is bounded).
        """

        for key, block_at, window in (
            (self._code_send_email_key(email, kind), 2, 60),          # 60s / 1
            (self._code_send_email_hour_key(email, kind), 4, 3600),   # ≤3 per hour
            (self._code_send_ip_hour_key(ip), 6, 3600),               # ≤5 per hour per IP
        ):
            decision = self._consume(key, block_at, window)
            if not decision.allowed:
                raise AuthError(
                    "RATE_LIMITED",
                    429,
                    "Verification code rate limited",
                    "Too many code requests, try again later",
                    decision.retry_after_seconds,
                )

    def check_verify_ip(self, ip: str) -> None:
        """Throttle verify attempts per IP (≤10 / min) to block 6-digit brute force."""

        decision = self._consume(self._verify_ip_key(ip), 11, 60)
        if not decision.allowed:
            raise AuthError(
                "RATE_LIMITED",
                429,
                "Rate limited",
                "Too many verification attempts, try again later",
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
