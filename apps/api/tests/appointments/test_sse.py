from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

# 复用同域已验证夹具与种子助手（单一来源，便于接手）
from .test_booking import (  # noqa: F401
    real_stack,
    _seed_user,
    _seed_slots,
    _authorized_client,
    _draft,
)


async def _collect_frames(stream, limit: int, timeout: float = 4.0) -> list[str]:
    """Read SSE lines until `limit` event frames seen or timeout; return raw lines."""
    frames: list[str] = []
    try:
        async with asyncio.timeout(timeout):
            async for line in stream.aiter_lines():
                frames.append(line)
                if line.startswith("event: ") and sum(
                    1 for f in frames if f.startswith("event: ")
                ) >= limit:
                    break
    except asyncio.TimeoutError:
        pass
    return frames


@pytest.mark.asyncio
async def test_sse_ready_frame_and_connection_cap(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    async with _authorized_client(app, engine, settings, owner) as client:
        async with client.stream("GET", "/slots/events") as first, client.stream(
            "GET", "/slots/events"
        ) as second:
            assert first.status_code == 200
            assert second.status_code == 200
            frames = await _collect_frames(first, limit=1)
            assert any(f == "event: stream.ready" for f in frames), frames
            # 同账号第 3 条连接必须被拒绝（TC-SSE-005）
            third = await client.get("/slots/events")
            assert third.status_code == 429


@pytest.mark.asyncio
async def test_sse_propagates_slot_change_without_pii(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine)
    start = datetime(2030, 6, 3, 3, 0, tzinfo=UTC)
    slots = _seed_slots(engine, start)
    draft = _draft(slots)
    async with _authorized_client(app, engine, settings, owner) as client:
        preview = await client.post("/appointment-confirmations", json=draft)
        assert preview.status_code == 200
        async with client.stream("GET", "/slots/events") as stream:
            response = await client.post(
                "/appointments",
                headers={"Idempotency-Key": str(uuid4())},
                json={"confirmation_token": preview.json()["confirmation_token"], "appointment": draft},
            )
            assert response.status_code == 201, response.status_code
            frames = await _collect_frames(stream, limit=2, timeout=4.0)
            events = [f for f in frames if f.startswith("event: slot.changed")]
            assert events, frames
            # 事件不得泄露他人 PII（TC-SSE-004）
            payload = "\n".join(f for f in frames if f.startswith("data: "))
            assert "appointment_id" not in payload
            assert "company_name" not in payload
            assert "contact_phone" not in payload
