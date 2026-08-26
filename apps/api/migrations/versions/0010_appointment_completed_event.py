"""Add the appointment-completed lifecycle event to the existing Outbox enum."""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_appointment_completed_event"
down_revision: str | Sequence[str] | None = "0009_aiqa_observations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_LABELS = (
    "appointment_created",
    "appointment_details_updated",
    "appointment_rescheduled",
    "appointment_cancelled",
    "reminder_due",
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE notification_event_type "
            "ADD VALUE IF NOT EXISTS 'appointment_completed'"
        )


def downgrade() -> None:
    op.execute("DELETE FROM notification_events WHERE type='appointment_completed'")
    op.drop_index("ix_notification_events_pending_schedule", table_name="notification_events")
    op.execute(
        "ALTER TABLE notification_events ALTER COLUMN type TYPE text USING type::text"
    )
    op.execute("DROP TYPE notification_event_type")
    labels = ",".join(f"'{label}'" for label in _OLD_LABELS)
    op.execute(f"CREATE TYPE notification_event_type AS ENUM ({labels})")
    op.execute(
        "ALTER TABLE notification_events ALTER COLUMN type "
        "TYPE notification_event_type USING type::notification_event_type"
    )
    op.create_index(
        "ix_notification_events_pending_schedule",
        "notification_events",
        ["scheduled_at"],
        postgresql_where="type = 'reminder_due' AND status = 'pending'",
    )
