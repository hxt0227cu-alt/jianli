"""SQLAlchemy Core repository for the approved AI QA conversation schema (0004).

Follows the ``app/auth/repository.py`` style: raw ``text()`` SQL, ``connect()`` for reads
and ``begin()`` for writes, UUIDs passed through psycopg directly. Tables:
``conversations`` / ``conversation_messages`` (domain model v1.1.5 §6.13, 180d purge).

Handoff note for Codex: round 3 (knowledge ingestion) adds a sibling repository over
``knowledge_documents`` / ``knowledge_index_versions`` in this module.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

_PURGE_DAYS = 180


def _now_utc() -> datetime:
    return datetime.now(UTC)


class ConversationRepository:
    """Persistent conversations and messages for authenticated Answer calls."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_conversations(self, user_id: UUID) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, created_at, updated_at FROM conversations "
                    "WHERE user_id=:user_id AND deleted_at IS NULL "
                    "ORDER BY updated_at DESC"
                ),
                {"user_id": user_id},
            ).mappings().all()
        return [dict(row) for row in rows]

    def create_conversation(self, user_id: UUID, now: datetime) -> dict[str, Any]:
        conversation_id = uuid4()
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO conversations (id,user_id,created_at,updated_at,purge_after) "
                    "VALUES (:id,:user_id,:now,:now,:purge_after)"
                ),
                {
                    "id": conversation_id,
                    "user_id": user_id,
                    "now": now,
                    "purge_after": now + timedelta(days=_PURGE_DAYS),
                },
            )
        return {"id": conversation_id, "created_at": now, "updated_at": now}

    def get_conversation(self, conversation_id: UUID) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT id, user_id, deleted_at FROM conversations WHERE id=:conversation_id"
                ),
                {"conversation_id": conversation_id},
            ).mappings().one_or_none()
        return dict(row) if row else None

    def list_messages(self, conversation_id: UUID) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, role, content, is_offtopic, created_at "
                    "FROM conversation_messages WHERE conv_id=:conversation_id "
                    "ORDER BY created_at ASC, id ASC"
                ),
                {"conversation_id": conversation_id},
            ).mappings().all()
        return [dict(row) for row in rows]

    def append_message(
        self,
        conversation_id: UUID,
        *,
        role: str,
        content: str,
        is_offtopic: bool,
        now: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO conversation_messages "
                    "(id,conv_id,role,content,is_offtopic,created_at) "
                    "VALUES (:id,:conv_id,:role,:content,:is_offtopic,:now)"
                ),
                {
                    "id": uuid4(),
                    "conv_id": conversation_id,
                    "role": role,
                    "content": content,
                    "is_offtopic": is_offtopic,
                    "now": now,
                },
            )

    def touch(self, conversation_id: UUID, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text("UPDATE conversations SET updated_at=:now WHERE id=:conversation_id"),
                {"now": now, "conversation_id": conversation_id},
            )


def default_now() -> datetime:
    return _now_utc()
