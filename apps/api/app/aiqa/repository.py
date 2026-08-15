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


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(value) for value in vector) + "]"


class KnowledgeRepository:
    """Knowledge-document metadata + pgvector retrieval (M6 round 3, migration 0005)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_documents(self) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id,name,type,size,status,parse_mode,failure_reason,created_at "
                    "FROM knowledge_documents ORDER BY created_at DESC"
                ),
            ).mappings().all()
        return [dict(row) for row in rows]

    def get_document(self, document_id: UUID) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT id,name,type,size,status,parse_mode,failure_reason,"
                    "retrieval_disabled_at FROM knowledge_documents WHERE id=:document_id"
                ),
                {"document_id": document_id},
            ).mappings().one_or_none()
        return dict(row) if row else None

    def create_document(
        self,
        *,
        document_id: UUID,
        name: str,
        doc_type: str,
        size: int,
        content_checksum: str,
        storage_key: str,
        parse_mode: str,
        now: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO knowledge_documents "
                    "(id,name,type,size,content_checksum,storage_key,status,parse_mode,"
                    "version,created_at) "
                    "VALUES (:id,:name,:type,:size,:checksum,:storage_key,'indexing',"
                    ":parse_mode,1,:now)"
                ),
                {
                    "id": document_id,
                    "name": name,
                    "type": doc_type,
                    "size": size,
                    "checksum": content_checksum,
                    "storage_key": storage_key,
                    "parse_mode": parse_mode,
                    "now": now,
                },
            )

    def mark_indexed(self, document_id: UUID) -> None:
        """Chunk-level embeddings replaced whole-document embedding (TASK-KB-RAG-001):
        the 0005 column stays NULL and chunk vectors live in ``knowledge_chunks``."""

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE knowledge_documents SET status='indexed', "
                    "embedding=NULL, failure_reason=NULL WHERE id=:document_id"
                ),
                {"document_id": document_id},
            )

    def mark_failed(self, document_id: UUID, reason: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE knowledge_documents SET status='failed', failure_reason=:reason "
                    "WHERE id=:document_id"
                ),
                {"document_id": document_id, "reason": reason},
            )

    def disable_retrieval(self, document_id: UUID, now: datetime) -> None:
        """Soft delete: immediately disables retrieval (domain model §6.14)."""

        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE knowledge_documents SET retrieval_disabled_at=:now "
                    "WHERE id=:document_id"
                ),
                {"document_id": document_id, "now": now},
            )

    # -- chunk-level storage and hybrid retrieval (TASK-KB-RAG-001) -----------------------

    def replace_chunks(
        self,
        document_id: UUID,
        chunks: list[tuple[int, str]],
        embeddings: list[list[float]],
        now: datetime,
    ) -> None:
        """Replace all chunks of a document (delete + insert in one transaction)."""

        with self._engine.begin() as connection:
            connection.execute(
                text("DELETE FROM knowledge_chunks WHERE doc_id=:document_id"),
                {"document_id": document_id},
            )
            for (seq, content), vector in zip(chunks, embeddings, strict=True):
                connection.execute(
                    text(
                        "INSERT INTO knowledge_chunks "
                        "(id,doc_id,seq,content,embedding,created_at) "
                        "VALUES (:id,:doc_id,:seq,:content,:embedding,:now)"
                    ),
                    {
                        "id": uuid4(),
                        "doc_id": document_id,
                        "seq": seq,
                        "content": content,
                        "embedding": _vector_literal(vector),
                        "now": now,
                    },
                )

    def search_chunks(
        self, embedding: list[float], top_k: int = 10, min_score: float = 0.0
    ) -> list[dict[str, Any]]:
        """Vector retrieval over chunks of active documents. Score = 1 - distance.

        ``min_score`` (P1, TASK-KB-THRESHOLD-001): drop chunks below the cosine
        relevance threshold (0 = disabled, legacy top-k hard recall).
        """

        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT c.id AS chunk_id, c.doc_id, c.seq, c.content, d.name AS doc_name, "
                    "1 - (c.embedding <=> :query) AS score "
                    "FROM knowledge_chunks c "
                    "JOIN knowledge_documents d ON d.id = c.doc_id "
                    "WHERE d.retrieval_disabled_at IS NULL AND c.embedding IS NOT NULL "
                    "AND (1 - (c.embedding <=> :query)) >= :min_score "
                    "ORDER BY c.embedding <=> :query LIMIT :top_k"
                ),
                {"query": _vector_literal(embedding), "min_score": min_score, "top_k": top_k},
            ).mappings().all()
        return [dict(row) for row in rows]

    def load_chunk_corpus(self) -> list[tuple[str, str]]:
        """(chunk_id, content) pairs of active documents for BM25 indexing."""

        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT c.id, c.content FROM knowledge_chunks c "
                    "JOIN knowledge_documents d ON d.id = c.doc_id "
                    "WHERE d.retrieval_disabled_at IS NULL"
                ),
            ).mappings().all()
        return [(str(row["id"]), row["content"]) for row in rows]

    def chunk_rows(self, chunk_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Chunk detail rows keyed by chunk id (for assembling candidates)."""

        if not chunk_ids:
            return {}
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT c.id, c.doc_id, c.seq, c.content, d.name AS doc_name "
                    "FROM knowledge_chunks c "
                    "JOIN knowledge_documents d ON d.id = c.doc_id "
                    "WHERE c.id = ANY(:ids)"
                ),
                {"ids": chunk_ids},
            ).mappings().all()
        return {str(row["id"]): dict(row) for row in rows}
