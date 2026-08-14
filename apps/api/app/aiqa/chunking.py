"""Document chunking for chunk-level RAG retrieval (TASK-KB-RAG-001).

Pure Python, zero dependencies. Chunks are fixed-size character windows with overlap,
preferring paragraph boundaries when the boundary falls inside the window. Each chunk
gets its own embedding (pgvector), enabling finer-grained recall than whole-document
vectors. ``seq`` is 1-based.
"""

from __future__ import annotations

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_OVERLAP = 50


def chunk_text(
    text: str, chunk_size: int = _DEFAULT_CHUNK_SIZE, overlap: int = _DEFAULT_OVERLAP
) -> list[tuple[int, str]]:
    """Split ``text`` into ``(seq, chunk)`` pieces (seq starts at 1)."""

    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [(1, text)]
    chunks: list[tuple[int, str]] = []
    start = 0
    seq = 1
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Prefer a paragraph/sentence boundary near the window end.
        if end < len(text):
            window = text[start:end]
            boundary = max(
                window.rfind("\n"),
                window.rfind("。"),
                window.rfind("；"),
                window.rfind("！"),
                window.rfind("？"),
                window.rfind(". "),
            )
            if boundary > chunk_size // 2:
                end = start + boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((seq, chunk))
            seq += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
