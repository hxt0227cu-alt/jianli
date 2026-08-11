from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError, IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 12, 9, tzinfo=UTC)


@pytest.fixture(scope="session")
def referential_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_ops_002_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    engine = create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO appointments VALUES "
        "(:id,:user,:company,NULL,:now,:later,'invalid',:x,'fp',"
        "NULL,NULL,NULL,NULL,1,:now,NULL,NULL,NULL,NULL)",
        "INSERT INTO appointment_slots VALUES (:id,:now,:later,'invalid',NULL,1)",
        "INSERT INTO availability_overrides VALUES (:id,:now,:later,'invalid',NULL,:user,:now)",
    ],
)
def test_invalid_enums_are_rejected(referential_engine: Engine, statement: str) -> None:
    with pytest.raises(DBAPIError), referential_engine.begin() as connection:
        user_id, company_id = uuid4(), uuid4()
        connection.execute(
            text("INSERT INTO users VALUES (:id,:email,'hash','interviewer',true,NULL,NULL,NULL)"),
            {"id": user_id, "email": f"user-{user_id}@example.invalid"},
        )
        connection.execute(
            text("INSERT INTO companies VALUES (:id,'company',:x)"),
            {"id": company_id, "x": b"x"},
        )
        connection.execute(
            text(statement),
            {
                "id": uuid4(),
                "user": user_id,
                "company": company_id,
                "now": NOW,
                "later": NOW + timedelta(minutes=30),
                "x": b"x",
            },
        )


def test_missing_foreign_key_is_rejected(referential_engine: Engine) -> None:
    with pytest.raises(IntegrityError), referential_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO availability_overrides "
                "(id,start_at,end_at,action,created_by,created_at) "
                "VALUES (:id,:now,:later,'force_available',:missing,:now)"
            ),
            {
                "id": uuid4(),
                "now": NOW,
                "later": NOW + timedelta(minutes=30),
                "missing": uuid4(),
            },
        )
