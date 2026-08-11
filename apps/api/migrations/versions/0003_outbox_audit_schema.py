"""Create the approved notification event and audit log schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_outbox_audit_schema"
down_revision: str | Sequence[str] | None = "0002_booking_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enums() -> tuple[postgresql.ENUM, postgresql.ENUM]:
    bind = op.get_bind()
    definitions = (
        (
            "notification_event_type",
            (
                "appointment_created",
                "appointment_details_updated",
                "appointment_rescheduled",
                "appointment_cancelled",
                "reminder_due",
            ),
        ),
        (
            "notification_event_status",
            ("pending", "processing", "processed", "cancelled", "failed"),
        ),
    )
    for name, labels in definitions:
        postgresql.ENUM(*labels, name=name).create(bind, checkfirst=True)
    return tuple(
        postgresql.ENUM(*labels, name=name, create_type=False) for name, labels in definitions
    )  # type: ignore[return-value]


def upgrade() -> None:
    event_type, event_status = _create_enums()
    op.create_table(
        "notification_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("type", event_type, nullable=False),
        sa.Column("biz_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("status", event_status, nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_by_event_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_notification_events_idempotency_key"),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target", sa.Text(), nullable=False),
        sa.Column("masked_detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_events_biz_id", "notification_events", ["biz_id"])
    op.create_index(
        "ix_notification_events_pending_schedule",
        "notification_events",
        ["scheduled_at"],
        postgresql_where=sa.text("type = 'reminder_due' AND status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_notification_events_pending_schedule", table_name="notification_events")
    op.drop_index("ix_notification_events_biz_id", table_name="notification_events")
    op.drop_table("notification_events")
    for name in ("notification_event_status", "notification_event_type"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
