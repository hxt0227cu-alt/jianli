"""Add objective AI QA observations to conversation messages.

The columns are nullable so historical and user messages remain valid.  Only
non-negative citation counts and server-side latencies are accepted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_aiqa_observations"
down_revision: str | Sequence[str] | None = "0008_notification_deliveries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("conversation_messages", sa.Column("grounded", sa.Boolean()))
    op.add_column("conversation_messages", sa.Column("citations_count", sa.Integer()))
    op.add_column("conversation_messages", sa.Column("latency_ms", sa.Integer()))
    op.create_check_constraint(
        "ck_conversation_messages_citations_count_nonnegative",
        "conversation_messages",
        "citations_count IS NULL OR citations_count >= 0",
    )
    op.create_check_constraint(
        "ck_conversation_messages_latency_ms_nonnegative",
        "conversation_messages",
        "latency_ms IS NULL OR latency_ms >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_conversation_messages_latency_ms_nonnegative",
        "conversation_messages",
        type_="check",
    )
    op.drop_constraint(
        "ck_conversation_messages_citations_count_nonnegative",
        "conversation_messages",
        type_="check",
    )
    op.drop_column("conversation_messages", "latency_ms")
    op.drop_column("conversation_messages", "citations_count")
    op.drop_column("conversation_messages", "grounded")
