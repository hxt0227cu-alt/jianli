"""TC-AI-013: bounded, anonymous-only semantic answer reuse."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.aiqa.embeddings import LocalEmbeddingGateway
from app.aiqa.gateway import StubGateway
from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.semantic_cache import SemanticAnswerCache, SemanticCacheError
from app.aiqa.service import AnswerService


class FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.sets: dict[str, set[str]] = {}
        self.expirations: list[tuple[str, int]] = []

    def pipeline(self, transaction: bool = True) -> FakeRedis:
        return self

    def lpush(self, key: str, value: str) -> FakeRedis:
        self.lists.setdefault(key, []).insert(0, value)
        return self

    def ltrim(self, key: str, start: int, stop: int) -> FakeRedis:
        self.lists[key] = self.lists.get(key, [])[start : stop + 1]
        return self

    def expire(self, key: str, seconds: int) -> FakeRedis:
        self.expirations.append((key, seconds))
        return self

    def sadd(self, key: str, value: str) -> FakeRedis:
        self.sets.setdefault(key, set()).add(value)
        return self

    def execute(self) -> list[object]:
        return []

    def lrange(self, key: str, start: int, stop: int) -> list[str]:
        return self.lists.get(key, [])[start : stop + 1]

    def smembers(self, key: str) -> set[str]:
        return self.sets.get(key, set())

    def delete(self, *keys: str) -> int:
        for key in keys:
            self.lists.pop(key, None)
            self.sets.pop(key, None)
        return len(keys)


def test_cache_is_domain_isolated_bounded_and_omits_question_plaintext() -> None:
    redis = FakeRedis()
    cache = SemanticAnswerCache(redis, similarity_threshold=0.94, ttl_seconds=600, max_entries=2)
    resume = cache.namespace("resume", None)
    projects = cache.namespace("projects", None)

    cache.put(resume, [1.0, 0.0], "public answer", [{"doc": "resume"}], "model")
    cache.put(resume, [0.0, 1.0], "second", [], "model")
    cache.put(resume, [0.7, 0.7], "third", [], "model")

    assert len(redis.lists[resume]) == 2
    assert cache.lookup(resume, [0.71, 0.69]).answer == "third"  # type: ignore[union-attr]
    assert cache.lookup(projects, [0.71, 0.69]) is None
    serialized = " ".join(redis.lists[resume])
    assert "question" not in serialized
    assert "user_id" not in serialized
    assert (resume, 600) in redis.expirations


def test_invalidate_all_removes_registered_domains() -> None:
    redis = FakeRedis()
    cache = SemanticAnswerCache(redis)
    first = cache.namespace("resume", None)
    second = cache.namespace("projects", "agent")
    cache.put(first, [1.0], "a", [], "m")
    cache.put(second, [1.0], "b", [], "m")

    cache.invalidate_all()

    assert first not in redis.lists
    assert second not in redis.lists


@pytest.mark.asyncio
async def test_stream_writes_then_hits_cache_without_answer_generation() -> None:
    redis = FakeRedis()
    cache = SemanticAnswerCache(redis)
    gateway = CountingStubGateway()
    service = AnswerService(
        gateway,
        AnswerRateLimiter(),
        embedder=LocalEmbeddingGateway(64),
        semantic_cache=cache,
    )

    first = await _collect(service)
    second = await _collect(service)

    assert gateway.answer_generations == 1
    assert any("语义缓存命中" in event for event in second)
    assert any("grounded\":true" in event for event in first)
    assert any("grounded\":true" in event for event in second)


@pytest.mark.asyncio
async def test_cache_failure_is_bypassed() -> None:
    service = AnswerService(
        StubGateway(),
        AnswerRateLimiter(),
        embedder=LocalEmbeddingGateway(64),
        semantic_cache=FailingCache(),
    )

    events = await _collect(service)

    assert any("grounded\":true" in event for event in events)


class CountingStubGateway(StubGateway):
    def __init__(self) -> None:
        self.answer_generations = 0

    async def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        if tools is None:
            self.answer_generations += 1
        async for event in super().answer(messages, tools):
            yield event


class FailingCache:
    def lookup(self, namespace: str, embedding: list[float]) -> Any:
        raise SemanticCacheError("redis unavailable")

    def put(self, *args: object) -> None:
        raise AssertionError("failed lookup must suppress cache write")

    def invalidate_all(self) -> None:
        raise SemanticCacheError("redis unavailable")


async def _collect(service: AnswerService) -> list[str]:
    return [
        event
        async for event in service.stream_answer(
            question="你擅长什么技术方向？",
            page_key="resume",
            project_key=None,
            principal=None,
            conversation_id=None,
        )
    ]
