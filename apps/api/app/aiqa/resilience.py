"""Small, thread-safe circuit breaker for external AI providers."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any, Literal

CircuitEvent = Literal["opened", "rejected", "recovered"]
CircuitState = Literal["closed", "open", "half_open"]


class CircuitOpenError(RuntimeError):
    """Raised when an open circuit rejects a provider call."""


class CircuitBreaker:
    """Count logical failures and allow exactly one recovery probe."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_seconds: float = 30.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        on_event: Callable[[CircuitEvent], None] | None = None,
    ) -> None:
        self._failure_threshold = max(1, failure_threshold)
        self._recovery_seconds = max(0.0, recovery_seconds)
        self._clock = clock
        self._on_event = on_event
        self._lock = threading.Lock()
        self._state: CircuitState = "closed"
        self._failures = 0
        self._opened_at = 0.0
        self._probe_in_flight = False

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    def before_call(self) -> None:
        event: CircuitEvent | None = None
        rejected = False
        with self._lock:
            if self._state == "closed":
                return
            if self._state == "open":
                elapsed = self._clock() - self._opened_at
                if elapsed >= self._recovery_seconds and not self._probe_in_flight:
                    self._state = "half_open"
                    self._probe_in_flight = True
                    return
            event = "rejected"
            rejected = True
        self._emit(event)
        if rejected:
            raise CircuitOpenError("provider circuit is open")

    def record_success(self) -> None:
        event: CircuitEvent | None = None
        with self._lock:
            if self._state != "closed":
                event = "recovered"
            self._state = "closed"
            self._failures = 0
            self._probe_in_flight = False
        self._emit(event)

    def record_failure(self) -> None:
        event: CircuitEvent | None = None
        with self._lock:
            if self._state == "half_open":
                self._state = "open"
                self._opened_at = self._clock()
                self._probe_in_flight = False
                event = "opened"
            elif self._state == "closed":
                self._failures += 1
                if self._failures >= self._failure_threshold:
                    self._state = "open"
                    self._opened_at = self._clock()
                    event = "opened"
        self._emit(event)

    def _emit(self, event: CircuitEvent | None) -> None:
        if event is not None and self._on_event is not None:
            self._on_event(event)


_BEFORE_CALL_LUA = """-- jianli-circuit-before
local state = redis.call('HGET', KEYS[1], 'state')
if not state or state == 'closed' then return 1 end
if state == 'half_open' then return 0 end
local now = redis.call('TIME')
local now_ms = now[1] * 1000 + math.floor(now[2] / 1000)
local opened_at = tonumber(redis.call('HGET', KEYS[1], 'opened_at') or '0')
if now_ms - opened_at < tonumber(ARGV[1]) then return 0 end
redis.call('HSET', KEYS[1], 'state', 'half_open')
redis.call('PEXPIRE', KEYS[1], ARGV[2])
return 2
"""

_RECORD_FAILURE_LUA = """-- jianli-circuit-failure
local state = redis.call('HGET', KEYS[1], 'state') or 'closed'
if state == 'open' then return 0 end
local now = redis.call('TIME')
local now_ms = now[1] * 1000 + math.floor(now[2] / 1000)
if state == 'half_open' then
  redis.call('HSET', KEYS[1], 'state', 'open', 'failures', ARGV[1], 'opened_at', now_ms)
  redis.call('PEXPIRE', KEYS[1], ARGV[2])
  return 1
end
local failures = redis.call('HINCRBY', KEYS[1], 'failures', 1)
if failures >= tonumber(ARGV[1]) then
  redis.call('HSET', KEYS[1], 'state', 'open', 'opened_at', now_ms)
  redis.call('PEXPIRE', KEYS[1], ARGV[2])
  return 1
end
redis.call('HSET', KEYS[1], 'state', 'closed')
redis.call('PEXPIRE', KEYS[1], ARGV[2])
return 0
"""

_RECORD_SUCCESS_LUA = """-- jianli-circuit-success
local state = redis.call('HGET', KEYS[1], 'state')
redis.call('DEL', KEYS[1])
if state and state ~= 'closed' then return 1 end
return 0
"""


class RedisCircuitBreaker(CircuitBreaker):
    """Redis-shared breaker with atomic Lua transitions and local failure fallback."""

    _COMPONENTS = ("llm", "reranker")

    def __init__(
        self,
        redis_client: Any,
        component: Literal["llm", "reranker"],
        failure_threshold: int = 3,
        recovery_seconds: float = 30.0,
        *,
        on_event: Callable[[CircuitEvent], None] | None = None,
    ) -> None:
        if component not in self._COMPONENTS:
            raise ValueError("unsupported circuit component")
        super().__init__(failure_threshold, recovery_seconds, on_event=on_event)
        self._redis = redis_client
        self._key = f"jianli:aiqa:circuit:{component}"
        self._failure_threshold = max(1, failure_threshold)
        self._recovery_ms = max(1, int(recovery_seconds * 1000))
        self._ttl_ms = max(60_000, self._recovery_ms * 4)
        self._distributed_event = on_event
        self._fallback = CircuitBreaker(
            failure_threshold, recovery_seconds, on_event=on_event
        )

    @property
    def state(self) -> CircuitState:
        try:
            raw = self._redis.hget(self._key, "state")
        except Exception:
            return self._fallback.state
        value = raw.decode() if isinstance(raw, bytes) else raw
        if value == "open":
            return "open"
        if value == "half_open":
            return "half_open"
        return "closed"

    def before_call(self) -> None:
        try:
            result = int(
                self._redis.eval(
                    _BEFORE_CALL_LUA, 1, self._key, self._recovery_ms, self._ttl_ms
                )
            )
        except Exception:
            self._fallback.before_call()
            return
        if result == 0:
            self._emit_distributed("rejected")
            raise CircuitOpenError("provider circuit is open")

    def record_failure(self) -> None:
        try:
            opened = int(
                self._redis.eval(
                    _RECORD_FAILURE_LUA,
                    1,
                    self._key,
                    self._failure_threshold,
                    self._ttl_ms,
                )
            )
        except Exception:
            self._fallback.record_failure()
            return
        if opened == 1:
            self._emit_distributed("opened")

    def record_success(self) -> None:
        try:
            recovered = int(self._redis.eval(_RECORD_SUCCESS_LUA, 1, self._key))
        except Exception:
            self._fallback.record_success()
            return
        self._fallback.record_success()
        if recovered == 1:
            self._emit_distributed("recovered")

    def _emit_distributed(self, event: CircuitEvent) -> None:
        if self._distributed_event is not None:
            self._distributed_event(event)
