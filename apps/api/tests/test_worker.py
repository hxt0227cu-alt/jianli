"""Worker tests: SMTP-unconfigured smoke + the full SMTP send path (M3 gap closure).

The SMTP path was runtime-unverified when M3 closed (no SMTP credentials in the dev
environment). This suite closes that gap in two layers:

- ``test_worker_smoke_logs_one_safe_structured_event`` — DB-free, SMTP unset: the worker
  exits without I/O and logs exactly one structured event (existing behavior).
- ``test_worker_smtp_path_claims_renders_marks`` — real PostgreSQL/Redis: an appointment
  created through the API writes ``appointment_created`` + ``reminder_due`` to the Outbox;
  the worker claims the due event, decrypts the appointment, renders the Chinese email,
  "sends" it through a fake SMTP sender and marks the event ``processed``. The future
  ``reminder_due`` stays ``pending`` (scheduled_at gate). No real SMTP server is needed.
"""

from __future__ import annotations

import asyncio
import json
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
from app.auth.repository import AuthRepository
from app.auth.router import CSRF_COOKIE, SESSION_COOKIE
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app
from app.notifications import worker as notification_worker
from app.worker import run_worker

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")
ORIGIN = "https://booking.test"

_NEEDS_DB = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


# ---------------------------------------------------------------------------
# DB-free: SMTP-unconfigured worker smoke
# ---------------------------------------------------------------------------


def test_worker_smoke_logs_one_safe_structured_event(capsys, monkeypatch) -> None:
    monkeypatch.setenv("JIANLI_SECRET_TOKEN", "do-not-log")

    exit_code = run_worker(Settings(log_level="INFO"))

    output = capsys.readouterr().err.strip().splitlines()
    assert exit_code == 0
    assert len(output) == 1
    record = json.loads(output[0])
    assert record["event"] == "worker_smoke_completed"
    assert record["logger"] == "jianli.worker"
    assert "do-not-log" not in output[0]


# ---------------------------------------------------------------------------
# Real PostgreSQL/Redis: SMTP send path (M3 gap closure)
# ---------------------------------------------------------------------------


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
        # SMTP creds present so the worker would construct a sender; the test injects a fake.
        smtp_host="smtp.example.invalid",
        smtp_port=465,
        smtp_user="worker-test@example.invalid",
        smtp_password="worker-test-password",
        smtp_from="worker-test@example.invalid",
    )


def _reset_database(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE audit_logs, notification_events, users, companies CASCADE")
        )


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
                "email": f"interviewer-{user_id}@example.invalid",
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
                {"id": slot_id, "start_at": slot_start, "end_at": slot_start + timedelta(minutes=30)},  # noqa: E501
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


def _draft(slot_ids: list[UUID]) -> dict[str, object]:
    return {
        "slot_ids": [str(value) for value in slot_ids],
        "company_name": "Example, Inc.",
        "meeting_platform": "Tencent Meeting",
        "meeting_number": "123-456-789",
        "contact_last_name": "Zhang",
        "contact_salutation": "Teacher",
        "contact_phone": "13800000000",
        "notes": "Private note",
    }


@_NEEDS_DB
def test_worker_smtp_path_claims_renders_marks() -> None:
    """Full worker path: claim due Outbox event -> decrypt -> render -> send -> processed.

    The future ``reminder_due`` event (start - 10min) must stay pending (scheduled_at
    gate), and only ``appointment_created`` is claimed and processed this round.
    """
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    auth_runtime = build_auth_runtime(settings)
    booking = build_booking_runtime(settings, auth_runtime)
    app = create_app(settings, auth_runtime, booking)
    try:
        interviewer = _seed_user(engine)
        slot_ids = _seed_slots(engine, datetime.now(UTC) + timedelta(days=1, minutes=30))
        draft = _draft(slot_ids)

        async def _create_appointment() -> None:
            async with _authorized_client(app, engine, settings, interviewer) as client:
                preview = await client.post("/appointment-confirmations", json=draft)
                assert preview.status_code == 200, preview.text
                created = await client.post(
                    "/appointments",
                    headers={"Origin": ORIGIN, "Idempotency-Key": str(uuid4())},
                    json={
                        "confirmation_token": preview.json()["confirmation_token"],
                        "appointment": draft,
                    },
                )
                assert created.status_code == 201, created.text

        asyncio.run(_create_appointment())

        with engine.connect() as connection:
            outbox = {
                row["type"]: row["status"]
                for row in connection.execute(
                    text("SELECT type, status FROM notification_events")
                ).mappings()
            }
        assert outbox == {"appointment_created": "pending", "reminder_due": "pending"}

        sent: list[tuple[str, str, str]] = []

        class _FakeSender:
            def send(self, to: str, subject: str, body: str) -> None:
                sent.append((to, subject, body))

        auth_repo = AuthRepository(engine)
        claimed = notification_worker._claim_batch(engine)
        claimed_types = [event_type for _, event_type, _ in claimed]
        assert "appointment_created" in claimed_types
        assert "reminder_due" not in claimed_types  # future scheduled_at gate

        for event_id, event_type, biz_id in claimed:
            notification_worker._process(
                engine, booking, auth_repo, _FakeSender(), event_id, event_type, biz_id
            )
            notification_worker._mark(engine, event_id, "processed")

        assert len(sent) == 1
        _recipient, subject, body = sent[0]
        assert "Example, Inc." in subject
        assert "面试预约确认" in subject
        assert "Example, Inc." in body
        assert "123-456-789" in body
        assert "13800000000" in body

        with engine.connect() as connection:
            final = {
                row["type"]: row["status"]
                for row in connection.execute(
                    text("SELECT type, status FROM notification_events")
                ).mappings()
            }
        assert final["appointment_created"] == "processed"
        assert final["reminder_due"] == "pending"
    finally:
        auth_runtime.close()
        redis_client.close()
        _reset_database(engine)
        engine.dispose()
