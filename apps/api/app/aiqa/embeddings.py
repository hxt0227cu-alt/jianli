"""Embedding gateway for knowledge-base vector retrieval (M6 round 3).

Two implementations behind one protocol:

* ``LocalEmbeddingGateway`` — deterministic, dependency-free hash embedding of the
  configured dimension. Used whenever no LLM is configured, so upload/indexing and
  vector retrieval run and are testable with zero external services.
* ``OpenAIEmbeddingGateway`` — calls an OpenAI-compatible ``/embeddings`` endpoint via
  httpx (**lazy-imported**, still a dev extra). Requests ``dimensions`` matching the
  ``vector(N)`` column; a response with a different dimension raises ``EmbeddingError``
  instead of silently corrupting rows.

Handoff note for Codex: providers plug in behind ``EmbeddingGateway.embed``; wiring lives
in ``runtime.build_aiqa_runtime``. Keep the vector dimension aligned with migration 0005.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"[a-z0-9]+|[一-鿿]")


class EmbeddingError(Exception):
    """Raised when embedding generation fails or the dimension mismatches the schema."""


@runtime_checkable
class EmbeddingGateway(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingGateway:
    """Deterministic hash-based embedding: stable across runs, no network, no deps."""

    def __init__(self, dimension: int) -> None:
        self._dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self._dimension
            for token in _tokens(text):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self._dimension
                sign = 1.0 if digest[4] & 1 else -1.0
                vector[index] += sign
            vectors.append(_normalize(vector))
        return vectors


class OpenAIEmbeddingGateway:
    """OpenAI-compatible /embeddings via httpx (lazy import; httpx stays a dev extra)."""

    def __init__(
        self, base_url: str, api_key: str, model: str, dimension: int, timeout: float
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dimension = dimension
        self._timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            import httpx  # lazy: httpx is a dev extra, not a runtime dependency
        except ImportError as error:
            raise EmbeddingError("httpx is required for the OpenAI embedding gateway") from error
        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": texts, "dimensions": self._dimension}
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self._timeout)
        except httpx.HTTPError as error:
            raise EmbeddingError(str(error)) from error
        if response.status_code >= 400:
            raise EmbeddingError(f"embedding provider returned {response.status_code}")
        data = response.json()
        vectors: list[list[float]] = []
        for item in data.get("data", []):
            vector = item["embedding"]
            if len(vector) != self._dimension:
                raise EmbeddingError(
                    f"embedding dimension {len(vector)} != schema {self._dimension}"
                )
            vectors.append(vector)
        if len(vectors) != len(texts):
            raise EmbeddingError("embedding provider returned an unexpected row count")
        return vectors


def _tokens(text: str) -> list[str]:
    return [
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) > 1 or ord(tok[0]) >= 0x2E80
    ]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def build_embedding_gateway(
    *,
    base_url: str | None,
    api_key: str | None,
    model: str | None,
    dimension: int,
    timeout: float,
) -> EmbeddingGateway:
    """Pick the embedding implementation from configuration (OpenAI if configured)."""

    if base_url and api_key and model:
        return OpenAIEmbeddingGateway(base_url, api_key, model, dimension, timeout)
    return LocalEmbeddingGateway(dimension)
