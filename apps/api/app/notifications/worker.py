"""Notification Outbox consumer (M3 + R13/R14 Feishu channel, TASK-FEISHU-001).

Polls ``notification_events`` (pending, due) and sends email via the runtime SMTP
channel (interviewer side, M3) plus candidate-facing dual-channel deliveries
(R13/R14): candidate email + Feishu mirror/message, recorded per attempt in
``notification_deliveries`` (domain model §6.12) with the ``uq_delivery_attempt``
unique key preventing duplicate rows from concurrent consumers.

Delivery is at-least-once: events are claimed with ``FOR UPDATE SKIP LOCKED`` and
marked ``processed`` / ``failed``; ``failed`` events within a 10-minute window are
re-queued for retry. Candidate deliveries keep their own status machine and retry
window, independent of the interviewer email path (channels never backstop each
other, architecture §6.8).

Feishu is skipped entirely (no rows, no alerts) when ``settings.feishu_configured``
is false — equivalent to the feature being off. When configured, a failing mirror
produces a ``failed`` delivery row plus a ``FEISHU_SYNC_FAIL`` alert email to the
candidate; the interviewer email is unaffected.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from threading import Event
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from app.appointments.crypto import FieldCipher
from app.appointments.service import BookingService
from app.auth.repository import AuthRepository
from app.config import Settings

from .email import (
    EmailSender,
    render,
    render_candidate_notification,
    render_sync_fail_email,
)
from .feishu import FeishuAPIGateway, FeishuGateway

if TYPE_CHECKING:  # annotations are lazy (PEP 563), so this stays import-cycle free
    from app.appointments.models import Appointment

LOGGER = logging.getLogger("jianli.notifications")
_POLL_INTERVAL = 2.0
_CLAIM_LIMIT = 20
_RETRY_WINDOW = "10 minutes"

# Events that carry a candidate-side delivery (R13 reminders + R14 mirror).
_CANDIDATE_EVENTS = {
    "appointment_created",
    "appointment_rescheduled",
    "appointment_cancelled",
    "reminder_due",
}


def _claim_batch(engine: Engine) -> list[tuple[UUID, str, UUID]]:
    with engine.begin() as connection:
        rows = connection.execute(
            text(
                "UPDATE notification_events SET status='processing' "
                "WHERE id IN ("
                "  SELECT id FROM notification_events "
                "  WHERE status='pending' AND (scheduled_at IS NULL OR scheduled_at <= now()) "
                "  ORDER BY created_at LIMIT :limit FOR UPDATE SKIP LOCKED"
                ") RETURNING id, type, biz_id"
            ),
            {"limit": _CLAIM_LIMIT},
        ).mappings().all()
    return [(row["id"], row["type"], row["biz_id"]) for row in rows]


def _requeue_failed(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE notification_events SET status='pending' "
                f"WHERE status='failed' AND created_at > now() - interval '{_RETRY_WINDOW}'"
            )
        )


def _requeue_failed_deliveries(engine: Engine) -> None:
    """Re-open failed candidate deliveries inside the retry window."""

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE notification_deliveries SET status='queued',next_retry_at=NULL "
                f"WHERE status='failed' AND created_at > now() - interval '{_RETRY_WINDOW}'"
            )
        )


def _mark(engine: Engine, event_id: UUID, status: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE notification_events SET status=:status WHERE id=:id"),
            {"id": event_id, "status": status},
        )


def _process(
    engine: Engine,
    booking: BookingService,
    auth_repo: AuthRepository,
    sender: EmailSender,
    event_id: UUID,
    event_type: str,
    biz_id: UUID,
) -> None:
    with engine.connect() as connection:
        owner_id = connection.execute(
            text("SELECT user_id FROM appointments WHERE id=:id"), {"id": biz_id}
        ).scalar()
    if owner_id is None:
        raise ValueError(f"appointment {biz_id} has no owner")
    owner_email = auth_repo.find_email_by_user_id(owner_id)
    if not owner_email:
        raise ValueError(f"no email for owner {owner_id}")
    appointment = booking.get_notification_appointment(biz_id)
    if appointment is None:
        raise ValueError(f"appointment {biz_id} not found")
    subject, body = render(event_type, appointment, owner_email)
    sender.send(owner_email, subject, body)
    LOGGER.info("notification_sent", extra={"event_id": str(event_id), "type": event_type})


# ---------------------------------------------------------------------------
# Candidate-side dual-channel deliveries (R13 reminders + R14 Feishu mirror)
# ---------------------------------------------------------------------------


def _find_active_owner_admin(engine: Engine) -> dict[str, object] | None:
    """Resolve the unique active owner_admin (uq_active_owner_admin invariant)."""

    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT u.id,u.email,o.id AS config_id,"
                "o.candidate_feishu_open_id_ciphertext "
                "FROM users u LEFT JOIN owner_contact_configs o ON o.user_id=u.id "
                "WHERE u.role='owner_admin' AND u.deleted_at IS NULL"
            ),
        ).mappings().one_or_none()
    return dict(row) if row else None


def _decrypt_open_id(
    cipher: FieldCipher | None, config_id: object, envelope: object
) -> str | None:
    if cipher is None or not isinstance(config_id, UUID) or not isinstance(envelope, bytes):
        return None
    try:
        return cipher.decrypt(
            envelope, "owner_contact_configs", "candidate_feishu_open_id_ciphertext", config_id
        )
    except Exception:
        LOGGER.exception("candidate_open_id_decrypt_failed", extra={"config_id": str(config_id)})
        return None


def _build_field_cipher(settings: Settings) -> FieldCipher | None:
    """Build the field cipher for owner-contact decryption, or None when unset."""

    if not settings.field_encryption_current_key_id or not settings.field_encryption_keys:
        return None
    try:
        key_ring = json.loads(settings.field_encryption_keys.get_secret_value())
    except json.JSONDecodeError:
        return None
    if not isinstance(key_ring, dict):
        return None
    try:
        return FieldCipher(settings.field_encryption_current_key_id, key_ring)
    except ValueError:
        return None


def _materialize_candidate_deliveries(
    engine: Engine, event_id: UUID, now: datetime, channels: tuple[str, ...]
) -> list[tuple[UUID, str]]:
    """Insert candidate delivery rows for a candidate event (only configured channels).

    Idempotent via ``uq_delivery_attempt``: re-running the same event (retry/restart)
    does not create duplicate attempt rows. Returns ``(delivery_id, channel)``.
    """

    rows: list[tuple[UUID, str]] = []
    with engine.begin() as connection:
        for channel in channels:
            delivery_id = uuid4()
            connection.execute(
                text(
                    "INSERT INTO notification_deliveries "
                    "(id,event_id,delivery_purpose,channel,event_version,attempt_no,"
                    "status,channel_metadata,created_at) "
                    "VALUES (:id,:event_id,'candidate_notification',:channel,1,1,"
                    "'queued','{}',:now) "
                    "ON CONFLICT (event_id,delivery_purpose,channel,event_version,attempt_no) "
                    "DO NOTHING"
                ),
                {
                    "id": delivery_id,
                    "event_id": event_id,
                    "channel": channel,
                    "now": now,
                },
            )
            exists = connection.execute(
                text(
                    "SELECT id FROM notification_deliveries "
                    "WHERE event_id=:event_id AND delivery_purpose='candidate_notification' "
                    "AND channel=:channel AND event_version=1 AND attempt_no=1"
                ),
                {"event_id": event_id, "channel": channel},
            ).scalar()
            if exists is not None:
                rows.append((exists, channel))
    return rows


def _mark_delivery(
    engine: Engine,
    delivery_id: UUID,
    status: str,
    *,
    provider_id: str | None = None,
    error: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE notification_deliveries SET status=:status,provider_message_id=:pid,"
                "last_error=:error,channel_metadata=:metadata,next_retry_at=NULL WHERE id=:id"
            ),
            {
                "id": delivery_id,
                "status": status,
                "pid": provider_id,
                "error": error,
                "metadata": json.dumps(metadata or {}, sort_keys=True),
            },
        )


def _send_candidate_email(
    engine: Engine,
    email_sender: EmailSender,
    delivery_id: UUID,
    event_type: str,
    appt: Appointment,
    owner_admin: dict[str, object],
) -> None:
    try:
        _mark_delivery(engine, delivery_id, "sending")
        subject, body = render_candidate_notification(event_type, appt)
        email_sender.send(str(owner_admin["email"]), subject, body)
        _mark_delivery(engine, delivery_id, "succeeded")
        LOGGER.info(
            "candidate_email_sent",
            extra={"delivery_id": str(delivery_id), "type": event_type},
        )
    except Exception as error:
        _mark_delivery(engine, delivery_id, "failed", error=str(error))
        LOGGER.exception(
            "candidate_email_failed", extra={"delivery_id": str(delivery_id), "type": event_type}
        )


def _send_candidate_feishu(
    engine: Engine,
    feishu: FeishuGateway,
    cipher: FieldCipher | None,
    alert_email_sender: EmailSender,
    delivery_id: UUID,
    event_type: str,
    appt: Appointment,
    owner_admin: dict[str, object],
) -> None:
    _mark_delivery(engine, delivery_id, "sending")
    mirror_record_id: str | None = None
    message_id: str | None = None
    error_text: str | None = None
    try:
        mirror_record_id = feishu.upsert_bitable_row(appt, None)  # R14 mirror
    except Exception as error:
        error_text = f"bitable: {error}"

    open_id = _decrypt_open_id(
        cipher,
        owner_admin.get("config_id"),
        owner_admin.get("candidate_feishu_open_id_ciphertext"),
    )
    if error_text is None and open_id:  # R13 message only when mirror succeeded
        try:
            _subject, body = render_candidate_notification(event_type, appt)
            message_id = feishu.send_message(open_id, body)
        except Exception as error:
            error_text = f"message: {error}"

    if error_text is None:
        _mark_delivery(
            engine,
            delivery_id,
            "succeeded",
            provider_id=message_id,
            metadata={"feishu_record_id": mirror_record_id, "open_id_configured": bool(open_id)},
        )
        LOGGER.info(
            "candidate_feishu_sent",
            extra={"delivery_id": str(delivery_id), "record_id": mirror_record_id},
        )
    else:
        _mark_delivery(engine, delivery_id, "failed", error=error_text)
        LOGGER.error(
            "candidate_feishu_failed",
            extra={"delivery_id": str(delivery_id), "error": error_text},
        )
        _alert_sync_fail(engine, alert_email_sender, appt, error_text)


def _alert_sync_fail(
    engine: Engine, email_sender: EmailSender, appt: Appointment, error: str
) -> None:
    owner_admin = _find_active_owner_admin(engine)
    if owner_admin is None:
        return
    try:
        subject, body = render_sync_fail_email(appt, error)
        email_sender.send(str(owner_admin["email"]), subject, body)
    except Exception:
        LOGGER.exception("feishu_sync_fail_alert_failed")


def _deliver_candidate(
    engine: Engine,
    booking: BookingService,
    email_sender: EmailSender,
    feishu: FeishuGateway | None,
    cipher: FieldCipher | None,
    event_id: UUID,
    event_type: str,
    biz_id: UUID,
    now: datetime,
) -> None:
    """Deliver all candidate rows for one event; each channel fails independently."""

    owner_admin = _find_active_owner_admin(engine)
    if owner_admin is None:
        LOGGER.error(
            "no_active_owner_admin_for_candidate_notification",
            extra={"event_id": str(event_id), "type": event_type},
        )
        return

    appointment = booking.get_notification_appointment(biz_id)
    if appointment is None:
        return

    channels: tuple[str, ...] = ("email",) if feishu is None else ("email", "feishu")
    for delivery_id, channel in _materialize_candidate_deliveries(
        engine, event_id, now, channels
    ):
        if channel == "email":
            _send_candidate_email(
                engine, email_sender, delivery_id, event_type, appointment, owner_admin
            )
        else:
            _send_candidate_feishu(
                engine,
                feishu,  # type: ignore[arg-type]  # feishu is not None when channel='feishu'
                cipher,
                email_sender,
                delivery_id,
                event_type,
                appointment,
                owner_admin,
            )


def run_notification_worker(
    settings: Settings,
    engine: Engine,
    booking: BookingService,
    auth_repo: AuthRepository,
    stop_event: Event | None = None,
) -> int:
    email_sender = EmailSender(settings)
    feishu: FeishuGateway | None = (
        FeishuAPIGateway(settings) if settings.feishu_configured else None
    )
    cipher = _build_field_cipher(settings)
    LOGGER.info("feishu_channel_configured" if feishu else "feishu_channel_disabled")
    LOGGER.info("notification_worker_started")
    while not (stop_event and stop_event.is_set()):
        claimed = _claim_batch(engine)
        for event_id, event_type, biz_id in claimed:
            try:
                _process(engine, booking, auth_repo, email_sender, event_id, event_type, biz_id)
                _mark(engine, event_id, "processed")
            except Exception:  # one bad event must not kill the worker
                LOGGER.exception("notification_failed", extra={"event_id": str(event_id)})
                _mark(engine, event_id, "failed")
            if event_type in _CANDIDATE_EVENTS:
                try:
                    _deliver_candidate(
                        engine,
                        booking,
                        email_sender,
                        feishu,
                        cipher,
                        event_id,
                        event_type,
                        biz_id,
                        datetime.now(UTC),
                    )
                except Exception:  # candidate delivery must never kill the worker either
                    LOGGER.exception(
                        "candidate_delivery_failed", extra={"event_id": str(event_id)}
                    )
        _requeue_failed(engine)
        _requeue_failed_deliveries(engine)
        time.sleep(_POLL_INTERVAL)
    LOGGER.info("notification_worker_stopped")
    return 0


async def run_notification_worker_async(
    settings: Settings,
    engine: Engine,
    booking: BookingService,
    auth_repo: AuthRepository,
    stop_event: Event | None = None,
) -> int:
    """Async wrapper so the worker can be hosted alongside the API if desired."""

    return await asyncio.to_thread(
        run_notification_worker, settings, engine, booking, auth_repo, stop_event
    )
