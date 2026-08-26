"""Pure-Python retrieval over the static page corpus (M6 round 1).

No vector store, no new dependency. A small term-overlap scorer ranks page chunks
against the question and returns the top candidates used for grounding and citations.

Handoff note for Codex: swap ``retrieve`` for a pgvector / full-text search backed by
``knowledge_index_versions`` once TASK-M6-DB lands (round 3). Keep the return type
``list[Candidate]`` so the service and SSE framing are unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .content import PAGES, PageChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+|[一-鿿]")
_CJK_RUN_RE = re.compile(r"[一-鿿]+")

# CJK functional words that carry no topical meaning (TASK-KB-THRESHOLD-001):
# a question like "帮我写一个爬虫" shares 我/一/个 with every page chunk, so counting
# them makes every question "grounded". Excluding them makes the >=2 overlap gate
# actually test topical relevance (e.g. 技术/方向 vs a resume chunk), not function words.
_CJK_STOPWORDS = frozenset(
    "的了是在你我他她它一一个就有没不也和与及或被让给对从向到于之其们些"
    "都也很要会能这那什么怎么怎样哪个里谁几两多少为就才再又还只但而若则"
    "帮我做看过说想问叫请把给跟把"
)


@dataclass(frozen=True, slots=True)
class Candidate:
    doc: str
    fragment: int
    text: str
    score: float


def _tokens(text: str) -> set[str]:
    # Keep ASCII words of 2+ chars and every single CJK character (Chinese terms are
    # character-granular); drop stray single ASCII letters such as "a".
    return {
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) > 1 or ord(tok[0]) >= 0x2E80
    }


def _corpus(page_key: str, project_key: str | None) -> list[PageChunk]:
    page = PAGES.get(page_key)
    if page is None:
        return []
    if page_key == "projects" and project_key is not None:
        return [c for c in page.chunks if c.doc == project_key]
    return page.chunks


def _cjk_bigrams(text: str) -> set[str]:
    """Return adjacent CJK pairs, preserving word order for a cheap relevance signal."""

    return {
        run[index : index + 2]
        for run in _CJK_RUN_RE.findall(text)
        for index in range(len(run) - 1)
    }


def retrieve(
    question: str, page_key: str, project_key: str | None, top_k: int = 5
) -> list[Candidate]:
    """Rank page chunks by term overlap with the question; empty list means off-topic."""

    query_terms = _tokens(question) - _CJK_STOPWORDS
    if not query_terms:
        return []
    query_bigrams = _cjk_bigrams(question)
    scored: list[Candidate] = []
    for chunk in _corpus(page_key, project_key):
        chunk_terms = _tokens(chunk.text) - _CJK_STOPWORDS
        shared_terms = query_terms & chunk_terms
        overlap = len(shared_terms)
        shared_ascii = {term for term in shared_terms if term.isascii()}
        shared_bigrams = query_bigrams & _cjk_bigrams(chunk.text)
        # Require at least two overlapping terms so a single common CJK character
        # does not make every question "grounded". CJK matches must additionally
        # preserve adjacency: scattered characters such as 解/理 in "量子纠缠的原理"
        # must not match an unrelated chunk containing "理解".
        if overlap < 2 or (not shared_ascii and not shared_bigrams):
            continue
        # Light length normalization so a single strong match does not dominate unfairly.
        score = overlap / (len(chunk_terms) ** 0.5)
        scored.append(Candidate(chunk.doc, chunk.fragment, chunk.text, round(score, 4)))
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]
