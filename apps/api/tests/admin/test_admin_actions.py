"""Integration tests for the M5 admin operations (real PostgreSQL + Redis).

Covers RBAC (owner_admin only), force-cancel slot locking, availability-override
CRUD with slot rematerialization, and company-booking-exception creation with the
open-exception uniqueness guard. Fixtures mirror ``tests/appointments/test_booking.py``.
"""

from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, text

from app.appointments.runtime import build_booking_runtime
from app.auth.passwords import PasswordHasher
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")
ORIGIN = "https://booking.test"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


def _reset_database(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE audit_logs, notification_events, users, companies CASCADE")
        )


def _settings() -> Settings:
    assert DATABASE_URL and REDIS_URL
    return Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        csrf_hmac_key=os.environ["JIANLI_CSRF_HMAC_KEY"],
        rate_limit_hmac_key=os.environ["JIANLI_RATE_LIMIT_HMAC_KEY"],
        allowed_origins=(ORIGIN,),
        field_encryption_current_key_id=os.environ["JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID"],
        field_encryption_keys=os.environ["JIANLI_FIELD_ENCRYPTION_KEYS"],
        company_fingerprint_hmac_key=os.environ["JIANLI_COMPANY_FINGERPRINT_HMAC_KEY"],
        appointment_confirmation_hmac_key=os.environ["JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY"],
    )


@pytest.fixture
def real_stack() -> tuple[Engine, redis.Redis, object, Settings]:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    auth_runtime = build_auth_runtime(settings)
    booking_runtime = build_booking_runtime(settings, auth_runtime)
    app = create_app(settings, auth_runtime, booking_runtime)
    try:
        yield engine, redis_client, app, settings
    finally:
        auth_runtime.close()
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


def _seed_user(engine: Engine, role: str = "interviewer") -> UUID:
    user_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:password_hash,:role,true)"
            ),
            {
                "id": user_id,
                "email": f"{user_id}@example.invalid",
                "password_hash": PasswordHasher().hash("correct-password"),
                "role": role,
            },
        )
    return user_id


def _seed_slots(engine: Engine, start: datetime, count: int = 3) -> list[UUID]:
    ids = [uuid4() for _ in range(count)]
    with engine.begin() as connection:
        for offset, slot_id in enumerate(ids):
            slot_start = start + timedelta(minutes=30 * offset)
            connection.execute(
                text(
                    "INSERT INTO appointment_slots "
                    "(id,start_at,end_at,status,appointment_id,version) "
                    "VALUES (:id,:start_at,:end_at,'available',NULL,1)"
                ),
                {
                    "id": slot_id,
                    "start_at": slot_start,
                    "end_at": slot_start + timedelta(minutes=30),
                },
            )
    return ids


def _seed_appointment(
    engine: Engine, user_id: UUID, slot_ids: list[UUID], start: datetime
) -> UUID:
    company_id = uuid4()
    appointment_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO companies (id,normalized_name_fingerprint,raw_name_ciphertext) "
                "VALUES (:id,'admin-test-company',:value)"
            ),
            {"id": company_id, "value": b"encrypted"},
        )
        connection.execute(
            text(
                "INSERT INTO appointments "
                "(id,user_id,company_id,start_at,end_at,status,"
                "company_name_ciphertext,company_name_fingerprint,version,created_at) "
                "VALUES (:id,:user_id,:company_id,:start_at,:end_at,'active',"
                ":ciphertext,'admin-test-company',1,:created_at)"
            ),
            {
                "id": appointment_id,
                "user_id": user_id,
                "company_id": company_id,
                "start_at": start,
                "end_at": start + timedelta(minutes=90),
                "ciphertext": b"encrypted",
                "created_at": datetime.now(UTC),
            },
        )
        connection.execute(
            text(
                "UPDATE appointment_slots SET status='booked',appointment_id=:aid,version=2 "
                "WHERE id=ANY(CAST(:slot_ids AS uuid[]))"
            ),
            {"aid": appointment_id, "slot_ids": slot_ids},
        )
    return appointment_id


def _authorized_client(
    app: object, engine: Engine, settings: Settings, user_id: UUID
) -> AsyncClient:
    session_token = secrets.token_urlsafe(32)
    auth_runtime = app.state.auth_runtime
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO auth_sessions "
                "(id,user_id,session_token_hash,expires_at,revoked_at) "
                "VALUES (:id,:user_id,:token_hash,:expires_at,NULL)"
            ),
            {
                "id": uuid4(),
                "user_id": user_id,
                "token_hash": auth_runtime.tokens.digest(session_token),
                "expires_at": datetime.now(UTC) + timedelta(hours=1),
            },
        )
    csrf = auth_runtime.tokens.csrf(session_token)
    client = AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN)
    client.cookies.set(SESSION_COOKIE, session_token)
    client.cookies.set(CSRF_COOKIE, csrf)
    client.headers.update({"Origin": ORIGIN, "X-CSRF-Token": csrf})
    return client


def _slot_status(engine: Engine, slot_id: UUID) -> str:
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT status::text FROM appointment_slots WHERE id=:id"), {"id": slot_id}
        ).scalar_one()


@pytest.mark.asyncio
async def test_admin_reads_enforce_owner_role(real_stack) -> None:
    engine, _, app, settings = real_stack
    interviewer = _seed_user(engine, "interviewer")
    owner = _seed_user(engine, "owner_admin")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://testserver"
    ) as anonymous:
        for path in ("/admin/appointments", "/admin/availability-overrides"):
            denied = await anonymous.get(path)
            assert denied.status_code == 401
            assert denied.json()["code"] == "AUTH_EXPIRED"

    async with _authorized_client(app, engine, settings, interviewer) as client:
        for path in ("/admin/appointments", "/admin/availability-overrides"):
            denied = await client.get(path)
            assert denied.status_code == 403
            assert denied.json()["code"] == "PERM_DENIED"

    async with _authorized_client(app, engine, settings, owner) as client:
        for path in ("/admin/appointments", "/admin/availability-overrides"):
            ok = await client.get(path)
            assert ok.status_code == 200
            assert set(ok.json()) == {"items"}


@pytest.mark.asyncio
async def test_force_cancel_locks_appointment_slots(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    interviewer = _seed_user(engine)
    start = datetime(2030, 6, 3, 1, 0, tzinfo=UTC)
    slot_ids = _seed_slots(engine, start)
    appointment_id = _seed_appointment(engine, interviewer, slot_ids, start)

    async with _authorized_client(app, engine, settings, owner) as client:
        response = await client.post(
            f"/admin/appointments/{appointment_id}/force-cancel",
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 204
    with engine.connect() as connection:
        status = connection.execute(
            text("SELECT status::text FROM appointments WHERE id=:id"), {"id": appointment_id}
        ).scalar_one()
        assert status == "cancelled"
        linked = connection.execute(
            text(
                "SELECT count(*) FROM appointment_slots WHERE appointment_id=:id"
            ),
            {"id": appointment_id},
        ).scalar_one()
        assert linked == 0
    for slot_id in slot_ids:
        assert _slot_status(engine, slot_id) == "owner_locked"

    # Idempotent: a second force-cancel on an already-cancelled appointment is 204.
    async with _authorized_client(app, engine, settings, owner) as client:
        again = await client.post(
            f"/admin/appointments/{appointment_id}/force-cancel",
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert again.status_code == 204

    # Missing Idempotency-Key is rejected by the contract (422).
    async with _authorized_client(app, engine, settings, owner) as client:
        no_key = await client.post(f"/admin/appointments/{appointment_id}/force-cancel")
    assert no_key.status_code == 422


@pytest.mark.asyncio
async def test_availability_override_crud_rematerializes_slots(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    base = datetime(2030, 6, 3, 1, 0, tzinfo=UTC)
    slot_ids = _seed_slots(engine, base)
    window_start = base
    window_end = base + timedelta(hours=1)  # covers the first two 30-min slots

    async with _authorized_client(app, engine, settings, owner) as client:
        created = await client.post(
            "/admin/availability-overrides",
            json={
                "start_at": window_start.isoformat(),
                "end_at": window_end.isoformat(),
                "action": "force_unavailable",
                "reason": "maintenance",
            },
        )
    assert created.status_code == 201
    body = created.json()
    assert body["action"] == "force_unavailable"
    assert body["reason"] == "maintenance"
    override_id = body["id"]
    # First two slots now unavailable; the third (outside the window) stays available.
    assert _slot_status(engine, slot_ids[0]) == "unavailable"
    assert _slot_status(engine, slot_ids[1]) == "unavailable"
    assert _slot_status(engine, slot_ids[2]) == "available"

    listed = await client.get("/admin/availability-overrides")
    assert listed.status_code == 200
    assert any(item["id"] == override_id for item in listed.json()["items"])

    updated = await client.patch(
        f"/admin/availability-overrides/{override_id}",
        json={
            "start_at": window_start.isoformat(),
            "end_at": window_end.isoformat(),
            "action": "force_available",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["action"] == "force_available"
    assert _slot_status(engine, slot_ids[0]) == "available"
    assert _slot_status(engine, slot_ids[1]) == "available"
    assert _slot_status(engine, slot_ids[2]) == "available"

    deleted = await client.delete(f"/admin/availability-overrides/{override_id}")
    assert deleted.status_code == 204
    assert _slot_status(engine, slot_ids[0]) == "available"

    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT count(*) FROM availability_overrides")
        ).scalar_one() == 0
        audit = connection.execute(
            text(
                "SELECT action FROM audit_logs WHERE target=:id ORDER BY created_at"
            ),
            {"id": UUID(override_id)},
        ).scalars().all()
        assert audit == [
            "availability_override.created",
            "availability_override.updated",
            "availability_override.deleted",
        ]


@pytest.mark.asyncio
async def test_override_rejects_invalid_range(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    base = datetime(2030, 6, 3, 1, 0, tzinfo=UTC)
    async with _authorized_client(app, engine, settings, owner) as client:
        bad = await client.post(
            "/admin/availability-overrides",
            json={
                "start_at": base.isoformat(),
                "end_at": base.isoformat(),
                "action": "force_unavailable",
            },
        )
    assert bad.status_code == 422
    assert bad.json()["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_create_company_exception_and_duplicate(real_stack) -> None:
    engine, _, app, settings = real_stack
    owner = _seed_user(engine, "owner_admin")
    interviewer = _seed_user(engine)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    async with _authorized_client(app, engine, settings, owner) as client:
        created = await client.post(
            "/admin/company-booking-exceptions",
            json={
                "interviewer_user_id": str(interviewer),
                "company_name": "Dup, Inc.",
                "reason": "campus recruiting exception",
                "expires_at": expires_at.isoformat(),
            },
        )
    assert created.status_code == 201
    body = created.json()
    assert body["interviewer_user_id"] == str(interviewer)
    assert body["company_name"] == "Dup, Inc."
    exception_id = body["id"]

    # A second open exception for the same interviewer + company is rejected (409).
    async with _authorized_client(app, engine, settings, owner) as client:
        duplicate = await client.post(
            "/admin/company-booking-exceptions",
            json={
                "interviewer_user_id": str(interviewer),
                "company_name": "Dup, Inc.",
                "reason": "another reason",
                "expires_at": expires_at.isoformat(),
            },
        )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUP_EXCEPTION"

    # Past expiry is rejected (422).
    async with _authorized_client(app, engine, settings, owner) as client:
        past = await client.post(
            "/admin/company-booking-exceptions",
            json={
                "interviewer_user_id": str(interviewer),
                "company_name": "Future Co",
                "reason": "ok",
                "expires_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            },
        )
    assert past.status_code == 422

    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT count(*) FROM company_booking_exceptions")
        ).scalar_one() == 1
        assert connection.execute(
            text(
                "SELECT action FROM audit_logs WHERE target=:id"
            ),
            {"id": UUID(exception_id)},
        ).scalar_one() == "company_booking_exception.created"


@pytest.mark.asyncio
async def test_interviewer_cannot_mutate_overrides(real_stack) -> None:
    engine, _, app, settings = real_stack
    interviewer = _seed_user(engine, "interviewer")
    base = datetime(2030, 6, 3, 1, 0, tzinfo=UTC)
    async with _authorized_client(app, engine, settings, interviewer) as client:
        denied = await client.post(
            "/admin/availability-overrides",
            json={
                "start_at": base.isoformat(),
                "end_at": (base + timedelta(hours=1)).isoformat(),
                "action": "force_unavailable",
            },
        )
    assert denied.status_code == 403
    assert denied.json()["code"] == "PERM_DENIED"
