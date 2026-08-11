"""Create the approved booking-domain core schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_booking_schema"
down_revision: str | Sequence[str] | None = "0001_identity_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enums() -> tuple[postgresql.ENUM, postgresql.ENUM, postgresql.ENUM]:
    bind = op.get_bind()
    definitions = (
        ("appointment_status", ("active", "cancelled", "completed")),
        ("slot_status", ("available", "booked", "owner_locked", "unavailable")),
        ("availability_override_action", ("force_unavailable", "force_available")),
    )
    for name, labels in definitions:
        postgresql.ENUM(*labels, name=name).create(bind, checkfirst=True)
    return tuple(
        postgresql.ENUM(*labels, name=name, create_type=False) for name, labels in definitions
    )  # type: ignore[return-value]


def upgrade() -> None:
    appointment_status, slot_status, override_action = _create_enums()
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("normalized_name_fingerprint", sa.Text(), nullable=False),
        sa.Column("raw_name_ciphertext", sa.LargeBinary(), nullable=False),
        sa.UniqueConstraint(
            "normalized_name_fingerprint", name="uq_companies_normalized_name_fingerprint"
        ),
    )
    op.create_table(
        "company_booking_exceptions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("interviewer_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_fingerprint", sa.Text(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column(
            "dedupe_exception_id",
            sa.Uuid(),
            sa.ForeignKey("company_booking_exceptions.id"),
        ),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("company_name_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("company_name_fingerprint", sa.Text(), nullable=False),
        sa.Column("meeting_platform_ciphertext", sa.LargeBinary()),
        sa.Column("meeting_number_ciphertext", sa.LargeBinary()),
        sa.Column("contact_ciphertext", sa.LargeBinary()),
        sa.Column("notes_ciphertext", sa.LargeBinary()),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("purge_after", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", slot_status, nullable=False),
        sa.Column("appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("start_at", "end_at", name="uq_slot_unique"),
        sa.CheckConstraint("end_at = start_at + interval '30 minutes'", name="ck_slot_duration"),
    )
    op.create_table(
        "availability_overrides",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action", override_action, nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("end_at > start_at", name="ck_availability_override_range"),
    )

    op.create_index(
        "uq_exception_open",
        "company_booking_exceptions",
        ["interviewer_user_id", "company_fingerprint"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL"),
    )
    op.create_index(
        "uq_active_company",
        "appointments",
        ["company_name_fingerprint"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND dedupe_exception_id IS NULL"),
    )
    op.create_index(
        "uq_active_user",
        "appointments",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "uq_appointment_exception",
        "appointments",
        ["dedupe_exception_id"],
        unique=True,
        postgresql_where=sa.text("dedupe_exception_id IS NOT NULL"),
    )
    for name, table, columns in (
        ("ix_appointments_user_id", "appointments", ["user_id"]),
        ("ix_appointments_company_id", "appointments", ["company_id"]),
        ("ix_appointment_slots_appointment_id", "appointment_slots", ["appointment_id"]),
        (
            "ix_company_booking_exceptions_interviewer_user_id",
            "company_booking_exceptions",
            ["interviewer_user_id"],
        ),
        ("ix_availability_overrides_created_by", "availability_overrides", ["created_by"]),
    ):
        op.create_index(name, table, columns)


def downgrade() -> None:
    op.drop_index("ix_availability_overrides_created_by", table_name="availability_overrides")
    op.drop_table("availability_overrides")
    op.drop_index("ix_appointment_slots_appointment_id", table_name="appointment_slots")
    op.drop_table("appointment_slots")
    for name in (
        "ix_appointments_company_id",
        "ix_appointments_user_id",
        "uq_appointment_exception",
        "uq_active_user",
        "uq_active_company",
    ):
        op.drop_index(name, table_name="appointments")
    op.drop_table("appointments")
    op.drop_index(
        "ix_company_booking_exceptions_interviewer_user_id",
        table_name="company_booking_exceptions",
    )
    op.drop_index("uq_exception_open", table_name="company_booking_exceptions")
    op.drop_table("company_booking_exceptions")
    op.drop_table("companies")
    for name in ("availability_override_action", "slot_status", "appointment_status"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
