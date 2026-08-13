"""Migration 0004 (AI QA schema) tests on a real PostgreSQL database.

Follows the established suite pattern (see test_outbox_audit_schema.py): requires
``JIANLI_TEST_DATABASE_URL`` pointing at a dedicated DB named ``jianli_tc_aiqa_001_db``.
Covers reversibility (up → down to 0003 → up), table/enum/index/FK shape, the cycle FK,
"same file dedupe" partial unique index, and cascade deletes.
"""

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
PRIOR_TABLES = {
    "users",
    "auth_sessions",
    "email_verification_tokens",
    "password_reset_tokens",
    "companies",
    "company_booking_exceptions",
    "appointments",
    "appointment_slots",
    "availability_overrides",
    "notification_events",
    "audit_logs",
}
AIQA_TABLES = {
    "conversations",
    "conversation_messages",
    "knowledge_documents",
    "knowledge_index_versions",
}
NOW = datetime(2026, 8, 13, 9, tzinfo=UTC)


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
def aiqa_engine() -> Iterator[Engine]:
    assert DATABASE_URL is not None
    assert make_url(DATABASE_URL).database == "jianli_tc_aiqa_001_db"
    previous_url = os.environ.get("JIANLI_DATABASE_URL")
    os.environ["JIANLI_DATABASE_URL"] = DATABASE_URL
    config, engine = _config(), create_engine(DATABASE_URL)
    try:
        command.upgrade(config, "head")
        assert set(inspect(engine).get_table_names()) >= AIQA_TABLES
        assert set(inspect(engine).get_table_names()) >= PRIOR_TABLES
        command.downgrade(config, "0003_outbox_audit_schema")
        assert AIQA_TABLES.isdisjoint(inspect(engine).get_table_names())
        assert set(inspect(engine).get_table_names()) >= PRIOR_TABLES
        command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("JIANLI_DATABASE_URL", None)
        else:
            os.environ["JIANLI_DATABASE_URL"] = previous_url


def _shape(engine: Engine, table: str) -> dict[str, tuple[str, bool]]:
    def type_name(column: Any) -> str:
        name = type(column["type"]).__name__.lower()
        if name == "timestamp" and column["type"].timezone:
            return "timestamptz"
        # SQLAlchemy dialect names: BOOLEAN/INTEGER -> bool/int for readability.
        if name == "boolean":
            return "bool"
        if name == "integer":
            return "int"
        return name

    return {
        column["name"]: (type_name(column), column["nullable"])
        for column in inspect(engine).get_columns(table)
    }


def _insert_user(connection: Any) -> str:
    user_id = str(uuid4())
    connection.execute(
        text(
            "INSERT INTO users (id,email,password_hash,role,verified) "
            "VALUES (:id,:email,:pwd,'interviewer',true)"
        ),
        {"id": user_id, "email": f"aiqa-{uuid4().hex[:8]}@example.com", "pwd": "x"},
    )
    return user_id


def test_aiqa_schema_shape(aiqa_engine: Engine) -> None:
    assert _shape(aiqa_engine, "conversations") == {
        "id": ("uuid", False),
        "user_id": ("uuid", False),
        "created_at": ("timestamptz", False),
        "updated_at": ("timestamptz", False),
        "deleted_at": ("timestamptz", True),
        "purge_after": ("timestamptz", True),
    }
    assert _shape(aiqa_engine, "conversation_messages") == {
        "id": ("uuid", False),
        "conv_id": ("uuid", False),
        "role": ("enum", False),
        "content": ("text", False),
        "is_offtopic": ("bool", False),
        "created_at": ("timestamptz", False),
    }
    assert _shape(aiqa_engine, "knowledge_documents") == {
        "id": ("uuid", False),
        "name": ("text", False),
        "type": ("enum", False),
        "size": ("int", False),
        "content_checksum": ("text", False),
        "storage_key": ("text", False),
        "status": ("enum", False),
        "parse_mode": ("enum", True),
        "failure_reason": ("text", True),
        "retrieval_disabled_at": ("timestamptz", True),
        "active_index_version_id": ("uuid", True),
        "version": ("int", False),
        "created_at": ("timestamptz", False),
        # 0005: pgvector vector(768) column. SQLAlchemy does not recognize the
        # extension type, so the inspector reports it as the generic NullType.
        "embedding": ("nulltype", True),
    }
    assert _shape(aiqa_engine, "knowledge_index_versions") == {
        "id": ("uuid", False),
        "doc_id": ("uuid", False),
        "version": ("int", False),
        "status": ("enum", False),
        "indexed_at": ("timestamptz", False),
    }
    for name, labels in {
        "message_role": ["user", "assistant"],
        "knowledge_document_type": ["md", "pdf", "docx", "txt"],
        "knowledge_document_status": ["indexing", "indexed", "failed"],
        "knowledge_document_parse_mode": ["text", "ocr", "native"],
        "knowledge_index_status": ["building", "ready", "rolled_back"],
    }.items():
        assert _enum_labels(aiqa_engine, name) == labels


def test_aiqa_indexes_and_cycle_fk(aiqa_engine: Engine) -> None:
    inspector = inspect(aiqa_engine)
    conv_indexes = {i["name"] for i in inspector.get_indexes("conversations")}
    assert conv_indexes == {"ix_conversations_user", "ix_conversations_purge"}
    msg_indexes = {i["name"] for i in inspector.get_indexes("conversation_messages")}
    assert msg_indexes == {"ix_conversation_messages_conv"}
    doc_indexes = {i["name"]: i for i in inspector.get_indexes("knowledge_documents")}
    assert set(doc_indexes) == {
        "uq_knowledge_documents_storage_key",
        "uq_knowledge_documents_active_checksum",
        "ix_knowledge_documents_created_at",
    }
    checksum = doc_indexes["uq_knowledge_documents_active_checksum"]
    assert checksum["unique"] is True
    assert checksum["column_names"] == ["content_checksum"]
    predicate = str(checksum["dialect_options"]["postgresql_where"])
    assert "retrieval_disabled_at IS NULL" in predicate
    iv_indexes = {i["name"] for i in inspector.get_indexes("knowledge_index_versions")}
    assert iv_indexes == {
        "uq_knowledge_index_versions_doc_version",
        "ix_knowledge_index_versions_doc",
    }

    def fks(table: str) -> dict[str, dict[str, Any]]:
        return {fk["name"]: fk for fk in inspector.get_foreign_keys(table)}

    assert fks("conversations")["fk_conversations_user_id"]["referred_table"] == "users"
    conv_msg_fk = fks("conversation_messages")["fk_conversation_messages_conv_id"]
    assert conv_msg_fk["referred_table"] == "conversations"
    assert conv_msg_fk["options"].get("ondelete") == "CASCADE"
    assert fks("knowledge_documents")["fk_knowledge_documents_active_index_version_id"][
        "referred_table"
    ] == "knowledge_index_versions"
    iv_fk = fks("knowledge_index_versions")["fk_knowledge_index_versions_doc_id"]
    assert iv_fk["referred_table"] == "knowledge_documents"
    assert iv_fk["options"].get("ondelete") == "CASCADE"


def _insert_doc(connection: Any, checksum: str, storage_key: str) -> str:
    doc_id = str(uuid4())
    connection.execute(
        text(
            "INSERT INTO knowledge_documents "
            "(id,name,type,size,content_checksum,storage_key,status,version,created_at) "
            "VALUES (:id,'resume.md','md',100,:checksum,:key,'indexed',1,:created_at)"
        ),
        {
            "id": doc_id,
            "checksum": checksum,
            "key": storage_key,
            "created_at": NOW,
        },
    )
    return doc_id


def test_active_checksum_dedupe_and_reupload_after_disable(aiqa_engine: Engine) -> None:
    checksum = f"sha256-{uuid4().hex}"
    with aiqa_engine.begin() as connection:
        _insert_doc(connection, checksum, f"obj/{uuid4().hex}.md")
    with pytest.raises(IntegrityError), aiqa_engine.begin() as connection:
        _insert_doc(connection, checksum, f"obj/{uuid4().hex}.md")
    # Disable retrieval (delete semantics) then re-uploading the same content is allowed.
    with aiqa_engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE knowledge_documents SET retrieval_disabled_at=:now "
                "WHERE content_checksum=:c"
            ),
            {"now": NOW, "c": checksum},
        )
        _insert_doc(connection, checksum, f"obj/{uuid4().hex}.md")


def test_message_role_enum_and_doc_version_unique(aiqa_engine: Engine) -> None:
    with aiqa_engine.begin() as connection:
        user_id = _insert_user(connection)
        conv_id = str(uuid4())
        connection.execute(
            text(
                "INSERT INTO conversations (id,user_id,created_at,updated_at,purge_after) "
                "VALUES (:id,:uid,:now,:now,:purge)"
            ),
            {"id": conv_id, "uid": user_id, "now": NOW, "purge": NOW},
        )
    with pytest.raises(DBAPIError), aiqa_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO conversation_messages "
                "(id,conv_id,role,content,is_offtopic,created_at) "
                "VALUES (:id,:conv,'admin','hi',false,:now)"
            ),
            {"id": str(uuid4()), "conv": conv_id, "now": NOW},
        )
    with aiqa_engine.begin() as connection:
        doc_id = _insert_doc(connection, f"sha256-{uuid4().hex}", f"obj/{uuid4().hex}.md")
        connection.execute(
            text(
                "INSERT INTO knowledge_index_versions "
                "(id,doc_id,version,status,indexed_at) "
                "VALUES (:id,:doc,1,'ready',:now)"
            ),
            {"id": str(uuid4()), "doc": doc_id, "now": NOW},
        )
    with pytest.raises(IntegrityError), aiqa_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO knowledge_index_versions "
                "(id,doc_id,version,status,indexed_at) "
                "VALUES (:id,:doc,1,'ready',:now)"
            ),
            {"id": str(uuid4()), "doc": doc_id, "now": NOW},
        )


def test_conversation_cascade_deletes_messages(aiqa_engine: Engine) -> None:
    with aiqa_engine.begin() as connection:
        user_id = _insert_user(connection)
        conv_id = str(uuid4())
        connection.execute(
            text(
                "INSERT INTO conversations (id,user_id,created_at,updated_at) "
                "VALUES (:id,:uid,:now,:now)"
            ),
            {"id": conv_id, "uid": user_id, "now": NOW},
        )
        connection.execute(
            text(
                "INSERT INTO conversation_messages "
                "(id,conv_id,role,content,is_offtopic,created_at) "
                "VALUES (:id,:conv,'user','hi',false,:now)"
            ),
            {"id": str(uuid4()), "conv": conv_id, "now": NOW},
        )
        connection.execute(text("DELETE FROM conversations WHERE id=:id"), {"id": conv_id})
        count = connection.scalar(
            text("SELECT count(*) FROM conversation_messages WHERE conv_id=:id"), {"id": conv_id}
        )
        assert count == 0
