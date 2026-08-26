"""Migration 0009 objective AI QA observation tests on real PostgreSQL."""

from __future__ import annotations

import os
from collections.abc import Iterator
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


def _config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    return config


@pytest.fixture(scope="session")
def observation_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_aiqa_001_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config = _config()
    engine = create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "0008_notification_deliveries")
        old_columns = {c["name"] for c in inspect(engine).get_columns("conversation_messages")}
        assert {"grounded", "citations_count", "latency_ms"}.isdisjoint(old_columns)
        command.upgrade(config, "head")
        yield engine
    finally:
        command.upgrade(config, "head")
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


def test_observation_columns_and_checks(observation_engine: Engine) -> None:
    columns = {
        c["name"]: (type(c["type"]).__name__.lower(), c["nullable"])
        for c in inspect(observation_engine).get_columns("conversation_messages")
    }
    assert columns["grounded"] == ("boolean", True)
    assert columns["citations_count"] == ("integer", True)
    assert columns["latency_ms"] == ("integer", True)
    checks = {
        c["name"]
        for c in inspect(observation_engine).get_check_constraints("conversation_messages")
    }
    assert {
        "ck_conversation_messages_citations_count_nonnegative",
        "ck_conversation_messages_latency_ms_nonnegative",
    } <= checks


def test_observations_allow_null_and_reject_negative(observation_engine: Engine) -> None:
    user_id = uuid4()
    conversation_id = uuid4()
    with observation_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,'x','interviewer',true)"
            ),
            {"id": user_id, "email": f"obs-{user_id}@example.invalid"},
        )
        connection.execute(
            text(
                "INSERT INTO conversations (id,user_id,created_at,updated_at) "
                "VALUES (:id,:user_id,now(),now())"
            ),
            {"id": conversation_id, "user_id": user_id},
        )
        connection.execute(
            text(
                "INSERT INTO conversation_messages "
                "(id,conv_id,role,content,is_offtopic,created_at) "
                "VALUES (:id,:conv_id,'user','hello',false,now())"
            ),
            {"id": uuid4(), "conv_id": conversation_id},
        )
    for column in ("citations_count", "latency_ms"):
        with pytest.raises(IntegrityError), observation_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO conversation_messages "
                    f"(id,conv_id,role,content,is_offtopic,{column},created_at) "
                    f"VALUES (:id,:conv_id,'assistant','answer',false,-1,now())"
                ),
                {"id": uuid4(), "conv_id": conversation_id},
            )
