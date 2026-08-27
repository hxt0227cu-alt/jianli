"""TC-AI-012: Cross-Encoder ordering, strict protocol, and RRF fallback."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.aiqa.gateway import StubGateway
from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.reranker import CrossEncoderReranker, RerankerError, RerankResult
from app.aiqa.service import AnswerService
from app.aiqa.storage import KnowledgeStorage


class _Embedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class _Repository:
    def search_chunks(self, *_args: object, **_kwargs: object) -> list[dict[str, object]]:
        return [{"chunk_id": "a"}, {"chunk_id": "b"}, {"chunk_id": "c"}]

    def load_chunk_corpus(self, **_kwargs: object) -> list[tuple[str, str]]:
        return [
            ("a", "Python FastAPI 后端开发"),
            ("b", "Agent 工具权限与 RBAC"),
            ("c", "RAG 混合检索和评测"),
        ]

    def chunk_rows(self, chunk_ids: list[str]) -> dict[str, dict[str, object]]:
        rows = {
            "a": {"doc_name": "resume", "seq": 1, "content": "Python FastAPI 后端开发"},
            "b": {"doc_name": "resume", "seq": 2, "content": "Agent 工具权限与 RBAC"},
            "c": {"doc_name": "resume", "seq": 3, "content": "RAG 混合检索和评测"},
        }
        return {chunk_id: rows[chunk_id] for chunk_id in chunk_ids}


class _ReverseReranker:
    model_name = "cross-encoder-test"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.documents: list[str] = []

    def rerank(self, query: str, documents: list[str], top_n: int) -> list[RerankResult]:
        assert query == "Agent 权限"
        self.documents = documents
        if self.fail:
            raise RerankerError("provider_unavailable")
        indices = list(reversed(range(len(documents))))[:top_n]
        return [
            RerankResult(index=index, score=1 - rank / 10)
            for rank, index in enumerate(indices)
        ]


def _service(tmp_path: Any, reranker: _ReverseReranker | None) -> AnswerService:
    return AnswerService(
        StubGateway(),
        AnswerRateLimiter(),
        embedder=_Embedder(),
        knowledge_repository=_Repository(),  # type: ignore[arg-type]
        storage=KnowledgeStorage(str(tmp_path)),
        reranker=reranker,
        rerank_top_n=3,
    )


@pytest.mark.asyncio
async def test_cross_encoder_reorders_only_recalled_candidates(tmp_path: Any) -> None:
    reranker = _ReverseReranker()
    candidates = await _service(tmp_path, reranker)._knowledge_candidates(
        "Agent 权限", "resume", None
    )

    assert [candidate.text for candidate in candidates] == list(reversed(reranker.documents))
    assert {candidate.text for candidate in candidates} == set(reranker.documents)
    assert [candidate.score for candidate in candidates] == [1.0, 0.9, 0.8]


@pytest.mark.asyncio
async def test_provider_failure_preserves_rrf_order(tmp_path: Any) -> None:
    baseline = await _service(tmp_path, None)._knowledge_candidates("Agent 权限", "resume", None)
    fallback = await _service(tmp_path, _ReverseReranker(fail=True))._knowledge_candidates(
        "Agent 权限", "resume", None
    )
    assert fallback == baseline


def test_gateway_sends_minimal_payload_and_parses_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        captured.update({"url": url, **kwargs})
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 1, "relevance_score": 0.91},
                    {"index": 0, "relevance_score": 0.42},
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    gateway = CrossEncoderReranker("https://provider.test/v1", "secret", "reranker", 2)
    results = gateway.rerank("query", ["authorized-a", "authorized-b"], 2)

    assert results == [RerankResult(1, 0.91), RerankResult(0, 0.42)]
    assert captured["url"] == "https://provider.test/v1/rerank"
    assert captured["json"] == {
        "model": "reranker",
        "query": "query",
        "documents": ["authorized-a", "authorized-b"],
        "top_n": 2,
        "return_documents": False,
    }
    assert captured["headers"] == {"Authorization": "Bearer secret"}


def test_gateway_rejects_out_of_range_or_incomplete_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*_args: Any, **_kwargs: Any) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"index": 9, "relevance_score": 1}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    gateway = CrossEncoderReranker("https://provider.test/v1", "secret", "reranker", 2)
    with pytest.raises(RerankerError, match="invalid_response"):
        gateway.rerank("query", ["a", "b"], 2)
