"""DB-free tests for the AI QA (Answer) domain — M6 round 1.

Builds the real application via ``create_app`` (Settings without auth) so the router
mounting, the AuthError/validation handlers and the answer SSE pipeline are all exercised.
No database, no Redis, no network: the stub gateway is deterministic.

Covered contract behavior (docs/api/openapi.yaml + docs/api/sse.md §3):
- getPageContent / listRecommendedQuestions (200, 400 on unknown page_key)
- streamAnswer: grounded stream, greeting, off-topic refusal, anonymous rejection of
  conversation_id (401), invalid-session cookie (401), validation problem (422).
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.aiqa.persona import GREETING_REPLY, OFFTOPIC_REPLY
from app.auth.errors import AuthError
from app.config import Settings
from app.factory import create_app


@pytest.fixture
def client() -> TestClient:
    """Fresh app per test so the in-memory answer rate limiter resets."""

    return TestClient(create_app(Settings()))


def _events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.strip().split("\n\n"):
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


def _answer_stream(
    client: TestClient, **body: object
) -> tuple[int, list[tuple[str, dict[str, object]]]]:
    resp = client.post("/answers:stream", json=body)
    return resp.status_code, _events(resp.text) if resp.status_code == 200 else []


# --------------------------------------------------------------- pages


def test_get_page_content_resume(client: TestClient) -> None:
    resp = client.get("/pages/resume")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_key"] == "resume"
    assert data["title"]
    assert isinstance(data["sections"], list) and data["sections"]
    assert data["updated_at"].endswith("+00:00") or "T" in data["updated_at"]


def test_get_page_content_projects(client: TestClient) -> None:
    resp = client.get("/pages/projects")
    assert resp.status_code == 200
    assert resp.json()["page_key"] == "projects"


def test_get_page_content_unknown_key_problem(client: TestClient) -> None:
    resp = client.get("/pages/unknown")
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "INVALID_REQUEST"
    assert body["status"] == 400
    assert "trace_id" in body


def test_list_recommended_questions(client: TestClient) -> None:
    resp = client.get("/pages/resume/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "fallback"
    assert isinstance(data["items"], list) and len(data["items"]) <= 8


# --------------------------------------------------------------- streamAnswer


def test_stream_answer_grounded_flow(client: TestClient) -> None:
    status, events = _answer_stream(client, question="你擅长什么技术方向？", page_key="resume")
    assert status == 200
    names = [name for name, _ in events]
    assert names[0] == "answer.started"
    assert "answer.delta" in names
    assert "answer.citations" in names
    assert names[-1] == "answer.completed"

    started = dict(events[0][1])
    assert started["answer_id"]
    assert started["conversation_id"] is None
    completed = dict(events[-1][1])
    assert completed["grounded"] is True
    assert completed["offtopic"] is False
    assert completed["model"] == "stub"

    citations = next(d for name, d in events if name == "answer.citations")
    assert citations["citations"], "grounded answers must carry citations"
    for cite in citations["citations"]:
        assert "doc" in cite and "fragment" in cite and "storage_key" not in cite


def test_stream_answer_tool_calls_frame(client: TestClient) -> None:
    """Agent tooling (TASK-AGENT-TOOLS-002): the decision chain frame is emitted once.

    Grounded path: the stub decides to call search_knowledge (query = original question),
    the service executes it and reports hits (doc·fragment summary only — no storage_key,
    no full text). Off-topic path: no hits -> hits is an empty list, still refused.
    """
    status, events = _answer_stream(client, question="你擅长什么技术方向？", page_key="resume")
    assert status == 200
    tool_calls = [d for name, d in events if name == "answer.tool_calls"]
    assert len(tool_calls) == 1, "exactly one decision-chain frame on a grounded answer"
    calls = tool_calls[0]["calls"]
    assert len(calls) == 1
    call = calls[0]
    assert call["name"] == "search_knowledge"
    assert call["query"]
    assert call["hits"], "grounded tool call must report hits"
    for hit in call["hits"]:
        assert "doc" in hit and "fragment" in hit
        assert "storage_key" not in hit
        assert "text" not in hit

    status, events = _answer_stream(client, question="今天天气怎么样？", page_key="resume")
    assert status == 200
    tool_calls = [d for name, d in events if name == "answer.tool_calls"]
    assert len(tool_calls) == 1
    assert tool_calls[0]["calls"][0]["hits"] == []


def test_stream_answer_offtopic_refusal(client: TestClient) -> None:
    status, events = _answer_stream(client, question="今天天气怎么样？", page_key="resume")
    assert status == 200
    completed = dict(events[-1][1])
    assert completed["grounded"] is False
    assert completed["offtopic"] is True
    assert completed["model"] == "OFFTOPIC"
    delta_text = "".join(d["text"] for name, d in events if name == "answer.delta")
    assert OFFTOPIC_REPLY in delta_text


def test_stream_answer_greeting(client: TestClient) -> None:
    status, events = _answer_stream(client, question="你好", page_key="resume")
    assert status == 200
    completed = dict(events[-1][1])
    assert completed["offtopic"] is False
    assert completed["grounded"] is False
    delta_text = "".join(d["text"] for name, d in events if name == "answer.delta")
    assert GREETING_REPLY in delta_text


def test_stream_answer_project_scope(client: TestClient) -> None:
    status, events = _answer_stream(
        client, question="介绍下 jianli 的技术栈", page_key="projects", project_key="jianli"
    )
    assert status == 200
    completed = dict(events[-1][1])
    assert completed["grounded"] is True
    citations = next(d for name, d in events if name == "answer.citations")
    assert all(c["doc"] == "jianli" for c in citations["citations"])


def test_stream_answer_anonymous_conversation_id_rejected(client: TestClient) -> None:
    resp = client.post(
        "/answers:stream",
        json={"question": "你好", "page_key": "resume", "conversation_id": str(uuid4())},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTH_EXPIRED"


def test_stream_answer_invalid_cookie_401() -> None:
    class _FakeAuthService:
        def authenticate(self, token: str):  # type: ignore[no-untyped-def]
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Session expired")

    class _FakeRuntime:
        def __init__(self) -> None:
            self.service = _FakeAuthService()
            self.allowed_origins: frozenset[str] = frozenset()
            self.engine = None  # factory reads runtime.engine for aiqa persistence wiring

    app = create_app(Settings(), auth_runtime=_FakeRuntime())
    with TestClient(app) as invalid_client:
        invalid_client.cookies.set("__Host-session", "bogus-session-token-1234567890")
        resp = invalid_client.post(
            "/answers:stream", json={"question": "你好", "page_key": "resume"}
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == "AUTH_EXPIRED"


def test_stream_answer_validation_problem(client: TestClient) -> None:
    resp = client.post("/answers:stream", json={"question": ""})  # missing page_key, empty question
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "INVALID_REQUEST"
    assert "trace_id" in body
