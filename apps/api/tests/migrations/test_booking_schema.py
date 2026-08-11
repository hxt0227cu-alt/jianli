from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
# fmt: off
BOOKING_TABLES = {
    "companies", "company_booking_exceptions", "appointments", "appointment_slots",
    "availability_overrides",
}
IDENTITY_TABLES = {
    "users", "auth_sessions", "interviewer_profiles", "owner_contact_configs",
    "email_verification_tokens", "password_reset_tokens",
}
# fmt: on


def _config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    return config


def _enum_labels(engine: Engine, name: str) -> list[str]:
    query = (
        "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid "
        "WHERE t.typname=:name ORDER BY e.enumsortorder"
    )
    with engine.connect() as connection:
        return list(connection.scalars(text(query), {"name": name}))


@pytest.fixture(scope="session")
def booking_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_ops_002_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config, engine = _config(), create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= BOOKING_TABLES
        with engine.begin() as connection:
            user_id = uuid4()
            connection.execute(
                text(
                    "INSERT INTO users VALUES (:id,:email,'hash','interviewer',true,NULL,NULL,NULL)"
                ),
                {"id": user_id, "email": f"baseline-{user_id}@example.invalid"},
            )
        command.downgrade(config, "0001_identity_schema")
        assert BOOKING_TABLES.isdisjoint(inspect(engine).get_table_names())
        assert set(inspect(engine).get_table_names()) >= IDENTITY_TABLES
        with engine.connect() as connection:
            assert connection.scalar(
                text("SELECT count(*) FROM users WHERE id=:id"), {"id": user_id}
            )
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


@pytest.fixture(autouse=True)
def clean_data(booking_engine: Engine) -> Iterator[None]:
    yield
    with booking_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))
        connection.execute(text("TRUNCATE TABLE companies CASCADE"))


def _shape(engine: Engine, table: str) -> dict[str, tuple[str, bool]]:
    def type_name(column: Any) -> str:
        name = type(column["type"]).__name__.lower()
        return "timestamptz" if name == "timestamp" and column["type"].timezone else name

    return {
        column["name"]: (type_name(column), column["nullable"])
        for column in inspect(engine).get_columns(table)
    }


def _expected(required: str, nullable: str = "") -> dict[str, tuple[str, bool]]:
    result = {name: (kind, False) for name, kind in (item.split(":") for item in required.split())}
    result.update(
        {name: (kind, True) for name, kind in (item.split(":") for item in nullable.split())}
    )
    return result


# fmt: off
EXPECTED_SHAPES = {
    "companies": _expected("id:uuid normalized_name_fingerprint:text raw_name_ciphertext:bytea"),
    "company_booking_exceptions": _expected(
        "id:uuid interviewer_user_id:uuid company_fingerprint:text approved_by:uuid "
        "reason:text expires_at:timestamptz created_at:timestamptz",
        "consumed_at:timestamptz revoked_at:timestamptz revoked_by:uuid",
    ),
    "appointments": _expected(
        "id:uuid user_id:uuid company_id:uuid start_at:timestamptz end_at:timestamptz "
        "status:enum company_name_ciphertext:bytea company_name_fingerprint:text "
        "version:integer created_at:timestamptz",
        "dedupe_exception_id:uuid meeting_platform_ciphertext:bytea "
        "meeting_number_ciphertext:bytea contact_ciphertext:bytea notes_ciphertext:bytea "
        "cancelled_at:timestamptz completed_at:timestamptz deleted_at:timestamptz "
        "purge_after:timestamptz",
    ),
    "appointment_slots": _expected(
        "id:uuid start_at:timestamptz end_at:timestamptz status:enum version:integer",
        "appointment_id:uuid",
    ),
    "availability_overrides": _expected(
        "id:uuid start_at:timestamptz end_at:timestamptz action:enum created_by:uuid "
        "created_at:timestamptz",
        "reason:text",
    ),
}
# fmt: on


def test_booking_schema_shape(booking_engine: Engine) -> None:
    inspector = inspect(booking_engine)
    assert set(inspector.get_table_names()) >= BOOKING_TABLES
    assert _enum_labels(booking_engine, "appointment_status") == [
        "active",
        "cancelled",
        "completed",
    ]
    assert _enum_labels(booking_engine, "slot_status") == [
        "available",
        "booked",
        "owner_locked",
        "unavailable",
    ]
    assert _enum_labels(booking_engine, "availability_override_action") == [
        "force_unavailable",
        "force_available",
    ]
    for table, expected in EXPECTED_SHAPES.items():
        assert _shape(booking_engine, table) == expected

    # fmt: off
    expected_indexes = {
        "companies": {"uq_companies_normalized_name_fingerprint"},
        "company_booking_exceptions": {
            "ix_company_booking_exceptions_interviewer_user_id", "uq_exception_open"},
        "appointments": {
            "ix_appointments_company_id", "ix_appointments_user_id", "uq_active_company",
            "uq_active_user", "uq_appointment_exception"},
        "appointment_slots": {"ix_appointment_slots_appointment_id", "uq_slot_unique"},
        "availability_overrides": {"ix_availability_overrides_created_by"},
    }
    expected_fks = {
        "companies": {},
        "company_booking_exceptions": {"interviewer_user_id": "users"},
        "appointments": {
            "user_id": "users", "company_id": "companies",
            "dedupe_exception_id": "company_booking_exceptions"},
        "appointment_slots": {"appointment_id": "appointments"},
        "availability_overrides": {"created_by": "users"},
    }
    # fmt: on
    for table, names in expected_indexes.items():
        assert {item["name"] for item in inspector.get_indexes(table)} == names
    for table, expected in expected_fks.items():
        actual = {
            fk["constrained_columns"][0]: fk["referred_table"]
            for fk in inspector.get_foreign_keys(table)
        }
        assert actual == expected

    def checks(table: str) -> set[str]:
        return {c["name"] for c in inspector.get_check_constraints(table)}

    assert checks("appointment_slots") == {"ck_slot_duration"}
    assert checks("availability_overrides") == {"ck_availability_override_range"}


def test_repeat_upgrade_preserves_data(booking_engine: Engine) -> None:
    with booking_engine.begin() as connection:
        company_id = uuid4()
        connection.execute(
            text("INSERT INTO companies VALUES (:id,'preserved',:ciphertext)"),
            {"id": company_id, "ciphertext": b"ciphertext"},
        )
    command.upgrade(_config(), "head")
    with booking_engine.connect() as connection:
        assert connection.scalar(
            text("SELECT count(*) FROM companies WHERE id=:id"), {"id": company_id}
        )
