"""Small, thread-safe circuit breaker for external AI providers."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Literal

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
