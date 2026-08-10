"""Create the approved identity-domain schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_identity_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    role_for_ddl = postgresql.ENUM("interviewer", "owner_admin", name="user_role")
    role_for_ddl.create(op.get_bind(), checkfirst=True)
    role = postgresql.ENUM("interviewer", "owner_admin", name="user_role", create_type=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("purge_after", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(
        "uq_active_owner_admin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'owner_admin' AND deleted_at IS NULL"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("device", sa.Text()),
        sa.Column("ip", postgresql.INET()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_table(
        "interviewer_profiles",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("display_name", sa.Text()),
    )
    op.create_table(
        "owner_contact_configs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("candidate_phone_ciphertext", sa.LargeBinary()),
        sa.Column("candidate_feishu_open_id_ciphertext", sa.LargeBinary()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_owner_contact_configs_user_id"),
    )
    for table in ("email_verification_tokens", "password_reset_tokens"):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True)),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def downgrade() -> None:
    for table in ("password_reset_tokens", "email_verification_tokens"):
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_table(table)
    op.drop_table("owner_contact_configs")
    op.drop_table("interviewer_profiles")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("uq_active_owner_admin", table_name="users")
    op.drop_table("users")
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
