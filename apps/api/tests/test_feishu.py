"""Feishu channel tests (R13 candidate reminders + R14 Bitable mirror).

Covers the candidate-side delivery chain added by TASK-FEISHU-001:
- materializing candidate delivery rows (email + feishu) per event, idempotently
  (``uq_delivery_attempt``);
- per-channel delivery: candidate email via the SMTP sender, feishu mirror/message
  via the gateway stub;
- failure isolation: a failing feishu mirror marks only the feishu row ``failed``
  and raises a ``FEISHU_SYNC_FAIL`` alert email; the email row stays independent;
- feishu disabled -> only the email row is materialized;
- no active owner_admin -> candidate delivery skipped.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import redis
from sqlalchemy import Engine, create_engine, text

from app.appointments.crypto import FieldCipher
from app.appointments.runtime import build_booking_runtime
from app.auth.runtime import build_auth_runtime
from app.factory import create_app
from app.notifications import worker as notification_worker
from app.notifications.feishu import StubFeishuGateway
from tests.test_worker import (
    ORIGIN,
    _authorized_client,
    _draft,
    _reset_database,
    _safe_future_start,
    _seed_slots,
    _seed_user,
    _settings,
)

DATABASE_URL = os.environ.get("JIANLI_BOOKING_TEST_DATABASE_URL")
REDIS_URL = os.environ.get("JIANLI_BOOKING_TEST_REDIS_URL")

_NEEDS_DB = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL, reason="real PostgreSQL and Redis are required"
)


class _FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


class _FailingFeishu(StubFeishuGateway):
    def upsert_bitable_row(self, appointment, known_record_id: str | None) -> str:  # type: ignore[no-untyped-def]
        raise RuntimeError("bitable quota exceeded")


def _field_cipher(settings: object) -> FieldCipher:
    key_ring = json.loads(settings.field_encryption_keys.get_secret_value())  # type: ignore[attr-defined]
    return FieldCipher(settings.field_encryption_current_key_id, key_ring)  # type: ignore[attr-defined]


def _seed_owner_admin(
    engine: Engine, cipher: FieldCipher, open_id: str | None
) -> tuple[UUID, UUID]:
    """Insert the unique active owner_admin + their contact config (encrypted open_id)."""

    owner_id = _seed_user(engine, role="owner_admin")
    config_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO owner_contact_configs "
                "(id,user_id,candidate_phone_ciphertext,candidate_feishu_open_id_ciphertext,"
                "updated_at) VALUES (:id,:user_id,NULL,:open_id,:now)"
            ),
            {
                "id": config_id,
                "user_id": owner_id,
                "open_id": (
                    cipher.encrypt(
                        open_id,
                        "owner_contact_configs",
                        "candidate_feishu_open_id_ciphertext",
                        config_id,
                    )
                    if open_id
                    else None
                ),
                "now": datetime.now(UTC),
            },
        )
    return owner_id, config_id


def _create_appointment(engine: Engine, settings: object, owner: UUID) -> tuple[UUID, UUID]:
    """Create one appointment through the API; return (appointment_id, event_id)."""

    auth_runtime = build_auth_runtime(settings)  # type: ignore[arg-type]
    booking = build_booking_runtime(settings, auth_runtime)  # type: ignore[arg-type]
    app = create_app(settings, auth_runtime, booking)  # type: ignore[arg-type]
    slot_ids = _seed_slots(engine, _safe_future_start())
    draft = _draft(slot_ids)

    import asyncio

    async def _create() -> None:
        async with _authorized_client(app, engine, settings, owner) as client:  # type: ignore[arg-type]
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

    asyncio.run(_create())
    with engine.connect() as connection:
        appointment_id = connection.execute(
            text("SELECT id FROM appointments ORDER BY created_at DESC LIMIT 1")
        ).scalar()
        event = connection.execute(
            text(
                "SELECT id FROM notification_events "
                "WHERE type='appointment_created' ORDER BY created_at DESC LIMIT 1"
            )
        ).scalar()
    auth_runtime.close()
    return appointment_id, event


def _delivery_rows(engine: Engine, event_id: UUID) -> list[dict[str, object]]:
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    "SELECT channel,status,last_error,provider_message_id,channel_metadata "
                    "FROM notification_deliveries WHERE event_id=:id ORDER BY channel"
                ),
                {"id": event_id},
            ).mappings()
        ]


@_NEEDS_DB
def test_candidate_dual_channel_delivers_email_and_feishu() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _owner_id, _config_id = _seed_owner_admin(engine, cipher, "ou_candidate_001")
        interviewer = _seed_user(engine)
        appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        email_sender = _FakeEmailSender()
        feishu = StubFeishuGateway()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine, booking, email_sender, feishu, cipher, event_id, "appointment_created",
            appointment_id, datetime.now(UTC),
        )

        rows = _delivery_rows(engine, event_id)
        by_channel = {row["channel"]: row for row in rows}
        assert set(by_channel) == {"email", "feishu"}
        assert by_channel["email"]["status"] == "succeeded"
        assert by_channel["feishu"]["status"] == "succeeded"
        assert len(email_sender.sent) == 1
        assert "候选人" in email_sender.sent[0][1]
        assert len(feishu.messages) == 1
        assert feishu.messages[0][0] == "ou_candidate_001"
        assert len(feishu.rows) == 1
        metadata = by_channel["feishu"]["channel_metadata"]
        assert metadata["feishu_record_id"] is not None
        assert metadata["open_id_configured"] is True
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_completed_event_updates_bitable_without_email_or_feishu_message() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _seed_owner_admin(engine, cipher, "ou_candidate_completed")
        interviewer = _seed_user(engine)
        appointment_id, _created_event_id = _create_appointment(engine, settings, interviewer)
        completed_event_id = uuid4()
        now = datetime.now(UTC)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE appointments SET status='completed',completed_at=end_at "
                    "WHERE id=:id"
                ),
                {"id": appointment_id},
            )
            connection.execute(
                text(
                    "INSERT INTO notification_events "
                    "(id,type,biz_id,idempotency_key,status,created_at) VALUES "
                    "(:id,'appointment_completed',:biz_id,:key,'pending',:now)"
                ),
                {
                    "id": completed_event_id,
                    "biz_id": appointment_id,
                    "key": f"appointment:{appointment_id}:appointment_completed",
                    "now": now,
                },
            )

        email_sender = _FakeEmailSender()
        feishu = StubFeishuGateway()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine,
            booking,
            email_sender,
            feishu,
            cipher,
            completed_event_id,
            "appointment_completed",
            appointment_id,
            now,
        )

        rows = _delivery_rows(engine, completed_event_id)
        assert len(rows) == 1
        assert rows[0]["channel"] == "feishu"
        assert rows[0]["status"] == "succeeded"
        assert rows[0]["channel_metadata"]["message_suppressed"] is True
        assert email_sender.sent == []
        assert feishu.messages == []
        assert len(feishu.rows) == 1
        assert next(iter(feishu.rows.values()))["状态"] == "completed"
        assert notification_worker._has_failed_delivery(engine, completed_event_id) is False
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_feishu_mirror_failure_marks_failed_and_alerts() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _owner_id, _config_id = _seed_owner_admin(engine, cipher, "ou_candidate_002")
        interviewer = _seed_user(engine)
        appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        email_sender = _FakeEmailSender()
        feishu = _FailingFeishu()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine, booking, email_sender, feishu, cipher, event_id, "appointment_created",
            appointment_id, datetime.now(UTC),
        )

        rows = _delivery_rows(engine, event_id)
        by_channel = {row["channel"]: row for row in rows}
        assert by_channel["email"]["status"] == "succeeded"  # channel isolation
        assert by_channel["feishu"]["status"] == "failed"
        assert "bitable quota exceeded" in str(by_channel["feishu"]["last_error"])
        # FEISHU_SYNC_FAIL alert email went to the candidate (owner_admin)
        assert len(email_sender.sent) == 2
        assert "告警" in email_sender.sent[1][1]
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_missing_open_id_feishu_row_succeeds_without_message() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _seed_owner_admin(engine, cipher, None)  # no feishu open_id configured
        interviewer = _seed_user(engine)
        appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        email_sender = _FakeEmailSender()
        feishu = StubFeishuGateway()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine, booking, email_sender, feishu, cipher, event_id, "appointment_created",
            appointment_id, datetime.now(UTC),
        )

        rows = _delivery_rows(engine, event_id)
        by_channel = {row["channel"]: row for row in rows}
        assert by_channel["email"]["status"] == "succeeded"
        assert by_channel["feishu"]["status"] == "succeeded"  # mirror only, no message
        assert len(feishu.messages) == 0
        metadata = by_channel["feishu"]["channel_metadata"]
        assert metadata["open_id_configured"] is False
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_feishu_disabled_materializes_email_row_only() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _seed_owner_admin(engine, cipher, "ou_candidate_003")
        interviewer = _seed_user(engine)
        appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        email_sender = _FakeEmailSender()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine, booking, email_sender, None, cipher, event_id, "appointment_created",
            appointment_id, datetime.now(UTC),
        )

        rows = _delivery_rows(engine, event_id)
        assert [row["channel"] for row in rows] == ["email"]
        assert rows[0]["status"] == "succeeded"
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_materialize_is_idempotent_via_unique_attempt_key() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        _seed_owner_admin(engine, cipher, "ou_candidate_004")
        interviewer = _seed_user(engine)
        _appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        now = datetime.now(UTC)
        first = notification_worker._materialize_candidate_deliveries(
            engine, event_id, now, ("email", "feishu")
        )
        second = notification_worker._materialize_candidate_deliveries(
            engine, event_id, now, ("email", "feishu")
        )
        assert [row[0] for row in first] == [row[0] for row in second]
        with engine.connect() as connection:
            count = connection.execute(
                text(
                    "SELECT count(*) FROM notification_deliveries WHERE event_id=:id"
                ),
                {"id": event_id},
            ).scalar()
        assert count == 2
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()


@_NEEDS_DB
def test_no_active_owner_admin_skips_candidate_delivery() -> None:
    settings = _settings()
    engine = create_engine(settings.database_url)
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.flushdb()
    _reset_database(engine)
    try:
        cipher = _field_cipher(settings)
        interviewer = _seed_user(engine)  # no owner_admin in this DB
        appointment_id, event_id = _create_appointment(engine, settings, interviewer)

        email_sender = _FakeEmailSender()
        feishu = StubFeishuGateway()
        booking = build_booking_runtime(
            settings, build_auth_runtime(settings)  # type: ignore[arg-type]
        )
        notification_worker._deliver_candidate(
            engine, booking, email_sender, feishu, cipher, event_id, "appointment_created",
            appointment_id, datetime.now(UTC),
        )

        assert email_sender.sent == []
        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT count(*) FROM notification_deliveries WHERE event_id=:id"),
                {"id": event_id},
            ).scalar()
        assert count == 0
    finally:
        redis_client.close()
        _reset_database(engine)
        engine.dispose()
