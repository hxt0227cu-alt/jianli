"""Tests for the autonomous interview-booking agent tool (TASK-AIQA-BOOKING-001).

Two layers:

1. Unit layer (DB-free, always runs) — drives ``AnswerService._run_booking_tool`` with a
   fake ``BookingService`` (no Postgres/Redis). This isolates the *agent-side* decision
   logic that the appointments domain does NOT cover: RBAC, natural-language slot parsing,
   business-field completeness, and outcome mapping (confirmed / needs_info / failed /
   forbidden). The fake's ``slot_snapshot`` ignores ``week_offset`` and simply returns the
   slots it holds, so ``_resolve_booking_slots`` is exercised purely on local-start times.

2. Real-stack layer (Postgres + Redis, runs only when ``JIANLI_BOOKING_TEST_DATABASE_URL``
   and ``JIANLI_BOOKING_TEST_REDIS_URL`` are set — mirrors ``tests/appointments/test_booking.py``)
   — drives the same method against the genuine ``BookingService`` so the strong invariants
   (preview→create two-phase token, row lock, company fingerprint dedupe, notification
   events) and the end-to-end slot-consumption path are validated.

The agent tool only parses *explicit* ``target_date`` (YYYY-MM-DD) / ``start_time`` (HH:MM)
— converting "下周三" to a date is the model's job (design D1=A). Tests therefore pass
explicit dates, matching the tool's actual contract.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import IntegrityError

from app.aiqa.rate_limit import AnswerRateLimiter
from app.aiqa.service import AnswerService
from app.appointments.models import Appointment, AppointmentDraft, Slot, SlotSnapshot
from app.appointments.runtime import build_booking_runtime
from app.auth.errors import AuthError
from app.auth.models import Principal
from app.auth.runtime import build_auth_runtime
from app.config import Settings

LOCAL_TIME = ZoneInfo("Asia/Shanghai")


# --------------------------------------------------------------------------------------
# Fake BookingService (unit layer)
# --------------------------------------------------------------------------------------


class _NoopGateway:
    """Minimal gateway placeholder; ``_run_booking_tool`` never touches it."""


class _FakeBookingService:
    """Stand-in for ``BookingService`` with deterministic, scriptable behaviour.

    ``slot_snapshot`` ignores ``week_offset`` and returns whatever slots the test loaded,
    so slot *resolution* (the 3-consecutive-available filter) is exercised without a DB.
    ``preview`` returns a canned token; ``create`` returns a canned ``Appointment`` unless
    ``raise_on_create`` is set, letting a single method cover every outcome branch.
    """

    def __init__(self, slots: list[Slot]) -> None:
        self._slots = slots
        self.preview_calls: list[AppointmentDraft] = []
        self.created_draft: AppointmentDraft | None = None
        self.raise_on_create: type[Exception] | None = None
        self._confirm_token = "fake-confirm-token"

    def slot_snapshot(self, principal: Principal, week_offset: int) -> SlotSnapshot:
        return SlotSnapshot(
            watermark=1,
            generated_at=datetime.now(UTC),
            items=self._slots,
        )

    def preview(self, principal: Principal, draft: AppointmentDraft) -> object:
        self.preview_calls.append(draft)
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
        if self.raise_on_create is not None:
            raise self.raise_on_create
        self.created_draft = draft
        start = self._slots[0].start_at.astimezone(LOCAL_TIME)
        return Appointment(
            **draft.model_dump(),
            id=uuid4(),
            status="active",
            version=1,
            start_at=start,
            end_at=start + timedelta(minutes=90),
        )


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


def _interviewer(role: str = "interviewer") -> Principal:
    return Principal(
        id=uuid4(),
        email=f"{uuid4()}@example.invalid",
        role=role,  # type: ignore[arg-type]
        verified=True,
    )


def _service(booking: _FakeBookingService) -> AnswerService:
    return AnswerService(
        _NoopGateway(),  # type: ignore[arg-type]
        AnswerRateLimiter(),
        booking_service=booking,  # type: ignore[arg-type]
    )


def _full_args(target_date: str, start_time: str = "14:00") -> dict[str, object]:
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
# Unit layer — RBAC
# --------------------------------------------------------------------------------------


def test_rbac_anonymous_is_forbidden() -> None:
    """No principal -> the tool refuses without touching BookingService."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    result = asyncio.run(_service(booking)._run_booking_tool(_full_args("2030-06-03"), None))
    assert result == {
        "outcome": "forbidden",
        "payload": {"reason": "请先以面试官账号登录后再预约面试。"},
    }


def test_rbac_owner_admin_is_forbidden() -> None:
    """owner_admin is not allowed to self-book via the agent tool."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    principal = _interviewer("owner_admin")
    result = asyncio.run(_service(booking)._run_booking_tool(_full_args("2030-06-03"), principal))
    assert result["outcome"] == "forbidden"
    assert "登录" in result["payload"]["reason"]


def test_interviewer_passes_rbac() -> None:
    """interviewer principal clears RBAC and proceeds to slot resolution."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    result = asyncio.run(
        _service(booking)._run_booking_tool(_full_args("2030-06-03"), _interviewer())
    )
    assert result["outcome"] == "confirmed"


# --------------------------------------------------------------------------------------
# Unit layer — date / time parsing
# --------------------------------------------------------------------------------------


def test_needs_info_when_date_missing() -> None:
    """Unparseable / absent target_date + start_time -> needs_info for both."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    result = asyncio.run(
        _service(booking)._run_booking_tool({"target_date": "", "start_time": ""}, _interviewer())
    )
    assert result["outcome"] == "needs_info"
    assert set(result["payload"]["missing"]) == {"target_date", "start_time"}


def test_needs_info_when_time_malformed() -> None:
    """Valid date but malformed start_time -> still needs both fields."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    result = asyncio.run(
        _service(booking)._run_booking_tool(
            {"target_date": "2030-06-03", "start_time": "2pm"}, _interviewer()
        )
    )
    assert result["outcome"] == "needs_info"
    assert set(result["payload"]["missing"]) == {"target_date", "start_time"}


# --------------------------------------------------------------------------------------
# Unit layer — business-field completeness
# --------------------------------------------------------------------------------------


def test_needs_info_when_business_fields_missing() -> None:
    """Valid date + open slots but no company/contact -> needs_info lists the gaps."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    args = {"target_date": "2030-06-03", "start_time": "14:00"}  # nothing else supplied
    result = asyncio.run(_service(booking)._run_booking_tool(args, _interviewer()))
    assert result["outcome"] == "needs_info"
    assert set(result["payload"]["missing"]) == {
        "company_name",
        "meeting_platform",
        "meeting_number",
        "contact_last_name",
        "contact_salutation",
        "contact_phone",
    }


# --------------------------------------------------------------------------------------
# Unit layer — confirmed outcome + payload provenance
# --------------------------------------------------------------------------------------


def test_confirmed_payload_comes_from_create() -> None:
    """A fully-specified request resolves slots and surfaces create()'s appointment."""
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    booking = _FakeBookingService(_make_slots(start_local))
    result = asyncio.run(
        _service(booking)._run_booking_tool(_full_args("2030-06-03"), _interviewer())
    )
    assert result["outcome"] == "confirmed"
    payload = result["payload"]
    assert payload["company_name"] == "Acme Co."
    assert payload["meeting_platform"] == "Tencent Meeting"
    assert payload["contact"] == "TeacherZhang 13800000000"
    assert payload["start_at"].startswith("2030-06-03T14:00")
    assert payload["end_at"].startswith("2030-06-03T15:30")
    # preview + create were both invoked with the resolved 3-slot draft
    assert booking.created_draft is not None
    assert len(booking.created_draft.slot_ids) == 3


# --------------------------------------------------------------------------------------
# Unit layer — slot resolution failure
# --------------------------------------------------------------------------------------


def test_failed_when_a_slot_is_not_available() -> None:
    """Middle slot already booked -> resolution returns None -> failed, no create()."""
    start_local = datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)
    booking = _FakeBookingService(_make_slots(start_local, ("available", "booked", "available")))
    result = asyncio.run(
        _service(booking)._run_booking_tool(_full_args("2030-06-03"), _interviewer())
    )
    assert result["outcome"] == "failed"
    assert "未开放" in result["payload"]["reason"]
    assert booking.created_draft is None


# --------------------------------------------------------------------------------------
# Unit layer — error mapping (preview/create exceptions)
# --------------------------------------------------------------------------------------


def test_failed_when_create_raises_slot_taken() -> None:
    """create() raising AuthError(SLOT_TAKEN) -> failed with the domain reason."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    booking.raise_on_create = AuthError(
        "SLOT_TAKEN", 409, "Slot taken", "Selected slots unavailable"
    )
    result = asyncio.run(
        _service(booking)._run_booking_tool(_full_args("2030-06-03"), _interviewer())
    )
    assert result["outcome"] == "failed"
    assert result["payload"]["reason"] == "Selected slots unavailable"


def test_failed_when_create_raises_integrity_error() -> None:
    """create() raising IntegrityError (concurrent dup) -> failed gracefully."""
    booking = _FakeBookingService(_make_slots(datetime(2030, 6, 3, 14, 0, tzinfo=LOCAL_TIME)))
    booking.raise_on_create = IntegrityError("dup", None, None)
    result = asyncio.run(
        _service(booking)._run_booking_tool(_full_args("2030-06-03"), _interviewer())
    )
    assert result["outcome"] == "failed"
    assert "冲突" in result["payload"]["reason"]


# --------------------------------------------------------------------------------------
# Real-stack layer — genuine BookingService against a dedicated DB
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
    """Dedicated Postgres + Redis + real BookingService wired into AnswerService."""
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


def _seed_interviewer(engine: Engine) -> UUID:
    user_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,'x', 'interviewer', true)"
            ),
            {"id": user_id, "email": f"{user_id}@example.invalid"},
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
def test_real_stack_confirmed_consumes_slots_and_events(real_booking_stack) -> None:
    """End-to-end: a full request creates the appointment, books 3 slots, writes events."""
    engine, _booking, service = real_booking_stack
    user_id = _seed_interviewer(engine)
    # Next Monday 14:00 local (stable future target that never collides with past).
    today = datetime.now(LOCAL_TIME).date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    start_local = datetime.combine(monday, datetime.min.time().replace(hour=14), LOCAL_TIME)
    _seed_slots(engine, start_local)
    principal = Principal(
        id=user_id, email=f"{user_id}@example.invalid", role="interviewer", verified=True
    )
    args = _full_args(start_local.strftime("%Y-%m-%d"), "14:00")
    result = asyncio.run(service._run_booking_tool(args, principal))

    assert result["outcome"] == "confirmed"
    payload = result["payload"]
    assert payload["company_name"] == "Acme Co."
    # appointment.start_at is stored/returned in UTC; compare instants, not strings.
    actual_start = datetime.fromisoformat(payload["start_at"])
    assert actual_start == start_local.astimezone(UTC)
    actual_end = datetime.fromisoformat(payload["end_at"])
    assert actual_end == (start_local + timedelta(minutes=90)).astimezone(UTC)

    with engine.begin() as connection:
        active = connection.execute(
            text("SELECT count(*) FROM appointments WHERE status='active'")
        ).scalar_one()
        booked = connection.execute(
            text("SELECT count(*) FROM appointment_slots WHERE status='booked'")
        ).scalar_one()
        events = connection.execute(
            text(
                "SELECT count(*) FROM notification_events "
                "WHERE type IN ('appointment_created','reminder_due')"
            )
        ).scalar_one()
    assert active == 1
    assert booked == 3
    assert events >= 1


@pytestmark_integration
def test_real_stack_retry_after_booking_fails_gracefully(real_booking_stack) -> None:
    """Re-booking the same (now booked) slots yields a graceful failed frame, not 500."""
    engine, _booking, service = real_booking_stack
    user_id = _seed_interviewer(engine)
    today = datetime.now(LOCAL_TIME).date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    start_local = datetime.combine(monday, datetime.min.time().replace(hour=15), LOCAL_TIME)
    _seed_slots(engine, start_local)
    principal = Principal(
        id=user_id, email=f"{user_id}@example.invalid", role="interviewer", verified=True
    )
    args = _full_args(start_local.strftime("%Y-%m-%d"), "15:00")
    first = asyncio.run(service._run_booking_tool(args, principal))
    assert first["outcome"] == "confirmed"
    # Second attempt with identical slots -> they are now booked -> failed (not crash).
    second = asyncio.run(service._run_booking_tool(args, principal))
    assert second["outcome"] == "failed"
