from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError, IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
OUTBOX_TABLES = {"notification_events", "audit_logs"}
BOOKING_TABLES = {
    "companies",
    "company_booking_exceptions",
    "appointments",
    "appointment_slots",
    "availability_overrides",
}
NOW = datetime(2026, 8, 12, 9, tzinfo=UTC)


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
def outbox_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_ops_002_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config, engine = _config(), create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= OUTBOX_TABLES | BOOKING_TABLES
        with engine.begin() as connection:
            company_id = uuid4()
            connection.execute(
                text("INSERT INTO companies VALUES (:id,:fingerprint,:ciphertext)"),
                {
                    "id": company_id,
                    "fingerprint": f"preserved-db003-{company_id}",
                    "ciphertext": b"ciphertext",
                },
            )
        command.downgrade(config, "0002_booking_schema")
        assert OUTBOX_TABLES.isdisjoint(inspect(engine).get_table_names())
        assert set(inspect(engine).get_table_names()) >= BOOKING_TABLES
        with engine.begin() as connection:
            assert connection.scalar(
                text("SELECT count(*) FROM companies WHERE id=:id"), {"id": company_id}
            )
            connection.execute(text("DELETE FROM companies WHERE id=:id"), {"id": company_id})
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


@pytest.fixture(autouse=True)
def clean_data(outbox_engine: Engine) -> Iterator[None]:
    yield
    with outbox_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE notification_events, audit_logs"))


def _shape(engine: Engine, table: str) -> dict[str, tuple[str, bool]]:
    def type_name(column: Any) -> str:
        name = type(column["type"]).__name__.lower()
        return "timestamptz" if name == "timestamp" and column["type"].timezone else name

    return {
        column["name"]: (type_name(column), column["nullable"])
        for column in inspect(engine).get_columns(table)
    }


def test_outbox_audit_schema_shape(outbox_engine: Engine) -> None:
    inspector = inspect(outbox_engine)
    assert _shape(outbox_engine, "notification_events") == {
        "id": ("uuid", False),
        "type": ("enum", False),
        "biz_id": ("uuid", False),
        "scheduled_at": ("timestamptz", True),
        "idempotency_key": ("text", False),
        "status": ("enum", False),
        "cancelled_at": ("timestamptz", True),
        "superseded_by_event_id": ("uuid", True),
        "created_at": ("timestamptz", False),
    }
    assert _shape(outbox_engine, "audit_logs") == {
        "id": ("uuid", False),
        "actor": ("text", False),
        "action": ("text", False),
        "target": ("text", False),
        "masked_detail": ("text", False),
        "created_at": ("timestamptz", False),
    }
    assert _enum_labels(outbox_engine, "notification_event_type") == [
        "appointment_created",
        "appointment_details_updated",
        "appointment_rescheduled",
        "appointment_cancelled",
        "reminder_due",
    ]
    assert _enum_labels(outbox_engine, "notification_event_status") == [
        "pending",
        "processing",
        "processed",
        "cancelled",
        "failed",
    ]
    indexes = {item["name"]: item for item in inspector.get_indexes("notification_events")}
    assert set(indexes) == {
        "ix_notification_events_biz_id",
        "ix_notification_events_pending_schedule",
        "uq_notification_events_idempotency_key",
    }
    assert indexes["ix_notification_events_biz_id"]["column_names"] == ["biz_id"]
    pending = indexes["ix_notification_events_pending_schedule"]
    assert pending["column_names"] == ["scheduled_at"]
    predicate = str(pending["dialect_options"]["postgresql_where"])
    assert "type = 'reminder_due'" in predicate
    assert "status = 'pending'" in predicate
    assert not inspector.get_foreign_keys("notification_events")
    assert not inspector.get_foreign_keys("audit_logs")


def _insert_event(connection: Any, key: str, event_type: str = "appointment_created") -> None:
    connection.execute(
        text(
            "INSERT INTO notification_events "
            "(id,type,biz_id,idempotency_key,status,created_at) "
            "VALUES (:id,:type,:biz_id,:key,'pending',:created_at)"
        ),
        {
            "id": uuid4(),
            "type": event_type,
            "biz_id": uuid4(),
            "key": key,
            "created_at": NOW,
        },
    )


def test_event_constraints(outbox_engine: Engine) -> None:
    with outbox_engine.begin() as connection:
        _insert_event(connection, "same-key")
    with pytest.raises(IntegrityError), outbox_engine.begin() as connection:
        _insert_event(connection, "same-key")
    with pytest.raises(DBAPIError), outbox_engine.begin() as connection:
        _insert_event(connection, "invalid-type", "invalid")
    with pytest.raises(DBAPIError), outbox_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO notification_events "
                "(id,type,biz_id,idempotency_key,status,created_at) "
                "VALUES (:id,'reminder_due',:biz_id,'invalid-status','invalid',:created_at)"
            ),
            {"id": uuid4(), "biz_id": uuid4(), "created_at": NOW},
        )


def test_audit_requires_masked_detail(outbox_engine: Engine) -> None:
    with pytest.raises(IntegrityError), outbox_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO audit_logs (id,actor,action,target,created_at) "
                "VALUES (:id,'user:test','appointment.created','appointment:test',:created_at)"
            ),
            {"id": uuid4(), "created_at": NOW},
        )


def test_repeat_upgrade_preserves_data(outbox_engine: Engine) -> None:
    with outbox_engine.begin() as connection:
        _insert_event(connection, "preserved")
    command.upgrade(_config(), "head")
    with outbox_engine.connect() as connection:
        assert connection.scalar(
            text("SELECT count(*) FROM notification_events WHERE idempotency_key='preserved'")
        )
