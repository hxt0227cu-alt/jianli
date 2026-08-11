from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 12, 9, tzinfo=UTC)
EXCEPTION_SQL = text(
    "INSERT INTO company_booking_exceptions "
    "(id,interviewer_user_id,company_fingerprint,approved_by,reason,expires_at,created_at) "
    "VALUES (:id,:user,:fingerprint,:actor,'test',:expires,:created)"
)
APPOINTMENT_SQL = text(
    "INSERT INTO appointments "
    "(id,user_id,company_id,dedupe_exception_id,start_at,end_at,status,"
    "company_name_ciphertext,company_name_fingerprint,version,created_at) "
    "VALUES (:id,:user,:company,:exception,:start,:end,'active',:cipher,:fingerprint,1,:now)"
)


@pytest.fixture(scope="session")
def constraint_engine() -> Iterator[Engine]:
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


@pytest.fixture(autouse=True)
def clean_data(constraint_engine: Engine) -> Iterator[None]:
    yield
    with constraint_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))
        connection.execute(text("TRUNCATE TABLE companies CASCADE"))


def _user(connection: Any) -> UUID:
    user_id = uuid4()
    connection.execute(
        text("INSERT INTO users VALUES (:id,:email,'hash','interviewer',true,NULL,NULL,NULL)"),
        {"id": user_id, "email": f"user-{user_id}@example.invalid"},
    )
    return user_id


def _company(connection: Any, fingerprint: str | None = None) -> UUID:
    company_id = uuid4()
    connection.execute(
        text("INSERT INTO companies VALUES (:id,:fingerprint,:ciphertext)"),
        {"id": company_id, "fingerprint": fingerprint or str(company_id), "ciphertext": b"x"},
    )
    return company_id


def _exception(connection: Any, user_id: UUID, fingerprint: str) -> UUID:
    exception_id = uuid4()
    connection.execute(
        EXCEPTION_SQL,
        {
            "id": exception_id,
            "user": user_id,
            "fingerprint": fingerprint,
            "actor": uuid4(),
            "expires": NOW + timedelta(days=1),
            "created": NOW,
        },
    )
    return exception_id


def _appointment(
    connection: Any, user: UUID, company: UUID, fingerprint: str, exception: UUID | None = None
) -> None:
    connection.execute(
        APPOINTMENT_SQL,
        {
            "id": uuid4(),
            "user": user,
            "company": company,
            "exception": exception,
            "start": NOW,
            "end": NOW + timedelta(minutes=90),
            "cipher": b"x",
            "fingerprint": fingerprint,
            "now": NOW,
        },
    )


def test_company_fingerprint_is_unique(constraint_engine: Engine) -> None:
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        _company(connection, "same")
        _company(connection, "same")


@pytest.mark.parametrize("collision", ["user", "company"])
def test_active_appointment_partial_uniques(constraint_engine: Engine, collision: str) -> None:
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        users = (_user(connection), _user(connection))
        companies = (_company(connection), _company(connection))
        _appointment(connection, users[0], companies[0], "first")
        _appointment(
            connection,
            users[0] if collision == "user" else users[1],
            companies[1],
            "first" if collision == "company" else "second",
        )


def test_exception_uniques(constraint_engine: Engine) -> None:
    with constraint_engine.begin() as connection:
        users = (_user(connection), _user(connection))
        first_id = _exception(connection, users[0], "same")
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        _exception(connection, users[0], "same")
    with constraint_engine.begin() as connection:
        connection.execute(
            text("UPDATE company_booking_exceptions SET consumed_at=:now WHERE id=:id"),
            {"now": NOW, "id": first_id},
        )
        _exception(connection, users[0], "same")
        companies = (_company(connection), _company(connection))
        reusable = _exception(connection, users[1], "other")
        _appointment(connection, users[0], companies[0], "first", reusable)
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        _appointment(connection, users[1], companies[1], "second", reusable)


def test_slot_unique_and_duration_constraints(constraint_engine: Engine) -> None:
    insert = text(
        "INSERT INTO appointment_slots (id,start_at,end_at,status,version) "
        "VALUES (:id,:start,:end,'available',1)"
    )
    valid = {"id": uuid4(), "start": NOW, "end": NOW + timedelta(minutes=30)}
    with constraint_engine.begin() as connection:
        connection.execute(insert, valid)
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        connection.execute(insert, {**valid, "id": uuid4()})
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        connection.execute(
            insert,
            {"id": uuid4(), "start": NOW + timedelta(hours=1), "end": NOW + timedelta(hours=2)},
        )


def test_override_range_must_be_positive(constraint_engine: Engine) -> None:
    with pytest.raises(IntegrityError), constraint_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO availability_overrides "
                "(id,start_at,end_at,action,created_by,created_at) "
                "VALUES (:id,:now,:now,'force_unavailable',:user,:now)"
            ),
            {"id": uuid4(), "now": NOW, "user": _user(connection)},
        )
