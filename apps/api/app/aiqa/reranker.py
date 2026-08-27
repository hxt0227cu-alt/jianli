"""Optional Cross-Encoder reranking over an already-authorized RRF candidate set."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx


class RerankerError(Exception):
    """A provider or protocol failure; callers must retain the original RRF order."""


@dataclass(frozen=True, slots=True)
class RerankResult:
    index: int
    score: float


@runtime_checkable
class RerankerGateway(Protocol):
    @property
    def model_name(self) -> str: ...

    def rerank(self, query: str, documents: list[str], top_n: int) -> list[RerankResult]: ...


class CrossEncoderReranker:
    """Call an OpenAI-style ``POST /rerank`` endpoint with strict response validation."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = min(timeout, 5.0)

    @property
    def model_name(self) -> str:
        return self._model

    def rerank(self, query: str, documents: list[str], top_n: int) -> list[RerankResult]:
        if not documents:
            return []
        payload = {
            "model": self._model,
            "query": query,
            "documents": documents,
            "top_n": min(top_n, len(documents)),
            "return_documents": False,
        }
        try:
            response = httpx.post(
                f"{self._base_url}/rerank",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
                timeout=self._timeout,
            )
        except httpx.HTTPError as error:
            raise RerankerError("provider_unavailable") from error
        if response.status_code >= 400:
            raise RerankerError("provider_rejected")
        try:
            rows = response.json()["results"]
        except (KeyError, TypeError, ValueError) as error:
            raise RerankerError("invalid_response") from error
        if not isinstance(rows, list):
            raise RerankerError("invalid_response")
        results: list[RerankResult] = []
        seen: set[int] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise RerankerError("invalid_response")
            index = row.get("index")
            score = row.get("relevance_score")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or index < 0
                or index >= len(documents)
                or index in seen
                or not isinstance(score, int | float)
                or isinstance(score, bool)
            ):
                raise RerankerError("invalid_response")
            seen.add(index)
            results.append(RerankResult(index=index, score=float(score)))
        expected = min(top_n, len(documents))
        if len(results) != expected:
            raise RerankerError("invalid_response")
        return results


def build_reranker_gateway(
    *, base_url: str | None, api_key: str | None, model: str | None, timeout: float
) -> RerankerGateway | None:
    """Return no gateway unless every secret/config component is present."""

    if base_url and api_key and model:
        return CrossEncoderReranker(base_url, api_key, model, timeout)
    return None
