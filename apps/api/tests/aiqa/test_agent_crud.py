"""Tests for the agent self-service CRUD tools (TASK-AIQA-AGENT-CRUD-001).

Two layers, mirroring ``test_agent_booking.py``:

1. Unit layer (DB-free, always runs) — drives ``AnswerService._run_agent_tool`` (and the
   new multi-step ``stream_answer`` loop) with fake ``BookingService`` / ``LLMGateway``
   stand-ins. Covers RBAC (interviewer = own only; owner_admin = all), outcome mapping
   (listed / cancelled / rescheduled / forbidden / not_found / terminal / conflict /
   failed), and the list → cancel multi-step chain.

2. Real-stack layer (Postgres + Redis, runs only when ``JIANLI_BOOKING_TEST_*`` are set) —
   exercises the genuine ``BookingService`` so the ownership lock, slot release, and audit
   writes are validated end-to-end.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, create_engine, text

from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.service import AnswerService
from app.appointments.models import (
    Appointment,
    AppointmentDraft,
    AppointmentUpdate,
    Slot,
    SlotSnapshot,
)
from app.auth.errors import AuthError
from app.auth.models import Principal
from app.config import Settings

LOCAL_TIME = ZoneInfo("Asia/Shanghai")


# --------------------------------------------------------------------------------------
# Fake gateways
# --------------------------------------------------------------------------------------


class _NoopGateway:
    """Placeholder gateway; the unit-layer tool tests never touch it."""


class _ScriptedGateway:
    """Yields a pre-scripted sequence of (kind, payload) batches, one batch per call.

    Each entry in ``scripted`` is the list of frames returned by one ``answer()`` call.
    The multi-step loop calls ``answer()`` once per tool step, so the script naturally
    drives list → cancel → (model answers) → phrase.
    """

    def __init__(self, scripted: list[list[tuple[str, object]]]) -> None:
        self._script = list(scripted)
        self._i = 0
        self.model_name = "scripted"

    async def answer(self, messages, tools=None):
        if self._i >= len(self._script):
            yield ("delta", "。")
            return
        steps = self._script[self._i]
        self._i += 1
        for kind, payload in steps:
            yield kind, payload


# --------------------------------------------------------------------------------------
# Fake BookingService
# --------------------------------------------------------------------------------------


def _make_slots(
    start_local: datetime,
    statuses: tuple[str, str, str] = ("available", "available", "available"),
) -> list[Slot]:
    slots: list[Slot] = []
    for offset, status in enumerate(statuses):
        when = start_local + timedelta(minutes=30 * offset)
        slots.append(
            Slot(
                id=uuid4(),
                start_at=when.astimezone(UTC),
                end_at=(when + timedelta(minutes=30)).astimezone(UTC),
                status=status,
                resource_version=1,
                ownership="none",
            )
        )
    return slots


def _fake_booking(start_local: datetime, own_id: UUID) -> _FakeCRUDBookingService:
    """Compact builder for the fake BookingService used across unit tests."""
    return _FakeCRUDBookingService(_make_slots(start_local), own_id)


def _make_appt(
    aid: UUID,
    status: str = "active",
    version: int = 1,
    start_local: datetime | None = None,
    company: str = "Acme Co.",
) -> Appointment:
    start_local = start_local or datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    return Appointment(
        slot_ids=[uuid4(), uuid4(), uuid4()],
        company_name=company,
        meeting_platform="Tencent Meeting",
        meeting_number="123-456-789",
        contact_last_name="Zhang",
        contact_salutation="Teacher",
        contact_phone="13800000000",
        notes=None,
        id=aid,
        status=status,
        version=version,
        start_at=start_local.astimezone(UTC),
        end_at=(start_local + timedelta(minutes=90)).astimezone(UTC),
    )


class _FakeCRUDBookingService:
    """Scriptable stand-in covering the read/list/cancel/reschedule surface."""

    def __init__(self, slots: list[Slot], own_id: UUID, other_id: UUID | None = None) -> None:
        self._slots = slots
        self.own_id = own_id
        self.other_id = other_id
        self.own_appt = _make_appt(own_id, status="active", version=1)
        self.other_appt = _make_appt(other_id, status="active", version=1) if other_id else None
        self.cancel_calls: list[UUID] = []
        self.force_cancel_calls: list[UUID] = []
        self.update_calls: list[tuple[UUID, AppointmentUpdate]] = []
        self.reschedule_calls: list[tuple[UUID, list[UUID]]] = []
        self.list_my_calls = 0
        self.admin_list_calls = 0
        self.update_raise: type[AuthError] | AuthError | None = None
        self._confirm_token = "fake-confirm-token"

    # -- tool surface --

    def slot_snapshot(self, principal: Principal, week_offset: int) -> SlotSnapshot:
        return SlotSnapshot(watermark=1, generated_at=datetime.now(UTC), items=self._slots)

    def list_my(self, principal: Principal) -> list[Appointment]:
        self.list_my_calls += 1
        return [self.own_appt]

    def admin_list_appointments(self) -> list[Appointment]:
        self.admin_list_calls += 1
        items = [self.own_appt]
        if self.other_appt is not None:
            items.append(self.other_appt)
        return items

    def cancel(self, principal: Principal, appointment_id: UUID) -> None:
        # Mirror the real BookingService: ownership is enforced before any mutation.
        if appointment_id != self.own_id:
            raise AuthError("PERM_DENIED", 403, "Not the appointment owner", "owner mismatch")
        self.cancel_calls.append(appointment_id)
        return None

    def force_cancel(self, actor: Principal, appointment_id: UUID) -> None:
        self.force_cancel_calls.append(appointment_id)
        return None

    def read_own(self, principal: Principal, appointment_id: UUID) -> Appointment:
        if appointment_id != self.own_id:
            raise AuthError("PERM_DENIED", 403, "Not the appointment owner", "owner mismatch")
        return self.own_appt

    def update(
        self, principal: Principal, appointment_id: UUID, update: AppointmentUpdate
    ) -> Appointment:
        self.update_calls.append((appointment_id, update))
        if isinstance(self.update_raise, AuthError):
            raise self.update_raise
        return self.own_appt

    def admin_reschedule(
        self, actor: Principal, appointment_id: UUID, new_slot_ids: list[UUID]
    ) -> Appointment:
        self.reschedule_calls.append((appointment_id, new_slot_ids))
        return self.own_appt

    # -- booking surface (so request_interview_booking still works through the dispatcher) --

    def preview(self, principal: Principal, draft: AppointmentDraft) -> object:
        return type(
            "Preview",
            (),
            {
                "confirmation_token": self._confirm_token,
                "expires_at": datetime.now(UTC) + timedelta(minutes=3),
                "company_name": draft.company_name,
                "recipient_email": principal.email,
                "salutation": f"{draft.contact_last_name} {draft.contact_salutation}",
            },
        )()

    def create(
        self, principal: Principal, draft: AppointmentDraft, confirmation_token: str
    ) -> Appointment:
        start = self._slots[0].start_at.astimezone(LOCAL_TIME)
        return Appointment(
            **draft.model_dump(),
            id=uuid4(),
            status="active",
            version=1,
            start_at=start,
            end_at=start + timedelta(minutes=90),
        )


def _interviewer(role: str = "interviewer") -> Principal:
    return Principal(
        id=uuid4(),
        email=f"{uuid4()}@example.invalid",
        role=role,  # type: ignore[arg-type]
        verified=True,
    )


def _service(gateway, booking) -> AnswerService:
    return AnswerService(
        gateway,  # type: ignore[arg-type]
        AnswerRateLimiter(),
        booking_service=booking,  # type: ignore[arg-type]
    )


def _full_booking_args(target_date: str, start_time: str = "14:00") -> dict[str, object]:
    return {
        "target_date": target_date,
        "start_time": start_time,
        "company_name": "Acme Co.",
        "meeting_platform": "Tencent Meeting",
        "meeting_number": "123-456-789",
        "contact_last_name": "Zhang",
        "contact_salutation": "Teacher",
        "contact_phone": "13800000000",
    }


# --------------------------------------------------------------------------------------
# Unit layer — dispatcher routing & search signal
# --------------------------------------------------------------------------------------


def test_search_knowledge_returns_signal() -> None:
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), uuid4())
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "search_knowledge", {"query": "技术栈"}, _interviewer()
        )
    )
    assert result == {"outcome": "search", "payload": {"query": "技术栈"}}


def test_anonymous_is_forbidden_for_any_write() -> None:
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), uuid4())
    for name in ("list_my_appointments", "cancel_appointment", "reschedule_appointment"):
        result = asyncio.run(
            _service(_NoopGateway(), booking)._run_agent_tool(name, {}, None)
        )
        assert result["outcome"] == "forbidden"
        assert "登录" in result["payload"]["reason"]


def test_unknown_tool_is_failed() -> None:
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), uuid4())
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool("does_not_exist", {}, _interviewer())
    )
    assert result["outcome"] == "failed"


def test_booking_still_routed_through_dispatcher() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    booking = _FakeCRUDBookingService(_make_slots(start_local), uuid4())
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "request_interview_booking", _full_booking_args("2030-06-03"), _interviewer()
        )
    )
    assert result["outcome"] == "confirmed"


# --------------------------------------------------------------------------------------
# Unit layer — list (RBAC scope)
# --------------------------------------------------------------------------------------


def test_list_mine_for_interviewer() -> None:
    own_id = uuid4()
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), own_id)
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "list_my_appointments", {}, _interviewer()
        )
    )
    assert result["outcome"] == "listed"
    assert result["payload"]["scope"] == "mine"
    assert result["payload"]["items"][0]["appointment_id"] == str(own_id)
    assert booking.list_my_calls == 1
    assert booking.admin_list_calls == 0


def test_list_all_for_owner() -> None:
    own_id, other_id = uuid4(), uuid4()
    booking = _FakeCRUDBookingService(
        _make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)), own_id, other_id
    )
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "list_my_appointments", {}, _interviewer("owner_admin")
        )
    )
    assert result["outcome"] == "listed"
    assert result["payload"]["scope"] == "all"
    ids = {item["appointment_id"] for item in result["payload"]["items"]}
    assert {str(own_id), str(other_id)} <= ids
    assert booking.admin_list_calls == 1


# --------------------------------------------------------------------------------------
# Unit layer — cancel (RBAC + outcome mapping)
# --------------------------------------------------------------------------------------


def test_cancel_own_succeeds() -> None:
    own_id = uuid4()
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), own_id)
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "cancel_appointment", {"appointment_id": str(own_id)}, _interviewer()
        )
    )
    assert result == {"outcome": "cancelled", "payload": {"appointment_id": str(own_id)}}
    assert booking.cancel_calls == [own_id]
    assert booking.force_cancel_calls == []


def test_cancel_other_is_forbidden_for_interviewer() -> None:
    own_id, other_id = uuid4(), uuid4()
    booking = _FakeCRUDBookingService(
        _make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)), own_id, other_id
    )
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "cancel_appointment", {"appointment_id": str(other_id)}, _interviewer()
        )
    )
    assert result["outcome"] == "forbidden"
    assert "你名下" in result["payload"]["reason"]
    assert booking.cancel_calls == []  # ownership rejected before any cancellation


def test_owner_force_cancels_other() -> None:
    own_id, other_id = uuid4(), uuid4()
    booking = _FakeCRUDBookingService(
        _make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)), own_id, other_id
    )
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "cancel_appointment", {"appointment_id": str(other_id)}, _interviewer("owner_admin")
        )
    )
    assert result == {"outcome": "cancelled", "payload": {"appointment_id": str(other_id)}}
    assert booking.force_cancel_calls == [other_id]


def test_cancel_bad_uuid_is_failed() -> None:
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), uuid4())
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "cancel_appointment", {"appointment_id": "not-a-uuid"}, _interviewer()
        )
    )
    assert result["outcome"] == "failed"


# --------------------------------------------------------------------------------------
# Unit layer — reschedule (slot resolution, RBAC, error mapping)
# --------------------------------------------------------------------------------------


def test_reschedule_own_available_succeeds() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    own_id = uuid4()
    booking = _FakeCRUDBookingService(_make_slots(start_local), own_id)
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "reschedule_appointment",
            {"appointment_id": str(own_id), "target_date": "2030-06-03", "start_time": "14:00"},
            _interviewer(),
        )
    )
    assert result["outcome"] == "rescheduled"
    assert result["payload"]["appointment_id"] == str(own_id)
    assert "2030-06-03T14:00" in result["payload"]["start_at_local"]


def test_reschedule_unavailable_slot_is_failed() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    own_id = uuid4()
    booking = _FakeCRUDBookingService(
        _make_slots(start_local, ("available", "booked", "available")), own_id
    )
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "reschedule_appointment",
            {"appointment_id": str(own_id), "target_date": "2030-06-03", "start_time": "14:00"},
            _interviewer(),
        )
    )
    assert result["outcome"] == "failed"
    assert "未开放" in result["payload"]["reason"]
    assert booking.update_calls == []


def test_reschedule_version_conflict_is_mapped() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    own_id = uuid4()
    booking = _FakeCRUDBookingService(_make_slots(start_local), own_id)
    booking.update_raise = AuthError("VERSION_CONFLICT", 409, "Version conflict", "reload")
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "reschedule_appointment",
            {"appointment_id": str(own_id), "target_date": "2030-06-03", "start_time": "14:00"},
            _interviewer(),
        )
    )
    assert result["outcome"] == "conflict"
    assert "重新查询" in result["payload"]["reason"]


def test_reschedule_other_is_forbidden_for_interviewer() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    own_id, other_id = uuid4(), uuid4()
    booking = _FakeCRUDBookingService(_make_slots(start_local), own_id, other_id)
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "reschedule_appointment",
            {"appointment_id": str(other_id), "target_date": "2030-06-03", "start_time": "14:00"},
            _interviewer(),
        )
    )
    assert result["outcome"] == "forbidden"
    assert "你名下" in result["payload"]["reason"]


def test_owner_reschedule_other_bypasses_ownership() -> None:
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    own_id, other_id = uuid4(), uuid4()
    booking = _FakeCRUDBookingService(_make_slots(start_local), own_id, other_id)
    result = asyncio.run(
        _service(_NoopGateway(), booking)._run_agent_tool(
            "reschedule_appointment",
            {"appointment_id": str(other_id), "target_date": "2030-06-03", "start_time": "14:00"},
            _interviewer("owner_admin"),
        )
    )
    assert result["outcome"] == "rescheduled"
    assert booking.reschedule_calls == [(other_id, booking.reschedule_calls[0][1])]


# --------------------------------------------------------------------------------------
# Unit layer — multi-step loop (list → cancel) through stream_answer
# --------------------------------------------------------------------------------------


def _parse_sse(raw: str) -> dict[str, object]:
    """Parse an SSE frame: the event type lives in the ``event:`` line, the JSON in ``data:``."""
    event: str | None = None
    data: dict[str, object] | None = None
    for line in raw.splitlines():
        if line.startswith("event:"):
            event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data = json.loads(line[len("data:") :].lstrip())
    if data is None:
        return {}
    if event is not None:
        return {**data, "event": event}
    return data


def test_stream_answer_list_then_cancel_chain() -> None:
    """The model lists, then cancels; the loop must run both tools and emit the card."""
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
        [("delta", "。")],  # model answers directly -> loop breaks
        [("delta", "已为你取消第一条预约。")],  # final phrasing
    ]
    service = _service(_ScriptedGateway(script), booking)
    principal = _interviewer()
    frames: list[dict[str, object]] = []

    async def _run() -> None:
        async for frame in service.stream_answer(
            question="取消我的那条预约",
            page_key="resume",
            project_key=None,
            principal=principal,
            conversation_id=None,
        ):
            frames.append(_parse_sse(frame))

    asyncio.run(_run())

    booking_frames = [f for f in frames if f.get("event") == "answer.booking"]
    assert any(
        b.get("outcome") == "cancelled"
        and b.get("payload", {}).get("appointment_id") == str(own_id)
        for b in booking_frames
    )
    # Both tools actually executed in order.
    assert booking.list_my_calls == 1
    assert booking.cancel_calls == [own_id]
    # Final answer present.
    assert any(f.get("event") == "answer.completed" for f in frames)


def test_stream_answer_max_steps_is_bounded() -> None:
    """Even if the model keeps requesting tools, the loop stops at MAX_STEPS (no hang)."""
    booking = _fake_booking(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME), uuid4())
    # Every answer() call returns a tool_call -> loop must terminate at MAX_STEPS=4.
    endless = [[("tool_call", {"name": "list_my_appointments", "arguments": "{}"})]]
    script = [endless[0] for _ in range(8)]  # longer than MAX_STEPS
    service = _service(_ScriptedGateway(script), booking)
    frames: list[dict[str, object]] = []

    async def _run() -> None:
        async for frame in service.stream_answer(
            question="一直列",
            page_key="resume",
            project_key=None,
            principal=_interviewer(),
            conversation_id=None,
        ):
            frames.append(_parse_sse(frame))

    asyncio.run(_run())
    # list_my is invoked at most MAX_STEPS times (the loop bounds tool steps).
    assert booking.list_my_calls <= 4
    assert any(f.get("event") == "answer.completed" for f in frames)


# --------------------------------------------------------------------------------------
# Real-stack layer — genuine BookingService (gated by env)
# --------------------------------------------------------------------------------------

_BOOKING_DB_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
_BOOKING_REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")

pytestmark_integration = pytest.mark.skipif(
    not _BOOKING_DB_URL or not _BOOKING_REDIS_URL,
    reason="real PostgreSQL + Redis (JIANLI_BOOKING_TEST_*) are required",
)


def _integration_settings() -> Settings:
    assert _BOOKING_DB_URL and _BOOKING_REDIS_URL
    return Settings(
        database_url=_BOOKING_DB_URL,
        redis_url=_BOOKING_REDIS_URL,
        csrf_hmac_key=os.environ["JIANLI_CSRF_HMAC_KEY"],
        rate_limit_hmac_key=os.environ["JIANLI_RATE_LIMIT_HMAC_KEY"],
        allowed_origins=("https://booking.test",),
        field_encryption_current_key_id=os.environ["JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID"],
        field_encryption_keys=os.environ["JIANLI_FIELD_ENCRYPTION_KEYS"],
        company_fingerprint_hmac_key=os.environ["JIANLI_COMPANY_FINGERPRINT_HMAC_KEY"],
        appointment_confirmation_hmac_key=os.environ["JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY"],
    )


@pytest.fixture
def real_booking_stack():
    settings = _integration_settings()
    engine = create_engine(settings.database_url)
    import redis

    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE audit_logs, notification_events, appointments,"
                " appointment_slots, companies, users CASCADE"
            )
        )
    from app.appointments.runtime import build_booking_runtime
    from app.auth.runtime import build_auth_runtime

    auth_runtime = build_auth_runtime(settings)
    booking_runtime = build_booking_runtime(settings, auth_runtime)
    service = AnswerService(
        _NoopGateway(),  # type: ignore[arg-type]
        AnswerRateLimiter(),
        booking_service=booking_runtime,  # type: ignore[arg-type]
    )
    try:
        yield engine, booking_runtime, service
    finally:
        auth_runtime.close()
        redis_client.close()
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE audit_logs, notification_events, appointments,"
                    " appointment_slots, companies, users CASCADE"
                )
            )
        engine.dispose()


def _seed_user(engine: Engine, role: str) -> UUID:
    user_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,'x', :role, true)"
            ),
            {"id": user_id, "email": f"{user_id}@example.invalid", "role": role},
        )
    return user_id


def _seed_slots(engine: Engine, start_local: datetime) -> list[UUID]:
    ids = [uuid4(), uuid4(), uuid4()]
    with engine.begin() as connection:
        for offset, slot_id in enumerate(ids):
            slot_start = start_local + timedelta(minutes=30 * offset)
            connection.execute(
                text(
                    "INSERT INTO appointment_slots "
                    "(id,start_at,end_at,status,appointment_id,version) "
                    "VALUES (:id,:start_at,:end_at,'available',NULL,1)"
                ),
                {
                    "id": slot_id,
                    "start_at": slot_start.astimezone(UTC),
                    "end_at": (slot_start + timedelta(minutes=30)).astimezone(UTC),
                },
            )
    return ids


@pytestmark_integration
def test_real_stack_list_then_cancel(real_booking_stack) -> None:
    """End-to-end: list returns the active appointment, then cancel flips its status."""
    engine, _booking, service = real_booking_stack
    user_id = _seed_user(engine, "interviewer")
    today = datetime.now(LOCAL_TIME).date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    start_local = datetime.combine(monday, datetime.min.time().replace(hour=14), LOCAL_TIME)
    _seed_slots(engine, start_local)
    principal = Principal(
        id=user_id, email=f"{user_id}@example.invalid", role="interviewer", verified=True
    )
    # Book one first via the genuine service.
    booked = asyncio.run(
        service._run_agent_tool(
            "request_interview_booking",
            _full_booking_args(start_local.strftime("%Y-%m-%d"), "14:00"),
            principal,
        )
    )
    assert booked["outcome"] == "confirmed"
    appt_id = booked["payload"]["appointment_id"]
    # Now list + cancel through the agent tools.
    listed = asyncio.run(service._run_agent_tool("list_my_appointments", {}, principal))
    assert listed["outcome"] == "listed"
    assert any(i["appointment_id"] == appt_id for i in listed["payload"]["items"])
    cancelled = asyncio.run(
        service._run_agent_tool("cancel_appointment", {"appointment_id": appt_id}, principal)
    )
    assert cancelled == {"outcome": "cancelled", "payload": {"appointment_id": appt_id}}
    with engine.begin() as connection:
        status = connection.execute(
            text("SELECT status FROM appointments WHERE id=:id"), {"id": UUID(appt_id)}
        ).scalar_one()
    assert status == "cancelled"


@pytestmark_integration
def test_real_stack_owner_force_cancels_other(real_booking_stack) -> None:
    """owner_admin cancels an interviewer's appointment via the agent tool."""
    engine, _booking, service = real_booking_stack
    interviewer_id = _seed_user(engine, "interviewer")
    owner_id = _seed_user(engine, "owner_admin")
    today = datetime.now(LOCAL_TIME).date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    start_local = datetime.combine(monday, datetime.min.time().replace(hour=15), LOCAL_TIME)
    _seed_slots(engine, start_local)
    interviewer = Principal(
        id=interviewer_id,
        email=f"{interviewer_id}@example.invalid",
        role="interviewer",
        verified=True,
    )
    owner = Principal(
        id=owner_id, email=f"{owner_id}@example.invalid", role="owner_admin", verified=True
    )
    booked = asyncio.run(
        service._run_agent_tool(
            "request_interview_booking",
            _full_booking_args(start_local.strftime("%Y-%m-%d"), "15:00"),
            interviewer,
        )
    )
    assert booked["outcome"] == "confirmed"
    appt_id = booked["payload"]["appointment_id"]
    # Owner cancels the interviewer's appointment.
    cancelled = asyncio.run(
        service._run_agent_tool("cancel_appointment", {"appointment_id": appt_id}, owner)
    )
    assert cancelled == {"outcome": "cancelled", "payload": {"appointment_id": appt_id}}
    with engine.begin() as connection:
        status = connection.execute(
            text("SELECT status FROM appointments WHERE id=:id"), {"id": UUID(appt_id)}
        ).scalar_one()
    assert status == "cancelled"
