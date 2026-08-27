"""TC-AI-013: provider circuit breaker state and integration."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest

from app.aiqa.gateway import GatewayError, OpenAIGateway, _RetryableError
from app.aiqa.reranker import CrossEncoderReranker, RerankerError
from app.aiqa.resilience import CircuitBreaker, CircuitOpenError


def test_closed_open_half_open_closed_and_single_probe() -> None:
    now = [10.0]
    events: list[str] = []
    breaker = CircuitBreaker(2, 30, clock=lambda: now[0], on_event=events.append)

    breaker.before_call()
    breaker.record_failure()
    breaker.before_call()
    breaker.record_failure()
    assert breaker.state == "open"
    with pytest.raises(CircuitOpenError):
        breaker.before_call()

    now[0] += 30
    breaker.before_call()
    assert breaker.state == "half_open"
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    breaker.record_success()

    assert breaker.state == "closed"
    assert events == ["opened", "rejected", "rejected", "recovered"]


def test_llm_and_reranker_breakers_are_independent() -> None:
    llm = CircuitBreaker(1, 30)
    reranker = CircuitBreaker(1, 30)
    llm.record_failure()

    with pytest.raises(CircuitOpenError):
        llm.before_call()
    reranker.before_call()
    assert reranker.state == "closed"


@pytest.mark.asyncio
async def test_open_llm_gateway_skips_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def fail_once(
        self: OpenAIGateway,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        nonlocal calls
        calls += 1
        raise _RetryableError("unavailable")
        yield ("delta", "unreachable")

    monkeypatch.setattr(OpenAIGateway, "_stream_once", fail_once)
    breaker = CircuitBreaker(1, 30)
    gateway = OpenAIGateway("https://provider", "secret", "model", 1, 1, breaker)

    with pytest.raises(GatewayError):
        await _collect(gateway.answer([]))
    with pytest.raises(GatewayError, match="circuit"):
        await _collect(gateway.answer([]))
    assert calls == 1


def test_open_reranker_skips_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fail(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("private provider detail")

    monkeypatch.setattr(httpx, "post", fail)
    breaker = CircuitBreaker(1, 30)
    reranker = CrossEncoderReranker("https://provider", "secret", "model", 1, breaker)

    with pytest.raises(RerankerError):
        reranker.rerank("q", ["doc"], 1)
    with pytest.raises(RerankerError, match="circuit"):
        reranker.rerank("q", ["doc"], 1)
    assert calls == 1


async def _collect(
    events: AsyncIterator[tuple[str, str | dict[str, object]]],
) -> list[tuple[str, str | dict[str, object]]]:
    return [event async for event in events]
