"""Create the approved AI QA (Answer) schema: conversations, messages, knowledge docs.

Schema approved 2026-08-13 by user (TASK-M6-DB). Field/constraint design follows the
approved domain model v1.1.5 §6.13 (Conversation/Message, 180d purge) and §6.14
(KnowledgeDocument/KnowledgeIndexVersion, delete-disables-retrieval + index hot-swap).

Two structural notes for handoff (Codex):
- ``knowledge_documents.active_index_version_id`` and
  ``knowledge_index_versions.doc_id`` form a cycle, so the former FK is added AFTER both
  tables exist (``op.create_foreign_key``), and downgrade drops it first.
- "Same file dedupe" is a partial unique index on ``content_checksum`` restricted to
  active documents (``retrieval_disabled_at IS NULL``): deleting a document re-enables
  uploading the same content later.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_aiqa_schema"
down_revision: str | Sequence[str] | None = "0003_outbox_audit_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_enums() -> dict[str, postgresql.ENUM]:
    bind = op.get_bind()
    definitions = (
        ("message_role", ("user", "assistant")),
        ("knowledge_document_type", ("md", "pdf", "docx", "txt")),
        ("knowledge_document_status", ("indexing", "indexed", "failed")),
        ("knowledge_document_parse_mode", ("text", "ocr", "native")),
        ("knowledge_index_status", ("building", "ready", "rolled_back")),
    )
    for name, labels in definitions:
        postgresql.ENUM(*labels, name=name).create(bind, checkfirst=True)
    return {
        name: postgresql.ENUM(*labels, name=name, create_type=False)
        for name, labels in definitions
    }


def upgrade() -> None:
    enums = _create_enums()
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", name="fk_conversations_user_id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("purge_after", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_conversations_user",
        "conversations",
        ["user_id", sa.text("updated_at DESC")],
    )
    op.create_index(
        "ix_conversations_purge",
        "conversations",
        ["purge_after"],
        postgresql_where=sa.text("purge_after IS NOT NULL"),
    )

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "conv_id",
            sa.Uuid(),
            sa.ForeignKey(
                "conversations.id", name="fk_conversation_messages_conv_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("role", enums["message_role"], nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_offtopic", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_conversation_messages_conv",
        "conversation_messages",
        ["conv_id", "created_at"],
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", enums["knowledge_document_type"], nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content_checksum", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("status", enums["knowledge_document_status"], nullable=False),
        sa.Column("parse_mode", enums["knowledge_document_parse_mode"]),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("retrieval_disabled_at", sa.DateTime(timezone=True)),
        # FK to knowledge_index_versions is added after that table exists (cycle, see note).
        sa.Column("active_index_version_id", sa.Uuid()),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("storage_key", name="uq_knowledge_documents_storage_key"),
    )
    op.create_index(
        "uq_knowledge_documents_active_checksum",
        "knowledge_documents",
        ["content_checksum"],
        unique=True,
        postgresql_where=sa.text("retrieval_disabled_at IS NULL"),
    )
    op.create_index(
        "ix_knowledge_documents_created_at",
        "knowledge_documents",
        [sa.text("created_at DESC")],
    )

    op.create_table(
        "knowledge_index_versions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "doc_id",
            sa.Uuid(),
            sa.ForeignKey(
                "knowledge_documents.id",
                name="fk_knowledge_index_versions_doc_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", enums["knowledge_index_status"], nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("doc_id", "version", name="uq_knowledge_index_versions_doc_version"),
    )
    op.create_index(
        "ix_knowledge_index_versions_doc",
        "knowledge_index_versions",
        ["doc_id", "status"],
    )
    op.create_foreign_key(
        "fk_knowledge_documents_active_index_version_id",
        "knowledge_documents",
        "knowledge_index_versions",
        ["active_index_version_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_knowledge_documents_active_index_version_id",
        "knowledge_documents",
        type_="foreignkey",
    )
    op.drop_index("ix_knowledge_index_versions_doc", table_name="knowledge_index_versions")
    op.drop_index("ix_knowledge_documents_created_at", table_name="knowledge_documents")
    op.drop_index(
        "uq_knowledge_documents_active_checksum", table_name="knowledge_documents"
    )
    op.drop_table("knowledge_index_versions")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_conversation_messages_conv", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_purge", table_name="conversations")
    op.drop_index("ix_conversations_user", table_name="conversations")
    op.drop_table("conversations")
    for name in (
        "message_role",
        "knowledge_document_type",
        "knowledge_document_status",
        "knowledge_document_parse_mode",
        "knowledge_index_status",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
