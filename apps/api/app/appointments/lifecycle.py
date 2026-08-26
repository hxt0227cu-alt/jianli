"""Idempotent maintenance for appointment terminal-state transitions."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Connection, text


def complete_expired_appointments(
    connection: Connection,
    *,
    now: datetime,
    user_id: UUID | None = None,
) -> int:
    """Complete active appointments whose reserved interval has ended.

    The CTE also writes one completion Outbox event per appointment and cancels an
    unconsumed reminder. Completion is a lifecycle transition, not a user or owner
    cancellation, so no appointment-cancelled event is created.
    """

    user_filter = " AND user_id=:user_id" if user_id is not None else ""
    completed = connection.execute(
        text(
            "WITH completed AS ("
            "UPDATE appointments SET status='completed',completed_at=end_at,version=version+1 "
            "WHERE status='active' AND end_at<=:now"
            f"{user_filter} RETURNING id"
            "), completion_events AS ("
            "INSERT INTO notification_events "
            "(id,type,biz_id,scheduled_at,idempotency_key,status,created_at) "
            "SELECT gen_random_uuid(),'appointment_completed',id,NULL,"
            "'appointment:' || id::text || chr(58) || 'appointment_completed','pending',:now "
            "FROM completed ON CONFLICT (idempotency_key) DO NOTHING RETURNING biz_id"
            "), cancelled_reminders AS ("
            "UPDATE notification_events AS event SET status='cancelled',cancelled_at=:now "
            "FROM completed WHERE event.biz_id=completed.id "
            "AND event.type='reminder_due' AND event.status='pending' RETURNING event.id"
            ") SELECT count(*) FROM completed"
        ),
        {"now": now, "user_id": user_id},
    ).scalar_one()
    return int(completed)
