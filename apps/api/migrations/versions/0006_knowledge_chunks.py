"""Add chunk-level storage for hybrid retrieval (TASK-KB-RAG-001).

User-approved on 2026-08-14: documents are split into chunks (each with its own
pgvector embedding) for chunk-level recall. The 0005 ``knowledge_documents.embedding``
column is deprecated (kept, no longer written); chunk vectors live in this table.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_knowledge_chunks"
down_revision: str | Sequence[str] | None = "0005_knowledge_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIM = 768


def upgrade() -> None:
    op.execute(
        "CREATE TABLE knowledge_chunks ("
        "id UUID PRIMARY KEY, "
        "doc_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE, "
        "seq INTEGER NOT NULL, "
        "content TEXT NOT NULL, "
        f"embedding vector({_EMBEDDING_DIM}), "
        "created_at TIMESTAMPTZ NOT NULL, "
        "UNIQUE (doc_id, seq)"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE knowledge_chunks")
