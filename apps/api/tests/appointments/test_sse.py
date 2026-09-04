from __future__ import annotations

import asyncio
import contextlib
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import Request

from app.appointments.sse import stream_slot_events
from app.auth.errors import AuthError
from app.auth.models import Principal

# 复用同域已验证夹具与种子助手（单一来源，便于接手）
from .test_booking import (  # noqa: F401
    _authorized_client,
    _draft,
    _seed_slots,
    _seed_user,
    real_stack,
)

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


def _make_sse_request() -> Request:
    """Minimal ASGI scope so we can drive the SSE endpoint's StreamingResponse
    body generator directly (bypassing httpx's ASGITransport, which cannot stream
    an infinite SSE response — see below).

    NOTE: production SSE relies on ``request.is_disconnected()`` to stop polling when
    the real client disconnects. Under a test transport that signal never arrives, so
    we control the connection lifecycle explicitly via ``body_iterator.aclose()`` and
    stub ``is_disconnected`` to always report connected.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/slots/events",
        "headers": [],
        "query_string": b"",
        "scheme": "https",
    }
    request = Request(scope)

    # NOTE: ``request.is_disconnected()`` is async in Starlette (returns a coroutine).
    # Our stub must match that signature, otherwise ``await request.is_disconnected()``
    # in sse.py fails with ``TypeError: object bool can't be used in 'await' expression``.
    async def _always_connected() -> bool:
        return False

    request.is_disconnected = _always_connected  # type: ignore[method-assign]
    return request


async def _collect_stream(
    response, limit: int, timeout: float = 6.0, *, close: bool = True
) -> list[str]:
    """Iterate a StreamingResponse body, collecting SSE lines until ``limit`` event
    frames are seen or ``timeout`` elapses. Returns the raw lines.

    Uses the StreamingResponse ``body_iterator`` directly because httpx's
    ``ASGITransport`` (and starlette ``TestClient``) deadlock on an infinite SSE body:
    the generator's ``request.is_disconnected()`` blocks on ``receive()`` and the
    transport never sends a disconnect while the stream is open, so no frame is ever
    delivered to the consumer. Iterating the body generator bypasses the transport.
    """
    frames: list[str] = []
    try:
        async with asyncio.timeout(timeout):
            async for chunk in response.body_iterator:
                for line in chunk.splitlines():
                    frames.append(line)
                    if line.startswith("event: ") and sum(
                        1 for f in frames if f.startswith("event: ")
                    ) >= limit:
                        return frames
    except TimeoutError:
        pass
    finally:
        if close:
            with contextlib.suppress(Exception):
                await response.body_iterator.aclose()
    return frames


@pytest.mark.asyncio
async def test_sse_ready_frame_and_connection_cap(real_stack) -> None:
    engine, _, app, _ = real_stack
    booking_service = app.state.booking_runtime
    owner = _seed_user(engine)
    principal = Principal(
        id=owner, email=f"{owner}@example.invalid", role="interviewer", verified=True
    )
    request = _make_sse_request()

    # Two concurrent connections (kept open, mirroring real clients).
    first = stream_slot_events(booking_service, principal, request)
    second = stream_slot_events(booking_service, principal, request)
    try:
        frames_first = await _collect_stream(first, limit=1, close=False)
        assert any(f == "event: stream.ready" for f in frames_first), frames_first
        frames_second = await _collect_stream(second, limit=1, close=False)
        assert any(f == "event: stream.ready" for f in frames_second), frames_second

        # A third connection from the same account must be rejected (TC-SSE-005).
        third = stream_slot_events(booking_service, principal, request)
        with pytest.raises(AuthError):
            async for _ in third.body_iterator:
                pass
    finally:
        for conn in (first, second):
            with contextlib.suppress(Exception):
                await conn.body_iterator.aclose()


@pytest.mark.asyncio
async def test_sse_propagates_slot_change_without_pii(real_stack) -> None:
    engine, _, app, settings = real_stack
    booking_service = app.state.booking_runtime
    owner = _seed_user(engine)
    # Seed slots in the CURRENT week (mirrors test_slot_snapshot_is_authenticated_and_privacy_safe).
    # slot_snapshot only derives state for week_offset 0/1 relative to now(), so 2030-dated slots
    # would never appear in the SSE baseline and the slot.changed event would never fire.
    now = datetime.now(UTC)
    local_today = now.astimezone(ZoneInfo("Asia/Shanghai")).date()
    start = datetime.combine(
        local_today - timedelta(days=local_today.weekday()),
        datetime.min.time(),
        ZoneInfo("Asia/Shanghai"),
    ).astimezone(UTC) + timedelta(hours=3)
    slots = _seed_slots(engine, start)
    draft = _draft(slots)
    principal = Principal(
        id=owner, email=f"{owner}@example.invalid", role="interviewer", verified=True
    )
    request = _make_sse_request()

    async with _authorized_client(app, engine, settings, owner) as client:
        preview = await client.post("/appointment-confirmations", json=draft)
        assert preview.status_code == 200
        stream = stream_slot_events(booking_service, principal, request)

        # Drive the SSE body in a background task so the generator establishes its
        # baseline (available slots) BEFORE we create the appointment. The next poll
        # after creation must then emit slot.changed (architecture §5.1).
        collect_task = asyncio.create_task(_collect_stream(stream, limit=2, timeout=8.0))
        await asyncio.sleep(1.2)  # let the first poll seed the baseline
        response = await client.post(
            "/appointments",
            headers={"Idempotency-Key": str(uuid4())},
            json={"confirmation_token": preview.json()["confirmation_token"], "appointment": draft},
        )
        assert response.status_code == 201, response.status_code
        frames = await collect_task

    events = [f for f in frames if f.startswith("event: slot.changed")]
    assert events, frames
    # 事件不得泄露他人 PII（TC-SSE-004）
    payload = "\n".join(f for f in frames if f.startswith("data: "))
    assert "appointment_id" not in payload
    assert "company_name" not in payload
    assert "contact_phone" not in payload
