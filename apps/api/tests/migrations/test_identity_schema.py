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
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

DATABASE_URL = os.environ.get("JIANLI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="JIANLI_TEST_DATABASE_URL is required")
API_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_TABLES = {
    "users",
    "auth_sessions",
    "interviewer_profiles",
    "owner_contact_configs",
    "email_verification_tokens",
    "password_reset_tokens",
}


def _alembic_config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    return config


def _enum_exists(engine: Engine) -> bool:
    with engine.connect() as connection:
        return bool(
            connection.scalar(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace "
                    "WHERE n.nspname=current_schema() AND t.typname='user_role'"
                    ")"
                )
            )
        )


@pytest.fixture(scope="session")
def migrated_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config = _alembic_config()
    engine = create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= DOMAIN_TABLES
        assert _enum_exists(engine)

        command.downgrade(config, "base")
        assert DOMAIN_TABLES.isdisjoint(inspect(engine).get_table_names())
        assert not _enum_exists(engine)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM alembic_version")) == 0

        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


@pytest.fixture(autouse=True)
def clean_identity_data(migrated_engine: Engine) -> Iterator[None]:
    yield
    with migrated_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))


def _column_shape(inspector: Any, table: str) -> dict[str, tuple[str, bool]]:
    return {
        column["name"]: (type(column["type"]).__name__.lower(), column["nullable"])
        for column in inspector.get_columns(table)
    }


def _insert_user(connection: Any, *, role: str = "interviewer") -> tuple[object, str]:
    user_id = uuid4()
    email = f"user-{user_id}@example.invalid"
    connection.execute(
        text(
            "INSERT INTO users (id,email,password_hash,role,verified) "
            "VALUES (:id,:email,:hash,:role,true)"
        ),
        {"id": user_id, "email": email, "hash": "test-hash", "role": role},
    )
    return user_id, email


def test_identity_schema_shape(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    assert set(inspector.get_table_names()) == DOMAIN_TABLES | {"alembic_version"}
    assert _enum_exists(migrated_engine)

    expected_columns = {
        "users": {
            "id",
            "email",
            "password_hash",
            "role",
            "verified",
            "deletion_requested_at",
            "deleted_at",
            "purge_after",
        },
        "auth_sessions": {
            "id",
            "user_id",
            "session_token_hash",
            "device",
            "ip",
            "expires_at",
            "revoked_at",
        },
        "interviewer_profiles": {"user_id", "display_name"},
        "owner_contact_configs": {
            "id",
            "user_id",
            "candidate_phone_ciphertext",
            "candidate_feishu_open_id_ciphertext",
            "updated_at",
        },
        "email_verification_tokens": {
            "id",
            "user_id",
            "token_hash",
            "expires_at",
            "consumed_at",
        },
        "password_reset_tokens": {
            "id",
            "user_id",
            "token_hash",
            "expires_at",
            "consumed_at",
        },
    }
    for table, columns in expected_columns.items():
        assert set(_column_shape(inspector, table)) == columns

    users = _column_shape(inspector, "users")
    assert users["email"][1] is False
    assert users["password_hash"][1] is False
    assert users["role"][1] is False
    assert users["verified"][1] is False
    config = _column_shape(inspector, "owner_contact_configs")
    assert config["candidate_phone_ciphertext"][0] == "bytea"
    assert config["candidate_feishu_open_id_ciphertext"][0] == "bytea"
    assert "candidate_phone" not in config
    assert "candidate_feishu_open_id" not in config

    assert {index["name"] for index in inspector.get_indexes("users")} == {"uq_active_owner_admin"}
    assert {item["name"] for item in inspector.get_unique_constraints("users")} == {
        "uq_users_email"
    }
    assert {item["name"] for item in inspector.get_unique_constraints("owner_contact_configs")} == {
        "uq_owner_contact_configs_user_id"
    }
    assert {index["name"] for index in inspector.get_indexes("auth_sessions")} == {
        "ix_auth_sessions_user_id"
    }
    for table in ("email_verification_tokens", "password_reset_tokens"):
        assert {index["name"] for index in inspector.get_indexes(table)} == {f"ix_{table}_user_id"}
    for table in DOMAIN_TABLES - {"users"}:
        foreign_keys = inspector.get_foreign_keys(table)
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "users"
        assert foreign_keys[0]["options"] == {}


def test_unique_email_is_enforced(migrated_engine: Engine) -> None:
    with pytest.raises(IntegrityError), migrated_engine.begin() as connection:
        _, email = _insert_user(connection)
        connection.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,'test-hash','interviewer',true)"
            ),
            {"id": uuid4(), "email": email},
        )


def test_active_owner_constraint_and_soft_delete(migrated_engine: Engine) -> None:
    with pytest.raises(IntegrityError), migrated_engine.begin() as connection:
        _insert_user(connection, role="owner_admin")
        _insert_user(connection, role="owner_admin")

    with migrated_engine.begin() as connection:
        first_id, _ = _insert_user(connection, role="owner_admin")
        connection.execute(text("UPDATE users SET deleted_at=now() WHERE id=:id"), {"id": first_id})
        _insert_user(connection, role="owner_admin")


def test_invalid_role_is_rejected(migrated_engine: Engine) -> None:
    with pytest.raises(DBAPIError), migrated_engine.begin() as connection:
        _insert_user(connection, role="invalid_role")


@pytest.mark.parametrize(
    ("table", "columns", "values"),
    [
        (
            "auth_sessions",
            "id,user_id,session_token_hash,expires_at",
            ":id,:user_id,'token-hash',now()",
        ),
        ("interviewer_profiles", "user_id", ":user_id"),
        (
            "owner_contact_configs",
            "id,user_id,updated_at",
            ":id,:user_id,now()",
        ),
        (
            "email_verification_tokens",
            "id,user_id,token_hash,expires_at",
            ":id,:user_id,'token-hash',now()",
        ),
        (
            "password_reset_tokens",
            "id,user_id,token_hash,expires_at",
            ":id,:user_id,'token-hash',now()",
        ),
    ],
)
def test_missing_user_foreign_keys_are_rejected(
    migrated_engine: Engine, table: str, columns: str, values: str
) -> None:
    with pytest.raises(IntegrityError), migrated_engine.begin() as connection:
        connection.execute(
            text(f"INSERT INTO {table} ({columns}) VALUES ({values})"),
            {"id": uuid4(), "user_id": uuid4()},
        )


def test_repeat_upgrade_preserves_baseline_data(migrated_engine: Engine) -> None:
    with migrated_engine.begin() as connection:
        user_id, email = _insert_user(connection, role="owner_admin")

    command.upgrade(_alembic_config(), "head")

    with migrated_engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM users WHERE id=:id AND email=:email"),
                {"id": user_id, "email": email},
            )
            == 1
        )
