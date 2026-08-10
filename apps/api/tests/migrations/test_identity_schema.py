from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")


def test_identity_schema_shape() -> None:
    assert DATABASE_URL is not None
    inspector = inspect(create_engine(DATABASE_URL))
    assert set(inspector.get_table_names()) >= {
        "users",
        "auth_sessions",
        "interviewer_profiles",
        "owner_contact_configs",
        "email_verification_tokens",
        "password_reset_tokens",
    }
    assert {index["name"] for index in inspector.get_indexes("users")} >= {"uq_active_owner_admin"}


def test_second_active_owner_is_rejected() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL)
    first_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:hash,'owner_admin',true)"
            ),
            {"id": first_id, "email": f"owner-{first_id}@example.invalid", "hash": "hash"},
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        second_id = uuid4()
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:hash,'owner_admin',true)"
            ),
            {"id": second_id, "email": f"owner-{second_id}@example.invalid", "hash": "hash"},
        )
