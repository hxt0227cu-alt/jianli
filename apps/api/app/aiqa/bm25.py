"""Pure-Python BM25 (Okapi) for hybrid retrieval (TASK-KB-RAG-001).

Zero dependencies. Tokenization reuses the Answer-domain convention: CJK single
characters + ASCII word tokens (mirrors ``retrieval.py``). Documents are chunks with an
id (``str(chunk_id)``), a ``doc`` label and a ``text`` body; ranking returns (id, score).
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+|[一-鿿]")

_K1 = 1.5
_B = 0.75


def _tokens(text: str) -> list[str]:
    return [
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) > 1 or ord(tok[0]) >= 0x2E80
    ]


class BM25Index:
    """In-memory BM25 over a snapshot of chunk documents (small corpora)."""

    def __init__(self, documents: list[tuple[str, str]]) -> None:
        """``documents`` = [(chunk_id, text), ...]; stats computed eagerly."""

        self._documents = documents
        self._lengths: list[int] = []
        self._avg_len = 0.0
        self._postings: dict[str, dict[str, int]] = {}
        self._doc_freq: dict[str, int] = {}
        if documents:
            total = 0
            for chunk_id, text in documents:
                counts = Counter(_tokens(text))
                length = sum(counts.values())
                self._lengths.append(length)
                total += length
                for token, count in counts.items():
                    postings = self._postings.setdefault(token, {})
                    postings[chunk_id] = count
            self._avg_len = total / len(documents)
            self._doc_freq = {token: len(postings) for token, postings in self._postings.items()}

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        query_tokens = _tokens(query)
        if not query_tokens or not self._documents:
            return []
        n_docs = len(self._documents)
        scores: dict[str, float] = {}
        for token in set(query_tokens):
            postings = self._postings.get(token)
            if not postings:
                continue
            df = self._doc_freq[token]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            for index, (chunk_id, _) in enumerate(self._documents):
                freq = postings.get(chunk_id)
                if freq is None:
                    continue
                length = self._lengths[index]
                denom = freq + _K1 * (1 - _B + _B * length / self._avg_len)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + idf * (freq * (_K1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ranked[:top_k]


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, float]]],
    top_k: int = 10,
    k: int = 60,
) -> list[tuple[str, float]]:
    """RRF fusion: score = sum(1 / (k + rank_i)) across ranked chunk-id lists."""

    fused: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (chunk_id, _) in enumerate(ranked, start=1):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank)
    ranked = sorted(fused.items(), key=lambda item: item[1], reverse=True)
    return ranked[:top_k]
