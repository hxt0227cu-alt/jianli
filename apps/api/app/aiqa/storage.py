"""Local-disk object storage for parsed knowledge-document text (M6 round 3).

Implements the ``storage_key`` contract of domain model §6.14 using a local directory
(user-approved): each document's parsed text lives at ``{storage_dir}/{document_id}.txt``.
Zero dependencies, zero external services. Swap this for S3/COS later behind the same
three methods.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID


class KnowledgeStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)

    def _path(self, document_id: UUID) -> Path:
        return self._root / f"{document_id}.txt"

    def save(self, document_id: UUID, text: str) -> None:
        path = self._path(document_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def load(self, document_id: UUID) -> str:
        return self._path(document_id).read_text(encoding="utf-8")

    def delete(self, document_id: UUID) -> None:
        self._path(document_id).unlink(missing_ok=True)
