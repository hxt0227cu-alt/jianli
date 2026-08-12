"""Notification Outbox consumer (M3).

Polls ``notification_events`` (pending, due) and sends email via the runtime SMTP
channel. Delivery is at-least-once: events are claimed with ``FOR UPDATE SKIP LOCKED``
and marked ``processed`` / ``failed``; ``failed`` events within a 10-minute window are
re-queued for retry. A dedicated ``notification_deliveries`` attempt-history table
(domain model v1.1.5) is deferred to keep the schema surface minimal for this drop;
the status machine already provides attempt semantics.

Feishu (candidate-facing) is skipped: no Feishu credentials are configured here.
"""

from __future__ import annotations

import asyncio
import logging
import time
from threading import Event
from uuid import UUID

from sqlalchemy import Engine, text

from app.appointments.service import BookingService
from app.auth.repository import AuthRepository
from app.config import Settings

from .email import EmailSender, render

LOGGER = logging.getLogger("jianli.notifications")
_POLL_INTERVAL = 2.0
_CLAIM_LIMIT = 20
_RETRY_WINDOW = "10 minutes"


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


def run_notification_worker(
    settings: Settings,
    engine: Engine,
    booking: BookingService,
    auth_repo: AuthRepository,
    stop_event: Event | None = None,
) -> int:
    sender = EmailSender(settings)
    LOGGER.info("notification_worker_started")
    while not (stop_event and stop_event.is_set()):
        claimed = _claim_batch(engine)
        for event_id, event_type, biz_id in claimed:
            try:
                _process(engine, booking, auth_repo, sender, event_id, event_type, biz_id)
                _mark(engine, event_id, "processed")
            except Exception:  # one bad event must not kill the worker
                LOGGER.exception("notification_failed", extra={"event_id": str(event_id)})
                _mark(engine, event_id, "failed")
        if claimed:
            _requeue_failed(engine)
        else:
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
