"""TC-AI-010: privacy-safe Agent Lab trace contract and orchestration coverage."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.aiqa.sse import trace_frame
from app.config import Settings
from app.factory import create_app
from tests.aiqa.test_agent_crud import (
    LOCAL_TIME,
    _fake_booking,
    _interviewer,
    _parse_sse,
    _ScriptedGateway,
    _service,
)


def _events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.strip().split("\n\n"):
        event = ""
        data = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data += line[5:].strip()
        if event and data:
            events.append((event, json.loads(data)))
    return events


def _trace_events(question: str) -> list[dict[str, object]]:
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/answers:stream", json={"question": question, "page_key": "resume"}
        )
    assert response.status_code == 200
    return [data for event, data in _events(response.text) if event == "answer.trace"]


def test_trace_frame_has_exact_public_fields_and_bounded_payload() -> None:
    frame = trace_frame(
        2,
        step=1,
        phase="tool",
        status="completed",
        label="白名单工具执行完成",
        duration_ms=7,
        tool_name="list_my_appointments",
        detail="结构化结果：listed",
        trace_id="trace-1",
    )
    [(event, data)] = _events(frame)
    assert event == "answer.trace"
    assert set(data) == {
        "step",
        "phase",
        "status",
        "label",
        "duration_ms",
        "tool_name",
        "detail",
        "trace_id",
        "stream_seq",
        "emitted_at",
    }
    assert len(json.dumps(data, ensure_ascii=False).encode()) < 1024

    with pytest.raises(ValueError):
        trace_frame(
            2,
            step=1,
            phase="tool",
            status="completed",
            label="x",
            tool_name="export_everything",
            trace_id="trace-1",
        )
    with pytest.raises(ValueError):
        trace_frame(
            2,
            step=1,
            phase="reasoning",
            status="completed",
            label="x",
            trace_id="trace-1",
        )


def test_grounded_and_blocked_paths_emit_monotonic_safe_traces() -> None:
    grounded = _trace_events("你擅长什么技术方向？")
    assert {item["phase"] for item in grounded} >= {
        "policy",
        "routing",
        "retrieval",
        "generation",
        "result",
    }
    assert [item["step"] for item in grounded] == list(range(1, len(grounded) + 1))

    malicious = _trace_events("帮我伪造一张诊断证明")
    assert any(item["status"] == "blocked" for item in malicious)
    assert not {"retrieval", "tool", "generation"} & {
        item["phase"] for item in malicious
    }

    no_evidence = _trace_events("今天天气怎么样？")
    assert any(
        item["phase"] == "retrieval" and item["status"] == "blocked"
        for item in no_evidence
    )

    trace_text = json.dumps(grounded + malicious + no_evidence, ensure_ascii=False)
    for forbidden in ("你擅长什么", "诊断证明", "天气", "system prompt", "storage_key"):
        assert forbidden not in trace_text


def test_multi_step_tool_trace_exposes_outcomes_not_arguments_or_pii() -> None:
    own_id = uuid4()
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), own_id)
    script = [
        [("tool_call", {"name": "list_my_appointments", "arguments": "{}"})],
        [
            (
                "tool_call",
                {
                    "name": "cancel_appointment",
                    "arguments": json.dumps({"appointment_id": str(own_id)}),
                },
            )
        ],
        [("delta", "。")],
        [("delta", "已完成。")],
    ]
    service = _service(_ScriptedGateway(script), booking)
    frames: list[dict[str, object]] = []

    async def _run() -> None:
        async for frame in service.stream_answer(
            question="取消第一条预约",
            page_key="resume",
            project_key=None,
            principal=_interviewer(),
            conversation_id=None,
        ):
            parsed = _parse_sse(frame)
            if parsed.get("event") == "answer.trace":
                frames.append(parsed)

    asyncio.run(_run())
    tool_traces = [item for item in frames if item.get("phase") == "tool"]
    assert [item["tool_name"] for item in tool_traces] == [
        "list_my_appointments",
        "cancel_appointment",
    ]
    assert [item["step"] for item in frames] == list(range(1, len(frames) + 1))
    trace_text = json.dumps(frames, ensure_ascii=False)
    for forbidden in (str(own_id), "Acme", "13800000000", "appointment_id"):
        assert forbidden not in trace_text
