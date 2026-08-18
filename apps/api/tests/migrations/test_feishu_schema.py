"""Migration 0008: notification_deliveries schema + unique attempt key."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 18, 9, tzinfo=UTC)


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
def delivery_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_feishu_001_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config, engine = _config(), create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        yield engine
        command.downgrade(config, "0007_embedding_1024")
        command.upgrade(config, "head")
    finally:
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url
        engine.dispose()


def test_deliveries_table_columns(delivery_engine: Engine) -> None:
    columns = {
        column["name"]: column
        for column in inspect(delivery_engine).get_columns("notification_deliveries")
    }
    expected = {
        "id",
        "event_id",
        "delivery_purpose",
        "channel",
        "event_version",
        "attempt_no",
        "status",
        "channel_metadata",
        "provider_message_id",
        "next_retry_at",
        "last_error",
        "created_at",
    }
    assert set(columns) == expected
    assert columns["event_id"]["nullable"] is False
    assert columns["channel_metadata"]["nullable"] is False


def test_deliveries_enums(delivery_engine: Engine) -> None:
    assert _enum_labels(delivery_engine, "delivery_purpose") == [
        "candidate_notification",
        "interviewer_confirmation",
        "interviewer_cancellation",
    ]
    assert _enum_labels(delivery_engine, "delivery_channel") == ["feishu", "email"]
    assert _enum_labels(delivery_engine, "delivery_status") == [
        "queued",
        "sending",
        "succeeded",
        "failed",
        "retry_scheduled",
        "dead_letter",
    ]


def test_unique_delivery_attempt_index(delivery_engine: Engine) -> None:
    indexes = {
        index["name"]
        for index in inspect(delivery_engine).get_indexes("notification_deliveries")
    }
    assert "uq_delivery_attempt" in indexes
    assert "ix_notification_deliveries_status" in indexes

    # Two rows with the same (event, purpose, channel, version, attempt) must collide.
    event_id = uuid4()
    with delivery_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO notification_events "
                "(id,type,biz_id,idempotency_key,status,created_at) "
                "VALUES (:id,'appointment_created',:biz,:key,'processed',:now)"
            ),
            {"id": event_id, "biz": uuid4(), "key": str(uuid4()), "now": NOW},
        )
        connection.execute(
            text(
                "INSERT INTO notification_deliveries "
                "(id,event_id,delivery_purpose,channel,event_version,attempt_no,"
                "status,channel_metadata,created_at) "
                "VALUES (:id,:event_id,'candidate_notification','feishu',1,1,"
                "'queued','{}',:now)"
            ),
            {"id": uuid4(), "event_id": event_id, "now": NOW},
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO notification_deliveries "
                    "(id,event_id,delivery_purpose,channel,event_version,attempt_no,"
                    "status,channel_metadata,created_at) "
                    "VALUES (:id,:event_id,'candidate_notification','feishu',1,1,"
                    "'queued','{}',:now)"
                ),
                {"id": uuid4(), "event_id": event_id, "now": NOW},
            )


def test_same_event_multiple_purposes_channels_allowed(delivery_engine: Engine) -> None:
    """Same event may carry several purposes/channels: the unique key scopes them."""

    event_id = uuid4()
    with delivery_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO notification_events "
                "(id,type,biz_id,idempotency_key,status,created_at) "
                "VALUES (:id,'appointment_cancelled',:biz,:key,'processed',:now)"
            ),
            {"id": event_id, "biz": uuid4(), "key": str(uuid4()), "now": NOW},
        )
        for channel, purpose in (
            ("email", "candidate_notification"),
            ("feishu", "candidate_notification"),
            ("email", "interviewer_cancellation"),
        ):
            connection.execute(
                text(
                    "INSERT INTO notification_deliveries "
                    "(id,event_id,delivery_purpose,channel,event_version,attempt_no,"
                    "status,channel_metadata,created_at) "
                    "VALUES (:id,:event_id,:purpose,:channel,1,1,'queued','{}',:now)"
                ),
                {
                    "id": uuid4(),
                    "event_id": event_id,
                    "purpose": purpose,
                    "channel": channel,
                    "now": NOW,
                },
            )
        count = connection.execute(
            text("SELECT count(*) FROM notification_deliveries WHERE event_id=:id"),
            {"id": event_id},
        ).scalar()
    assert count == 3
