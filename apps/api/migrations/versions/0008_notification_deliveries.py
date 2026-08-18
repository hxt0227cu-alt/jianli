"""Create the approved NotificationDelivery attempt-history table (domain model §6.12).

Adds ``notification_deliveries``: one row per (event, delivery_purpose, channel,
event_version, attempt_no) with a per-attempt status machine (queued -> sending ->
succeeded / failed / retry_scheduled / dead_letter). The unique index
``uq_delivery_attempt`` prevents duplicate rows from concurrent consumers while
allowing multiple purposes per event and multiple attempts per delivery.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_notification_deliveries"
down_revision: str | Sequence[str] | None = "0007_embedding_1024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enums() -> tuple[postgresql.ENUM, postgresql.ENUM, postgresql.ENUM]:
    bind = op.get_bind()
    definitions = (
        (
            "delivery_purpose",
            (
                "candidate_notification",
                "interviewer_confirmation",
                "interviewer_cancellation",
            ),
        ),
        ("delivery_channel", ("feishu", "email")),
        (
            "delivery_status",
            ("queued", "sending", "succeeded", "failed", "retry_scheduled", "dead_letter"),
        ),
    )
    for name, labels in definitions:
        postgresql.ENUM(*labels, name=name).create(bind, checkfirst=True)
    return tuple(
        postgresql.ENUM(*labels, name=name, create_type=False) for name, labels in definitions
    )  # type: ignore[return-value]


def upgrade() -> None:
    purpose, channel, status = _create_enums()
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "event_id",
            sa.Uuid(),
            sa.ForeignKey("notification_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delivery_purpose", purpose, nullable=False),
        sa.Column("channel", channel, nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("channel_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("provider_message_id", sa.Text()),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "uq_delivery_attempt",
        "notification_deliveries",
        ["event_id", "delivery_purpose", "channel", "event_version", "attempt_no"],
        unique=True,
    )
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("uq_delivery_attempt", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    for name in ("delivery_status", "delivery_channel", "delivery_purpose"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
