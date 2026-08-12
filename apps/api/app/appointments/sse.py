"""Slot SSE event stream (sse.md v0.1, architecture §5).

Derives slot changes from committed PostgreSQL state by polling the existing
``slot_snapshot`` read path every ``POLL_INTERVAL`` seconds (per-connection, no
message middleware — architecture §5.1). Emits self-contained ``slot.changed``
frames carrying only the visible state (``ownership`` ∈ none/self/other); it never
includes ``appointment_id``, company, meeting number, contact or notes (TC-SSE-004).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.auth.models import Principal

from .models import Slot
from .service import BookingService

_POLL_INTERVAL = 1.0
_HEARTBEAT_INTERVAL = 15.0


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sse_frame(seq: int, event: str, data: dict) -> str:
    payload = json.dumps({**data, "stream_seq": seq}, separators=(",", ":"), ensure_ascii=False)
    return f"id: {seq}\nevent: {event}\ndata: {payload}\n\n"


def _slot_payload(slot: Slot) -> dict:
    return {
        "emitted_at": _now_iso(),
        "slot": {
            "id": str(slot.id),
            "start_at": slot.start_at.isoformat(),
            "end_at": slot.end_at.isoformat(),
            "status": slot.status,
            "resource_version": slot.resource_version,
            "ownership": slot.ownership,
        },
    }


async def _event_stream(
    service: BookingService, principal: Principal, request: Request
) -> AsyncIterator[str]:
    service.sse_registry.acquire(principal.id)
    try:
        seq = 0
        last: dict[object, tuple[str, int]] = {}
        # C1: ready frame (stream_seq=0); client pulls snapshot, then replays buffer (§5.3).
        yield _sse_frame(0, "stream.ready", {"watermark": 0, "emitted_at": _now_iso()})
        last_heartbeat = time.monotonic()
        while True:
            if await request.is_disconnected():
                return
            slots: list[Slot] = []
            for week in (0, 1):
                snapshot = await asyncio.to_thread(service.slot_snapshot, principal, week)
                slots.extend(snapshot.items)
            for slot in slots:
                key = (slot.status, slot.resource_version)
                previous = last.get(slot.id)
                if previous is None:
                    # Initial baseline; client reconciles via the snapshot it pulls on connect.
                    last[slot.id] = key
                    continue
                if previous != key:
                    seq += 1
                    last[slot.id] = key
                    yield _sse_frame(seq, "slot.changed", _slot_payload(slot))
            now = time.monotonic()
            if now - last_heartbeat >= _HEARTBEAT_INTERVAL:
                seq += 1
                last_heartbeat = now
                yield _sse_frame(seq, "heartbeat", {"emitted_at": _now_iso()})
            await asyncio.sleep(_POLL_INTERVAL)
    finally:
        service.sse_registry.release(principal.id)


def stream_slot_events(
    service: BookingService, principal: Principal, request: Request
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(service, principal, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
