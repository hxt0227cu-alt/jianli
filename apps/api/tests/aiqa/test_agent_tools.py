"""DB-free tests for the two-phase function-calling pipeline (TASK-AGENT-TOOLS-002).

The stub gateway cannot exercise "the model generates its own retrieval query", so this
suite drives ``AnswerService.stream_answer`` with fake gateways that mimic an OpenAI-compatible
provider: a first round that either emits a ``tool_call`` (model decided to search, with a
model-chosen query) or emits text deltas directly (model decided not to search), then a
second round that emits the final answer. No database, no Redis, no network.

Covered decisions (docs/api/sse.md §3, TASK-AGENT-TOOLS-002):
- model-generated query is what actually gets searched (grounded, citations, decision frame)
- model decides not to search -> system fallback on the original question still grounds
- model searches but finds nothing -> tool frame with empty hits + off-topic refusal
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from app.aiqa.gateway import LLMGateway
from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.service import AnswerService
from app.aiqa.storage import KnowledgeStorage


class _FakeGateway:
    """Mimic OpenAIGateway: optional tool_call on the first round, delta on the last.

    ``tool_query``: when set, the first round (tools offered) yields a search_knowledge
    call with that query; otherwise it yields a plain delta (model chose not to search).
    Every round after a tool decision yields the final delta (the fake has no recursion).
    """

    def __init__(self, tool_query: str | None = None) -> None:
        self._tool_query = tool_query
        self._rounds = 0

    @property
    def model_name(self) -> str:
        return "fake"

    async def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        self._rounds += 1
        first_round = tools is not None
        if first_round and self._tool_query is not None:
            yield (
                "tool_call",
                {
                    "name": "search_knowledge",
                    "arguments": json.dumps({"query": self._tool_query}),
                },
            )
            return
        yield ("delta", "（模拟回答）以上内容基于检索到的项目资料。")
        return


def _collect(
    service: AnswerService,
    question: str,
    page_key: str,
    project_key: str | None,
) -> list[tuple[str, dict[str, object]]]:
    async def _run() -> list[tuple[str, dict[str, object]]]:
        events: list[tuple[str, dict[str, object]]] = []
        async for raw in service.stream_answer(
            question=question,
            page_key=page_key,
            project_key=project_key,
            principal=None,
            conversation_id=None,
        ):
            # stream_answer yields raw SSE strings; parse them like the router does.
            for block in raw.strip().split("\n\n"):
                event = ""
                data_lines: list[str] = []
                for line in block.split("\n"):
                    if line.startswith("event:"):
                        event = line[len("event:") :].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[len("data:") :].strip())
                if event and data_lines:
                    events.append((event, json.loads("".join(data_lines))))
        return events

    return asyncio.run(_run())


def _service(tmp_path: Path, gateway: LLMGateway) -> AnswerService:
    return AnswerService(
        gateway,
        AnswerRateLimiter(),
        repository=None,
        embedder=None,
        knowledge_repository=None,
        storage=KnowledgeStorage(str(tmp_path / "knowledge")),
        min_score=0.0,
    )


@pytest.mark.parametrize(
    ("question", "tool_query"),
    [("介绍下 jianli 的技术栈", "jianli 技术栈"), ("jianli 项目做什么", "RAG 问答")],
)
def test_model_generated_query_is_what_gets_searched(
    tmp_path: Path, question: str, tool_query: str
) -> None:
    """The model's own retrieval query (not the raw question) drives the search."""
    service = _service(tmp_path, _FakeGateway(tool_query=tool_query))
    events = _collect(service, question, "projects", "jianli")
    names = [name for name, _ in events]
    assert "answer.tool_calls" in names
    completed = dict(events[-1][1])
    assert completed["grounded"] is True and completed["offtopic"] is False

    calls = next(d["calls"] for name, d in events if name == "answer.tool_calls")
    assert calls[0]["name"] == "search_knowledge"
    assert calls[0]["query"] == tool_query  # model-generated query, not the raw question
    assert calls[0]["hits"], "jianli project content must be hit by the tool query"
    assert all("storage_key" not in hit and "text" not in hit for hit in calls[0]["hits"])

    citations = next(d["citations"] for name, d in events if name == "answer.citations")
    assert all(str(c["doc"]) == "jianli" for c in citations)


def test_model_skips_tool_system_fallback_grounds(tmp_path: Path) -> None:
    """Model decides not to search -> system fallback on the original question still grounds."""
    service = _service(tmp_path, _FakeGateway(tool_query=None))
    events = _collect(service, "jianli 技术栈是什么", "projects", "jianli")
    completed = dict(events[-1][1])
    assert completed["grounded"] is True and completed["offtopic"] is False
    calls = next(d["calls"] for name, d in events if name == "answer.tool_calls")
    assert calls[0]["query"] == "jianli 技术栈是什么"  # fallback searched the raw question
    assert calls[0]["hits"]


def test_model_searches_but_no_hits_refuses(tmp_path: Path) -> None:
    """Model calls the tool but nothing matches -> empty hits frame + off-topic refusal."""
    service = _service(tmp_path, _FakeGateway(tool_query="量子纠缠"))
    events = _collect(service, "量子纠缠原理", "projects", "jianli")
    names = [name for name, _ in events]
    assert names[-1] == "answer.completed"
    completed = dict(events[-1][1])
    assert completed["grounded"] is False and completed["offtopic"] is True
    calls = next(d["calls"] for name, d in events if name == "answer.tool_calls")
    assert calls[0]["query"] == "量子纠缠"
    assert calls[0]["hits"] == []
    delta_text = "".join(d["text"] for name, d in events if name == "answer.delta")
    assert "不在我公开分享的范围" in delta_text
