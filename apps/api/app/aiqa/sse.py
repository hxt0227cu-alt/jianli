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
