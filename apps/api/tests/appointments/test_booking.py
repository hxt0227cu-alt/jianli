from __future__ import annotations

import asyncio
import os
import secrets
import threading
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, event, text

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


def _seed_slots(engine: Engine, start: datetime) -> list[UUID]:
    ids = [uuid4(), uuid4(), uuid4()]
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


def _draft(slot_ids: list[UUID], company: str = "Example, Inc.") -> dict[str, object]:
    return {
        "slot_ids": [str(value) for value in slot_ids],
        "company_name": company,
        "meeting_platform": "Tencent Meeting",
        "meeting_number": "123-456-789",
        "contact_last_name": "Zhang",
        "contact_salutation": "Teacher",
        "contact_phone": "13800000000",
        "notes": "Private note",
    }


@pytest.mark.asyncio
async def test_preview_is_read_only_and_auth_boundaries(real_stack) -> None:
    engine, _, app, settings = real_stack
    interviewer = _seed_user(engine)
    owner = _seed_user(engine, "owner_admin")
    slots = _seed_slots(engine, datetime(2030, 6, 3, 1, 0, tzinfo=UTC))
    draft = _draft(slots)
    before = _table_counts(engine)

    async with _authorized_client(app, engine, settings, interviewer) as client:
        response = await client.post("/appointment-confirmations", json=draft)
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {
            "confirmation_token",
            "expires_at",
            "company_name",
            "recipient_email",
            "salutation",
        }
        assert body["company_name"] == draft["company_name"]
        assert body["recipient_email"] == f"{interviewer}@example.invalid"
        assert body["salutation"] == "Zhang Teacher"
        assert datetime.fromisoformat(body["expires_at"]) - datetime.now(UTC) <= timedelta(
            minutes=3
        )
    assert _table_counts(engine) == before

    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anonymous:
        denied = await anonymous.post(
            "/appointment-confirmations", headers={"Origin": ORIGIN}, json=draft
        )
        assert denied.status_code == 401
        assert denied.json()["code"] == "AUTH_EXPIRED"
    async with _authorized_client(app, engine, settings, owner) as owner_client:
        denied = await owner_client.post("/appointment-confirmations", json=draft)
        assert denied.status_code == 403
        assert denied.json()["code"] == "PERM_DENIED"
    async with _authorized_client(app, engine, settings, interviewer) as cross_origin:
        denied = await cross_origin.post(
            "/appointment-confirmations", headers={"Origin": "https://evil.invalid"}, json=draft
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "PERM_DENIED"

    async with _authorized_client(app, engine, settings, interviewer) as csrf_client:
        csrf = csrf_client.headers.pop("X-CSRF-Token")
        missing = await csrf_client.post("/appointment-confirmations", json=draft)
        assert missing.status_code == 403
        assert missing.json()["code"] == "PERM_DENIED"
        wrong = await csrf_client.post(
            "/appointment-confirmations", headers={"X-CSRF-Token": "wrong"}, json=draft
        )
        assert wrong.status_code == 403
        assert wrong.json()["code"] == "PERM_DENIED"
        csrf_client.headers["X-CSRF-Token"] = csrf


@pytest.mark.asyncio
async def test_create_auth_csrf_and_origin_boundaries(real_stack) -> None:
    engine, _, app, settings = real_stack
    interviewer = _seed_user(engine)
    owner = _seed_user(engine, "owner_admin")
    slots = _seed_slots(engine, datetime(2030, 6, 3, 1, 30, tzinfo=UTC))
    draft = _draft(slots)
    async with _authorized_client(app, engine, settings, interviewer) as preview_client:
        preview = await preview_client.post("/appointment-confirmations", json=draft)
    payload = {
        "confirmation_token": preview.json()["confirmation_token"],
        "appointment": draft,
    }
    idempotency = {"Idempotency-Key": str(uuid4())}

    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as anonymous:
        denied = await anonymous.post(
            "/appointments", headers={"Origin": ORIGIN, **idempotency}, json=payload
        )
        assert denied.status_code == 401
        assert denied.json()["code"] == "AUTH_EXPIRED"
    async with _authorized_client(app, engine, settings, owner) as owner_client:
        denied = await owner_client.post("/appointments", headers=idempotency, json=payload)
        assert denied.status_code == 403
        assert denied.json()["code"] == "PERM_DENIED"
    async with _authorized_client(app, engine, settings, interviewer) as csrf_client:
        csrf = csrf_client.headers.pop("X-CSRF-Token")
        missing = await csrf_client.post("/appointments", headers=idempotency, json=payload)
        assert missing.status_code == 403
        assert missing.json()["code"] == "PERM_DENIED"
        wrong = await csrf_client.post(
            "/appointments",
            headers={**idempotency, "X-CSRF-Token": "wrong"},
            json=payload,
        )
        assert wrong.status_code == 403
        assert wrong.json()["code"] == "PERM_DENIED"
        csrf_client.headers["X-CSRF-Token"] = csrf
        cross_origin = await csrf_client.post(
            "/appointments",
            headers={**idempotency, "Origin": "https://evil.invalid"},
            json=payload,
        )
        assert cross_origin.status_code == 403
        assert cross_origin.json()["code"] == "PERM_DENIED"
    assert _table_counts(engine)["appointments"] == 0


@pytest.mark.asyncio
async def test_create_redis_outage_fails_closed_and_preview_uses_no_quota(real_stack) -> None:
    engine, redis_client, app, settings = real_stack
    user_id = _seed_user(engine)
    slots = _seed_slots(engine, datetime(2030, 6, 3, 2, 0, tzinfo=UTC))
    draft = _draft(slots)
    booking_keys_before = set(redis_client.scan_iter(match="booking:create:account:*"))
    async with _authorized_client(app, engine, settings, user_id) as client:
        preview = await client.post("/appointment-confirmations", json=draft)
        assert preview.status_code == 200
        assert set(redis_client.scan_iter(match="booking:create:account:*")) == booking_keys_before

        limiter = app.state.booking_runtime._rate_limiter
        working_client = limiter._client
        unavailable_client = redis.Redis(
            host="127.0.0.1", port=1, socket_connect_timeout=0.1, socket_timeout=0.1
        )
        limiter._client = unavailable_client
        try:
            response = await client.post(
                "/appointments",
                headers={"Idempotency-Key": str(uuid4())},
                json={
                    "confirmation_token": preview.json()["confirmation_token"],
                    "appointment": draft,
                },
            )
        finally:
            limiter._client = working_client
            unavailable_client.close()
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert _table_counts(engine)["appointments"] == 0


@pytest.mark.asyncio
async def test_create_is_atomic_encrypted_and_rate_limited(real_stack, caplog) -> None:
    engine, redis_client, app, settings = real_stack
    user_id = _seed_user(engine)
    slots = _seed_slots(engine, datetime(2030, 6, 3, 2, 30, tzinfo=UTC))
    draft = _draft(slots)
    async with _authorized_client(app, engine, settings, user_id) as client:
        preview = await client.post("/appointment-confirmations", json=draft)
        response = await client.post(
            "/appointments",
            headers={"Idempotency-Key": str(uuid4())},
            json={"confirmation_token": preview.json()["confirmation_token"], "appointment": draft},
        )
        assert response.status_code == 201
        assert set(response.json()) == set(draft) | {
            "id",
            "status",
            "version",
            "start_at",
            "end_at",
        }

    with engine.connect() as connection:
        appointment = connection.execute(text("SELECT * FROM appointments")).mappings().one()
        assert appointment["company_name_ciphertext"] != draft["company_name"].encode()
        assert appointment["meeting_number_ciphertext"] != draft["meeting_number"].encode()
        assert (
            connection.execute(
                text("SELECT count(*) FROM appointment_slots WHERE status='booked'")
            ).scalar_one()
            == 3
        )
        assert (
            connection.execute(text("SELECT count(*) FROM notification_events")).scalar_one() == 2
        )
        assert set(
            connection.execute(text("SELECT type::text FROM notification_events")).scalars()
        ) == {"appointment_created", "reminder_due"}
        audit = connection.execute(text("SELECT * FROM audit_logs")).mappings().one()
        assert audit["actor"] == str(user_id)
        assert audit["action"] == "appointment.created"
        serialized = " ".join(str(value) for value in audit.values())
        for sensitive in ("Example", "123-456", "138000", "Private note"):
            assert sensitive not in serialized

    redis_client.flushdb()
    other_user = _seed_user(engine)
    for index in range(10):
        extra_slots = _seed_slots(engine, datetime(2030, 7, 1 + index, 1, 0, tzinfo=UTC))
        extra_draft = _draft(extra_slots, f"Company {index}")
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE appointments SET status='completed' WHERE user_id=:id"),
                {"id": other_user},
            )
        async with _authorized_client(app, engine, settings, other_user) as client:
            preview = await client.post("/appointment-confirmations", json=extra_draft)
            attempt = await client.post(
                "/appointments",
                headers={"Idempotency-Key": str(uuid4())},
                json={
                    "confirmation_token": preview.json()["confirmation_token"],
                    "appointment": extra_draft,
                },
            )
            assert attempt.status_code == 201
    final_slots = _seed_slots(engine, datetime(2030, 8, 1, 1, 0, tzinfo=UTC))
    async with _authorized_client(app, engine, settings, other_user) as client:
        preview = await client.post(
            "/appointment-confirmations", json=_draft(final_slots, "Limited")
        )
        limited = await client.post(
            "/appointments",
            headers={"Idempotency-Key": str(uuid4())},
            json={
                "confirmation_token": preview.json()["confirmation_token"],
                "appointment": _draft(final_slots, "Limited"),
            },
        )
        assert limited.status_code == 429
        assert limited.json()["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_confirmation_tampering_has_no_side_effect(real_stack) -> None:
    engine, _, app, settings = real_stack
    user_id = _seed_user(engine)
    slots = _seed_slots(engine, datetime(2030, 6, 4, 1, 0, tzinfo=UTC))
    draft = _draft(slots)
    async with _authorized_client(app, engine, settings, user_id) as client:
        preview = await client.post("/appointment-confirmations", json=draft)
        changed = dict(draft, meeting_number="changed")
        response = await client.post(
            "/appointments",
            headers={"Idempotency-Key": str(uuid4())},
            json={
                "confirmation_token": preview.json()["confirmation_token"],
                "appointment": changed,
            },
        )
        assert response.status_code == 409
        assert response.json()["code"] == "CONFIRM_EXPIRED"
    assert _table_counts(engine)["appointments"] == 0


@pytest.mark.asyncio
async def test_two_transactions_race_for_slots_ten_rounds(real_stack) -> None:
    engine, redis_client, app, settings = real_stack
    booking_engine = app.state.booking_runtime._engine
    durations: list[float] = []
    for round_number in range(10):
        _reset_database(engine)
        redis_client.flushdb()
        users = [_seed_user(engine), _seed_user(engine)]
        slots = _seed_slots(engine, datetime(2031, 1, 2 + round_number, 1, 0, tzinfo=UTC))
        clients = [_authorized_client(app, engine, settings, user_id) for user_id in users]
        try:
            drafts = [_draft(slots, f"Race Company {round_number}-{index}") for index in range(2)]
            previews = await asyncio.gather(
                *[
                    client.post("/appointment-confirmations", json=draft)
                    for client, draft in zip(clients, drafts, strict=True)
                ]
            )
            barrier = threading.Barrier(2)
            backend_pids: list[int] = []
            pid_lock = threading.Lock()

            def observe_slot_lock(
                _connection, cursor, statement, _parameters, _context, _executemany
            ) -> None:
                if "FROM appointment_slots" not in statement or "FOR UPDATE" not in statement:
                    return
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = int(cursor.fetchone()[0])
                with pid_lock:
                    backend_pids.append(backend_pid)
                barrier.wait(timeout=5)

            event.listen(booking_engine, "before_cursor_execute", observe_slot_lock)
            started = time.perf_counter()
            try:
                results = await asyncio.gather(
                    *[
                        client.post(
                            "/appointments",
                            headers={"Idempotency-Key": str(uuid4())},
                            json={
                                "confirmation_token": preview.json()["confirmation_token"],
                                "appointment": draft,
                            },
                        )
                        for client, preview, draft in zip(clients, previews, drafts, strict=True)
                    ]
                )
            finally:
                event.remove(booking_engine, "before_cursor_execute", observe_slot_lock)
            durations.append(time.perf_counter() - started)
            assert barrier.n_waiting == 0
            assert len(backend_pids) == 2
            assert len(set(backend_pids)) == 2
            assert sorted(response.status_code for response in results) == [201, 409]
            loser = next(response for response in results if response.status_code == 409)
            assert loser.json()["code"] == "SLOT_TAKEN"
            counts = _table_counts(engine)
            assert counts == {
                "companies": 1,
                "appointments": 1,
                "appointment_slots": 3,
                "notification_events": 2,
                "audit_logs": 1,
            }
            winner = next(response for response in results if response.status_code == 201)
            with engine.connect() as connection:
                slot_rows = connection.execute(
                    text(
                        "SELECT status::text,appointment_id FROM appointment_slots "
                        "ORDER BY start_at,id"
                    )
                ).mappings()
                assert all(
                    row["status"] == "booked"
                    and str(row["appointment_id"]) == winner.json()["id"]
                    for row in slot_rows
                )
        finally:
            await asyncio.gather(*(client.aclose() for client in clients))
    assert max(durations) <= 1.5


def _table_counts(engine: Engine) -> dict[str, int]:
    tables = ("companies", "appointments", "appointment_slots", "notification_events", "audit_logs")
    with engine.connect() as connection:
        return {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in tables
        }
