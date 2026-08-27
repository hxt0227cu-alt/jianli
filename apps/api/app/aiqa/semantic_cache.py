"""Privacy-minimal Redis semantic answer cache."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class SemanticCacheError(RuntimeError):
    """Cache is unavailable or contains invalid data; callers must bypass it."""


@dataclass(frozen=True, slots=True)
class CachedAnswer:
    answer: str
    citations: list[dict[str, object]]
    model: str
    similarity: float


@runtime_checkable
class SemanticCache(Protocol):
    def lookup(self, namespace: str, embedding: list[float]) -> CachedAnswer | None: ...

    def put(
        self,
        namespace: str,
        embedding: list[float],
        answer: str,
        citations: list[dict[str, object]],
        model: str,
    ) -> None: ...

    def invalidate_all(self) -> None: ...


class SemanticAnswerCache:
    """Bounded list-per-domain cache; entries intentionally omit question plaintext."""

    _PREFIX = "jianli:aiqa:semantic"

    def __init__(
        self,
        redis_client: Any,
        *,
        similarity_threshold: float = 0.94,
        ttl_seconds: int = 600,
        max_entries: int = 100,
    ) -> None:
        self._redis = redis_client
        self._threshold = similarity_threshold
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries

    @classmethod
    def namespace(cls, page_key: str, project_key: str | None) -> str:
        digest = hashlib.sha256(f"{page_key}\x00{project_key or ''}".encode()).hexdigest()[:20]
        return f"{cls._PREFIX}:domain:{digest}"

    def lookup(self, namespace: str, embedding: list[float]) -> CachedAnswer | None:
        try:
            rows = self._redis.lrange(namespace, 0, self._max_entries - 1)
            best: CachedAnswer | None = None
            for raw in rows:
                item = json.loads(raw)
                stored = item["embedding"]
                if not isinstance(stored, list) or len(stored) != len(embedding):
                    continue
                similarity = _cosine(embedding, [float(value) for value in stored])
                if similarity < self._threshold or (
                    best is not None and similarity <= best.similarity
                ):
                    continue
                citations = item["citations"]
                if not isinstance(citations, list):
                    continue
                best = CachedAnswer(
                    answer=str(item["answer"]),
                    citations=citations,
                    model=str(item["model"]),
                    similarity=similarity,
                )
            return best
        except Exception as error:
            raise SemanticCacheError("semantic cache lookup failed") from error

    def put(
        self,
        namespace: str,
        embedding: list[float],
        answer: str,
        citations: list[dict[str, object]],
        model: str,
    ) -> None:
        payload = json.dumps(
            {
                "embedding": embedding,
                "answer": answer,
                "citations": citations,
                "model": model,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        try:
            pipeline = self._redis.pipeline(transaction=True)
            pipeline.lpush(namespace, payload)
            pipeline.ltrim(namespace, 0, self._max_entries - 1)
            pipeline.expire(namespace, self._ttl_seconds)
            pipeline.sadd(f"{self._PREFIX}:namespaces", namespace)
            pipeline.expire(f"{self._PREFIX}:namespaces", self._ttl_seconds)
            pipeline.execute()
        except Exception as error:
            raise SemanticCacheError("semantic cache write failed") from error

    def invalidate_all(self) -> None:
        registry = f"{self._PREFIX}:namespaces"
        try:
            namespaces = list(self._redis.smembers(registry))
            if namespaces:
                self._redis.delete(*namespaces)
            self._redis.delete(registry)
        except Exception as error:
            raise SemanticCacheError("semantic cache invalidation failed") from error


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
