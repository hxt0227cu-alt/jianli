"""TC-AI-014: Redis-shared circuit state and local fail-open fallback."""

from __future__ import annotations

import os
import threading
import time

import pytest
import redis

from app.aiqa.resilience import CircuitOpenError, RedisCircuitBreaker


class SharedFakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, str | int]] = {}
        self.lock = threading.Lock()
        self.now_ms = 1_000
        self.ttls: dict[str, int] = {}
        self.unavailable = False

    def hget(self, key: str, field: str) -> str | int | None:
        if self.unavailable:
            raise ConnectionError("redis unavailable")
        return self.data.get(key, {}).get(field)

    def eval(self, script: str, key_count: int, key: str, *args: object) -> int:
        if self.unavailable:
            raise ConnectionError("redis unavailable")
        assert key_count == 1
        with self.lock:
            row = self.data.get(key)
            if "circuit-before" in script:
                if row is None or row.get("state") == "closed":
                    return 1
                if row.get("state") == "half_open":
                    return 0
                recovery_ms, ttl_ms = int(args[0]), int(args[1])
                if self.now_ms - int(row.get("opened_at", 0)) < recovery_ms:
                    return 0
                row["state"] = "half_open"
                self.ttls[key] = ttl_ms
                return 2
            if "circuit-failure" in script:
                threshold, ttl_ms = int(args[0]), int(args[1])
                row = self.data.setdefault(key, {})
                state = row.get("state", "closed")
                if state == "open":
                    return 0
                failures = (
                    threshold
                    if state == "half_open"
                    else int(row.get("failures", 0)) + 1
                )
                row["failures"] = failures
                row["state"] = "open" if failures >= threshold else "closed"
                if row["state"] == "open":
                    row["opened_at"] = self.now_ms
                self.ttls[key] = ttl_ms
                return int(row["state"] == "open")
            if "circuit-success" in script:
                recovered = row is not None and row.get("state") != "closed"
                self.data.pop(key, None)
                return int(recovered)
        raise AssertionError("unknown script")


def test_instances_share_failures_and_one_recovery_probe() -> None:
    shared = SharedFakeRedis()
    first = RedisCircuitBreaker(shared, "llm", 2, 30)
    second = RedisCircuitBreaker(shared, "llm", 2, 30)

    first.record_failure()
    second.record_failure()
    assert first.state == second.state == "open"
    with pytest.raises(CircuitOpenError):
        first.before_call()

    shared.now_ms += 30_000
    first.before_call()
    assert first.state == "half_open"
    with pytest.raises(CircuitOpenError):
        second.before_call()
    first.record_success()
    second.before_call()

    assert first.state == second.state == "closed"
    assert shared.ttls["jianli:aiqa:circuit:llm"] >= 60_000


def test_half_open_failure_reopens_for_every_instance() -> None:
    shared = SharedFakeRedis()
    first = RedisCircuitBreaker(shared, "reranker", 1, 1)
    second = RedisCircuitBreaker(shared, "reranker", 1, 1)
    first.record_failure()
    shared.now_ms += 1_000
    second.before_call()

    second.record_failure()

    assert first.state == "open"
    with pytest.raises(CircuitOpenError):
        first.before_call()


def test_redis_failure_uses_local_breaker() -> None:
    shared = SharedFakeRedis()
    shared.unavailable = True
    breaker = RedisCircuitBreaker(shared, "llm", 1, 30)
    breaker.record_failure()

    with pytest.raises(CircuitOpenError):
        breaker.before_call()


def test_key_contains_only_fixed_component() -> None:
    shared = SharedFakeRedis()
    breaker = RedisCircuitBreaker(shared, "llm", 1, 30)
    breaker.record_failure()

    assert set(shared.data) == {"jianli:aiqa:circuit:llm"}


@pytest.mark.skipif(
    not os.getenv("JIANLI_AIQA_TEST_REDIS_URL"),
    reason="real Redis URL not configured",
)
def test_real_redis_cross_instance_atomic_probe() -> None:
    url = os.environ["JIANLI_AIQA_TEST_REDIS_URL"]
    first_client = redis.Redis.from_url(url, decode_responses=True)
    second_client = redis.Redis.from_url(url, decode_responses=True)
    key = "jianli:aiqa:circuit:llm"
    first_client.delete(key)
    try:
        first = RedisCircuitBreaker(first_client, "llm", 2, 0.05)
        second = RedisCircuitBreaker(second_client, "llm", 2, 0.05)
        first.record_failure()
        second.record_failure()
        with pytest.raises(CircuitOpenError):
            first.before_call()
        time.sleep(0.06)
        first.before_call()
        with pytest.raises(CircuitOpenError):
            second.before_call()
        first.record_success()
        second.before_call()
        assert first_client.exists(key) == 0
    finally:
        first_client.delete(key)
