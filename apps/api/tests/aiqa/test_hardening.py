"""TASK-M6-HARDENING-001: production-readiness hardening (DB-free).

Covers the four "should implement" items from the risk review:
- P0-1  LLM gateway exponential-backoff retry (5xx/network retryable, 4xx not) + usage capture
- P0-2  multi-turn memory backfill (recent history injected into the prompt)
- P0-3  structured observability (JsonFormatter optional fields)
- P1-2  token usage surfaced through the completed SSE frame

No database, no Redis, no network: the gateway retry is exercised with httpx.MockTransport,
and the service tests use fake in-memory collaborators.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from app.aiqa.gateway import GatewayError, OpenAIGateway, _RetryableError
from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.retrieval import Candidate
from app.aiqa.service import AnswerService
from app.logging_config import JsonFormatter

# ------------------------------------------------------------- gateway retry + usage


_SSE_OK = (
    'data: {"choices":[{"delta":{"content":"你好"}}]}\n\n'
    'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2,"total_tokens":7}}\n\n'
    "data: [DONE]\n\n"
)


def _parse_frames(frames: list[str]) -> list[tuple[str, dict[str, object]]]:
    """Parse the raw SSE frame strings yielded by ``stream_answer`` into (event, data) pairs."""
    out: list[tuple[str, dict[str, object]]] = []
    for block in frames:
        name = ""
        data_parts: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_parts.append(line[len("data:") :].strip())
        if name and data_parts:
            out.append((name, json.loads("".join(data_parts))))
    return out


@pytest.fixture
def mock_transport(monkeypatch: pytest.MonkeyPatch):
    """Patch ``httpx.AsyncClient`` (the gateway lazy-imports it) with a MockTransport handler.

    The handler increments ``calls[0]`` per upstream attempt. Returns (install, calls) where
    install(handler) wires the patch and calls is the shared attempt counter.
    """

    orig_async_client = httpx.AsyncClient
    state: dict[str, object] = {"handler": None}

    def _make(*_args: object, **kwargs: object) -> httpx.AsyncClient:
        transport = httpx.MockTransport(state["handler"])
        return orig_async_client(transport=transport, timeout=kwargs.get("timeout", 30))

    monkeypatch.setattr(httpx, "AsyncClient", _make)

    calls: list[int] = [0]

    def install(handler) -> list[int]:
        state["handler"] = handler
        return calls

    yield install, calls


@pytest.mark.asyncio
async def test_gateway_retries_on_500_then_succeeds(
    mock_transport: tuple,
) -> None:
    install, calls = mock_transport

    def handler(request: httpx.Request) -> httpx.Response:
        calls[0] += 1
        if calls[0] < 2:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, text=_SSE_OK)

    install(handler)
    gateway = OpenAIGateway("http://llm.test", "k", "m", 30, max_retries=3)

    events = [ev async for ev in gateway.answer([{"role": "user", "content": "hi"}])]

    assert calls[0] == 2, "first 500 must trigger exactly one retry"
    kinds = [kind for kind, _ in events]
    assert ("delta", "你好") in events
    assert ("usage", {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}) in events
    assert "tool_call" not in kinds


@pytest.mark.asyncio
async def test_gateway_does_not_retry_4xx(mock_transport: tuple) -> None:
    install, calls = mock_transport

    def handler(request: httpx.Request) -> httpx.Response:
        calls[0] += 1
        return httpx.Response(400, text="bad request")

    install(handler)
    gateway = OpenAIGateway("http://llm.test", "k", "m", 30, max_retries=3)

    with pytest.raises(GatewayError):
        async for _ in gateway.answer([{"role": "user", "content": "hi"}]):
            pass
    assert calls[0] == 1, "4xx is permanent and must not be retried"


@pytest.mark.asyncio
async def test_gateway_retry_exhausted_raises(mock_transport: tuple) -> None:
    install, calls = mock_transport

    def handler(request: httpx.Request) -> httpx.Response:
        calls[0] += 1
        return httpx.Response(503, text="unavailable")

    install(handler)
    gateway = OpenAIGateway("http://llm.test", "k", "m", 30, max_retries=1)

    with pytest.raises(GatewayError):
        async for _ in gateway.answer([{"role": "user", "content": "hi"}]):
            pass
    assert calls[0] == 1


def test_retryable_error_is_gateway_error() -> None:
    assert issubclass(_RetryableError, GatewayError)


# ------------------------------------------------------------- multi-turn memory backfill


class _RecordingGateway:
    """Stub-like gateway that records the messages it received and emits a tool call (Phase1)
    or a delta + usage (Phase2)."""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    @property
    def model_name(self) -> str:
        return "stub"

    async def answer(
        self, messages: list[dict[str, str]], tools: list[dict[str, object]] | None = None
    ):
        self.calls.append(messages)
        if tools:
            yield (
                "tool_call",
                {"name": "search_knowledge", "arguments": json.dumps({"query": "q"})},
            )
            return
        yield ("delta", "ans")
        yield (
            "usage",
            {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        )


class _FakeRepo:
    def __init__(self, prior: list[dict[str, object]]) -> None:
        self.prior = prior

    def list_messages(self, _conv_id: object) -> list[dict[str, object]]:
        return self.prior

    def append_message(self, *args: object, **kwargs: object) -> None:
        pass

    def touch(self, *args: object, **kwargs: object) -> None:
        pass


async def _fake_candidates(*_args: object, **_kwargs: object) -> list[Candidate]:
    return [Candidate(doc="resume", fragment=1, text="x", score=1.0)]


@pytest.mark.asyncio
async def test_memory_backfill_injects_history_and_surfaces_usage() -> None:
    prior = [
        {
            "id": i,
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"prior message {i}",
            "is_offtopic": False,
            "created_at": datetime.now(UTC),
        }
        for i in range(2)
    ]
    repo = _FakeRepo(prior)
    gw = _RecordingGateway()
    svc = AnswerService(gw, AnswerRateLimiter(), repo)
    svc._search_candidates = _fake_candidates  # type: ignore[assignment]

    frames = [
        ev
        async for ev in svc.stream_answer(
            question="它用了什么向量库？",
            page_key="resume",
            project_key=None,
            principal=object(),
            conversation_id=uuid4(),
        )
    ]
    events = _parse_frames(frames)

    # Phase1 messages must carry the prior history (the digital twin "remembers").
    assert any("prior message 0" in m["content"] for m in gw.calls[0])
    # The current question is NOT part of history (loaded before the user message is stored).
    assert all(m["content"] != "它用了什么向量库？" for m in gw.calls[0][1:-1])

    completed = next(d for name, d in events if name == "answer.completed")
    assert completed["grounded"] is True
    assert completed["usage"]["total_tokens"] == 4


@pytest.mark.asyncio
async def test_memory_backfill_is_bounded() -> None:
    prior = [
        {
            "id": i,
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"prior message {i}",
            "is_offtopic": False,
            "created_at": datetime.now(UTC),
        }
        for i in range(10)
    ]
    repo = _FakeRepo(prior)
    gw = _RecordingGateway()
    svc = AnswerService(gw, AnswerRateLimiter(), repo)
    svc._search_candidates = _fake_candidates  # type: ignore[assignment]

    _ = [
        ev
        async for ev in svc.stream_answer(
            question="它用了什么向量库？",
            page_key="resume",
            project_key=None,
            principal=object(),
            conversation_id=uuid4(),
        )
    ]

    history = [m for m in gw.calls[0][1:-1] if m["role"] in ("user", "assistant")]
    assert len(history) == 6, "history must be capped at _MAX_HISTORY_MESSAGES"
    # The earliest injected message is prior[4] (last 6 of 10 => indices 4..9).
    assert history[0]["content"] == "prior message 4"


@pytest.mark.asyncio
async def test_anonymous_stream_has_no_history() -> None:
    gw = _RecordingGateway()
    svc = AnswerService(gw, AnswerRateLimiter(), None)
    svc._search_candidates = _fake_candidates  # type: ignore[assignment]

    _ = [
        ev
        async for ev in svc.stream_answer(
            question="它用了什么向量库？",
            page_key="resume",
            project_key=None,
            principal=None,
            conversation_id=None,
        )
    ]
    # Anonymous: only system + the single current user message, no prior turns.
    history = [m for m in gw.calls[0] if m["role"] in ("user", "assistant")]
    assert len(history) == 1


# ------------------------------------------------------------- observability formatter


def test_json_formatter_includes_optional_fields() -> None:
    rec = logging.LogRecord("jianli.aiqa", logging.INFO, "p", 1, "answer_completed", None, None)
    rec.trace_id = "t1"
    rec.latency_ms = 12
    rec.grounded = True
    rec.offtopic = False
    rec.model = "stub"
    rec.prompt_tokens = 1
    rec.completion_tokens = 2
    out = JsonFormatter().format(rec)
    assert '"trace_id":"t1"' in out
    assert '"latency_ms":12' in out
    assert '"prompt_tokens":1' in out
    assert '"model":"stub"' in out


def test_json_formatter_omits_absent_fields() -> None:
    rec = logging.LogRecord("jianli.aiqa", logging.INFO, "p", 1, "plain_event", None, None)
    out = JsonFormatter().format(rec)
    assert "trace_id" not in out
    assert "latency_ms" not in out
