"""Migrate chunk embeddings to 1024 dims (SiliconFlow BGE-M3, TASK-KB-EMB-001).

User-approved on 2026-08-14 (choosing BGE-M3, which is a fixed 1024-dim model,
pre-approves this dimension change): the ``knowledge_chunks.embedding`` column
moves from vector(768) to vector(1024). pgvector cannot cast across dimensions,
so the column is dropped and re-added; existing chunk vectors are lost and the
knowledge base must be re-ingested (expected — dev/seed data only at this stage).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_embedding_1024"
down_revision: str | Sequence[str] | None = "0006_knowledge_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIM = 1024


def upgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding, "
        f"ADD COLUMN embedding vector({_EMBEDDING_DIM})"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding, "
        "ADD COLUMN embedding vector(768)"
    )
