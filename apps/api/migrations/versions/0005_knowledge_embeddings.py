"""Add pgvector support and the knowledge-document embedding column (M6 round 3).

User-approved on 2026-08-13 (TASK-M6-DB scope extension): switch PG to the pgvector
image (infra) and add ``knowledge_documents.embedding vector(768)`` for vector retrieval
of the knowledge base. The extension is infrastructure (``checkfirst``), so downgrade
only drops the column; the extension itself stays (harmless, idempotent).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_knowledge_embeddings"
down_revision: str | Sequence[str] | None = "0004_aiqa_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"ALTER TABLE knowledge_documents ADD COLUMN embedding "
        f"vector({_EMBEDDING_DIM})"
    )


def downgrade() -> None:
    op.drop_column("knowledge_documents", "embedding")
