"""AI Answer SSE frames (docs/api/sse.md §3).

Frame grammar mirrors ``app/appointments/sse.py``: every frame carries ``id`` (stream_seq,
monotonic per connection), ``event`` and a single-line JSON ``data`` with the common fields
``stream_seq``/``emitted_at``/``trace_id``. Answer events, in order:

1. ``answer.started``   — ``answer_id`` + nullable ``conversation_id``
2. zero+ ``answer.delta`` — ``text``
3. ``answer.citations``  — knowledge sources (doc label + fragment, never a storage_key)
4. ``answer.completed``  — ``grounded``/``offtopic``/``model``/``usage``
5. on failure ``answer.error`` — the standard Problem body, then the stream closes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sse_frame(seq: int, event: str, data: dict[str, object]) -> str:
    payload = json.dumps(
        {**data, "stream_seq": seq, "emitted_at": _now_iso()},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return f"id: {seq}\nevent: {event}\ndata: {payload}\n\n"


def started_frame(
    seq: int, answer_id: str, conversation_id: str | None, trace_id: str
) -> str:
    return _sse_frame(
        seq,
        "answer.started",
        {"answer_id": answer_id, "conversation_id": conversation_id, "trace_id": trace_id},
    )


def delta_frame(seq: int, text: str, trace_id: str) -> str:
    return _sse_frame(seq, "answer.delta", {"text": text, "trace_id": trace_id})


def tool_calls_frame(
    seq: int,
    calls: list[dict[str, object]],
    trace_id: str,
) -> str:
    """Agent tooling (TASK-AGENT-TOOLS-001): visible decision chain.

    Each call: ``{"name", "query", "hits"}`` where hits is the citation summary
    (doc label + fragment, never a storage_key or full text). Frontend renders this
    as "已检索知识库 → 命中 N 个片段".
    """
    return _sse_frame(seq, "answer.tool_calls", {"calls": calls, "trace_id": trace_id})


def citations_frame(seq: int, citations: list[dict[str, object]], trace_id: str) -> str:
    return _sse_frame(seq, "answer.citations", {"citations": citations, "trace_id": trace_id})


def completed_frame(
    seq: int,
    *,
    grounded: bool,
    offtopic: bool,
    model: str,
    usage: dict[str, object] | None,
    trace_id: str,
) -> str:
    return _sse_frame(
        seq,
        "answer.completed",
        {
            "grounded": grounded,
            "offtopic": offtopic,
            "model": model,
            "usage": usage,
            "trace_id": trace_id,
        },
    )


def error_frame(seq: int, problem: dict[str, object], trace_id: str) -> str:
    return _sse_frame(seq, "answer.error", {**problem, "trace_id": trace_id})


# Agent autonomous booking (TASK-AIQA-BOOKING-001): surface the booking tool's
# structured outcome to the frontend so it can render a confirmation card. Four
# outcomes, each with a stable `type` URN for the client to switch on:
#   confirmed  -> 预约成功（卡片展示时间/公司/平台/联系人）
#   needs_info -> 信息不全，模型随后用自然语言追问
#   failed     -> 时段未开放/冲突/系统错误，模型道歉并建议
#   forbidden  -> 未登录或非面试官，模型引导登录
_BOOKING_OUTCOME_TYPES: dict[str, str] = {
    "confirmed": "urn:jianli:booking:confirmed",
    "needs_info": "urn:jianli:booking:needs_info",
    "failed": "urn:jianli:booking:failed",
    "forbidden": "urn:jianli:booking:forbidden",
    # Agent self-service outcomes (TASK-AIQA-AGENT-CRUD-001): cancel / reschedule.
    "cancelled": "urn:jianli:booking:cancelled",
    "rescheduled": "urn:jianli:booking:rescheduled",
    "not_found": "urn:jianli:booking:not_found",
    "terminal": "urn:jianli:booking:terminal",
    "conflict": "urn:jianli:booking:conflict",
}


def booking_frame(
    seq: int, outcome: str, payload: dict[str, object], trace_id: str
) -> str:
    return _sse_frame(
        seq,
        "answer.booking",
        {
            "outcome": outcome,
            "type": _BOOKING_OUTCOME_TYPES.get(outcome, outcome),
            "payload": payload,
            "trace_id": trace_id,
        },
    )
