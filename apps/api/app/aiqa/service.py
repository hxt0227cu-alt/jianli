"""Answer service orchestration (M6 rounds 1-3).

Pipeline: retrieve grounded chunks (knowledge base via pgvector when available, else the
static page registry) → boundary check (greeting / off-topic refusal, persona voice) →
stream model deltas through the LLM gateway → emit SSE frames exactly as docs/api/sse.md
§3 defines.

Round 2: conversation persistence over the approved 0004 tables — with a valid session
**and** a ``conversation_id`` the user question is stored before the stream and the
assistant answer (with its ``is_offtopic`` flag) afterwards; the ``answer.started`` frame
echoes that ``conversation_id``. Anonymous calls and logged-in calls without a
``conversation_id`` are never persisted.

Round 3: knowledge-base ingestion (md/txt, local-disk storage, pgvector embeddings).
Round 4 (TASK-KB-PDF-001): PDF uploads supported (pypdf text extraction, parse_mode=native)
so the resume PDF itself can be indexed; md/txt stay parse_mode=text; docx stays failed.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
from collections.abc import AsyncIterator, Sequence
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.auth.errors import AuthError
from app.auth.models import Principal

from . import bm25
from .chunking import chunk_text as _chunk_text
from .content import PAGES, PageContentData
from .embeddings import EmbeddingError, EmbeddingGateway
from .gateway import GatewayError, LLMGateway
from .models import (
    Conversation,
    ConversationList,
    KnowledgeDocument,
    KnowledgeDocumentList,
    Message,
    MessageList,
    RecommendationSource,
)
from .persona import GREETING_REPLY, OFFTOPIC_REPLY, build_system_prompt, is_greeting
from .rate_limit import AnswerRateLimiter
from .repository import ConversationRepository, KnowledgeRepository, default_now
from .retrieval import Candidate, retrieve
from .sse import (
    citations_frame,
    completed_frame,
    delta_frame,
    error_frame,
    started_frame,
    tool_calls_frame,
)
from .storage import KnowledgeStorage

_OFFTOPIC_CODE = "OFFTOPIC"
_GREETING_CODE = "GREETING"
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # openapi KnowledgeDocument.size maximum 10485760
_SUPPORTED_TYPES = {"md", "txt", "pdf"}

# Agent tooling (TASK-AGENT-TOOLS-002): the single whitelisted read-only tool. The model
# decides whether to call it and generates its own `query` (tool_choice=auto); the service
# executes it with the existing hybrid retrieval. Booking/write/admin endpoints are never
# registered here (PRD decision #14) — see docs/api/sse.md §3.
_SEARCH_TOOLS: list[dict[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "在站点主人的公开知识库（简历、项目、技术笔记等资料）中检索与用户问题"
                "相关的片段。当问题需要事实依据时调用；请用问题中的关键主题词作为检索词"
                "query（如项目名、技术名、经历关键词），不要整句复制问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "检索词：问题中的关键主题词，例如 'Litchi Copilot'、"
                            "'技术栈'、'腾讯实习'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def _extract_pdf_text(raw: bytes) -> str:
    """Extract text from a PDF via pypdf (TASK-KB-PDF-001)."""

    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ValueError("pypdf is required for PDF parsing") from error
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _format_context(candidates: list[Candidate]) -> str:
    return "\n".join(f"[{c.doc} #{c.fragment}] {c.text}" for c in candidates)


def _conversation_from(row: dict[str, Any]) -> Conversation:
    return Conversation(
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _message_from(row: dict[str, Any]) -> Message:
    return Message(
        id=row["id"],
        role=row["role"],
        content=row["content"],
        is_offtopic=row["is_offtopic"],
        created_at=row["created_at"],
    )


class AnswerService:
    """Per-request orchestration; holds the gateway, rate limiter and optional stores."""

    def __init__(
        self,
        gateway: LLMGateway,
        rate_limiter: AnswerRateLimiter,
        repository: ConversationRepository | None = None,
        embedder: EmbeddingGateway | None = None,
        knowledge_repository: KnowledgeRepository | None = None,
        storage: KnowledgeStorage | None = None,
        min_score: float = 0.0,
    ) -> None:
        self._gateway = gateway
        self._rate_limiter = rate_limiter
        self._repository = repository
        self._embedder = embedder
        self._knowledge_repository = knowledge_repository
        self._storage = storage
        self._min_score = min_score

    # -- synchronous helpers used by the router before streaming -------------------------

    def check_rate_limit(self, ip: str) -> None:
        """Public answer rate limit; raises AuthError 429 on budget exhaustion."""

        self._rate_limiter.consume(ip)

    def page_content(self, page_key: str) -> PageContentData | None:
        return PAGES.get(page_key)

    def recommendations(self, page_key: str) -> tuple[list[str], RecommendationSource]:
        page = PAGES.get(page_key)
        if page is None:
            return [], "fallback"
        return page.recommendations, "fallback"

    # -- conversation endpoints (round 2) -------------------------------------------------

    def _require_repository(self) -> ConversationRepository:
        if self._repository is None:
            raise AuthError(
                "MODEL_UNAVAILABLE", 503, "Conversation storage unavailable", "Retry later"
            )
        return self._repository

    def list_conversations(self, user_id: UUID) -> ConversationList:
        repository = self._require_repository()
        rows = repository.list_conversations(user_id)
        return ConversationList(items=[_conversation_from(row) for row in rows])

    def create_conversation(self, user_id: UUID) -> Conversation:
        repository = self._require_repository()
        row = repository.create_conversation(user_id, default_now())
        return _conversation_from(row)

    def list_messages(self, user_id: UUID, conversation_id: UUID) -> MessageList:
        repository = self._require_repository()
        conversation = repository.get_conversation(conversation_id)
        if conversation is None or conversation.get("deleted_at") is not None:
            raise AuthError(
                "INVALID_REQUEST", 404, "Conversation not found", "Unknown conversation"
            )
        if conversation["user_id"] != user_id:
            raise AuthError(
                "PERM_DENIED", 403, "Forbidden", "Conversation belongs to another user"
            )
        rows = repository.list_messages(conversation_id)
        return MessageList(items=[_message_from(row) for row in rows])

    # -- knowledge-base endpoints (round 3) -----------------------------------------------

    def _require_knowledge(self) -> tuple[KnowledgeRepository, KnowledgeStorage, EmbeddingGateway]:
        if self._knowledge_repository is None or self._storage is None or self._embedder is None:
            raise AuthError("MODEL_UNAVAILABLE", 503, "Knowledge base unavailable", "Retry later")
        return self._knowledge_repository, self._storage, self._embedder

    def list_knowledge_documents(self) -> KnowledgeDocumentList:
        repository, _, _ = self._require_knowledge()
        items: list[KnowledgeDocument] = []
        for row in repository.list_documents():
            items.append(
                KnowledgeDocument(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    size=row["size"],
                    status=row["status"],
                    parse_mode=row.get("parse_mode"),
                    failure_reason=row.get("failure_reason"),
                    created_at=row["created_at"],
                )
            )
        return KnowledgeDocumentList(items=items)

    async def upload_knowledge_documents(self, files: Sequence[Any]) -> None:
        """Parse + index each md/txt/pdf upload (202 semantics; per-file status in list)."""

        repository, storage, embedder = self._require_knowledge()
        now = default_now()
        for file in files:
            filename = (file.filename or "document").rsplit("/", 1)[-1]
            suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if suffix not in {"md", "pdf", "docx", "txt"}:
                continue  # unknown extension: nothing to index
            document_id = uuid4()
            try:
                raw = await file.read()
            except Exception:  # pragma: no cover - defensive
                continue
            checksum = hashlib.sha256(raw).hexdigest()
            try:
                repository.create_document(
                    document_id=document_id,
                    name=filename,
                    doc_type=suffix,
                    size=len(raw),
                    content_checksum=checksum,
                    storage_key=f"knowledge/{document_id}.txt",
                    parse_mode="native" if suffix == "pdf" else "text",
                    now=now,
                )
            except IntegrityError:
                continue  # active checksum duplicate (uq_knowledge_documents_active_checksum)
            if len(raw) > _MAX_UPLOAD_BYTES:
                await asyncio.to_thread(
                    repository.mark_failed, document_id, "file exceeds 10MB limit"
                )
                continue
            if suffix not in _SUPPORTED_TYPES:
                await asyncio.to_thread(
                    repository.mark_failed, document_id, f"{suffix} parsing is not supported in MVP"
                )
                continue
            if suffix == "pdf":
                try:
                    text = await asyncio.to_thread(_extract_pdf_text, raw)
                except Exception as error:  # pypdf failure or corrupt PDF -> failed with reason
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, f"PDF parse failed: {error}"
                    )
                    continue
                if not text.strip():
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, "no extractable text in PDF"
                    )
                    continue
            else:
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    await asyncio.to_thread(
                        repository.mark_failed, document_id, "not valid UTF-8 text"
                    )
                    continue
            storage.save(document_id, text)
            try:
                chunks = _chunk_text(text)
                chunk_texts = [content for _, content in chunks]
                embeddings = embedder.embed(chunk_texts)
            except EmbeddingError as error:
                await asyncio.to_thread(repository.mark_failed, document_id, str(error))
                continue
            await asyncio.to_thread(
                repository.replace_chunks, document_id, chunks, embeddings, default_now()
            )
            await asyncio.to_thread(repository.mark_indexed, document_id)

    def delete_knowledge_document(self, document_id: UUID) -> None:
        repository, storage, _ = self._require_knowledge()
        document = repository.get_document(document_id)
        if document is None:
            raise AuthError("INVALID_REQUEST", 404, "Document not found", "Unknown document")
        repository.disable_retrieval(document_id, default_now())
        storage.delete(document_id)

    # -- streaming pipeline ---------------------------------------------------------------

    async def stream_answer(
        self,
        *,
        question: str,
        page_key: str,
        project_key: str | None,
        principal: Principal | None,
        conversation_id: UUID | None,
    ) -> AsyncIterator[str]:
        """Yield SSE frames for one answer (started → deltas → citations → completed)."""

        persist = (
            principal is not None
            and conversation_id is not None
            and self._repository is not None
        )
        trace_id = str(uuid4())
        seq = 0
        answer_id = str(uuid4())
        yield started_frame(
            seq := seq + 1,
            answer_id,
            str(conversation_id) if persist else None,
            trace_id,
        )

        if persist:
            assert (
                principal is not None
                and conversation_id is not None
                and self._repository is not None
            )
            await asyncio.to_thread(
                self._repository.append_message,
                conversation_id,
                role="user",
                content=question,
                is_offtopic=False,
                now=default_now(),
            )

        deltas: list[str] = []

        # Greeting first (no model round-trip, unchanged policy).
        if is_greeting(question):
            yield delta_frame(seq := seq + 1, GREETING_REPLY, trace_id)
            yield citations_frame(seq := seq + 1, [], trace_id)
            yield completed_frame(
                seq := seq + 1,
                grounded=False,
                offtopic=False,
                model=_GREETING_CODE,
                usage=None,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, GREETING_REPLY, False)
            return

        # Agent tooling (TASK-AGENT-TOOLS-002): two-phase function calling. Phase 1 —
        # the model decides whether to call the whitelisted read-only `search_knowledge`
        # tool and generates its own retrieval terms (`tool_choice=auto`). The service
        # executes the tool, then Phase 2 generates the grounded answer with the results.
        # No-hits always falls back to the existing off-topic refusal (never fabricate).
        _MODEL_ERROR_FRAME: dict[str, object] = {
            "type": "urn:jianli:error:model_unavailable",
            "title": "Model unavailable",
            "status": 503,
            "code": "MODEL_UNAVAILABLE",
            "detail": "The answer service is temporarily unavailable",
        }
        messages1 = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": f"用户问题：{question}"},
        ]
        tool_request: dict[str, object] | None = None
        try:
            async for kind, payload in self._gateway.answer(messages1, tools=_SEARCH_TOOLS):
                if kind == "tool_call" and isinstance(payload, dict):
                    tool_request = payload
                    break
        except GatewayError:
            yield error_frame(seq := seq + 1, _MODEL_ERROR_FRAME, trace_id)
            return

        candidates: list[Candidate] = []
        search_query = question
        if tool_request is not None and tool_request.get("name") == "search_knowledge":
            # Model decided to search: execute the tool with the model-generated query.
            try:
                arguments = json.loads(str(tool_request.get("arguments") or "{}"))
            except json.JSONDecodeError:
                arguments = {}
            search_query = str(arguments.get("query") or question).strip() or question
            candidates = await self._search_candidates(
                search_query, question, page_key, project_key
            )
        else:
            # Model decided not to search (or no tool response): system fallback on the
            # original question keeps grounded semantics stable; no hits -> refusal.
            candidates = await self._search_candidates(
                question, question, page_key, project_key
            )

        if not candidates:
            yield tool_calls_frame(
                seq := seq + 1,
                [
                    {
                        "name": "search_knowledge",
                        "query": search_query,
                        "hits": [],
                    }
                ],
                trace_id,
            )
            yield delta_frame(seq := seq + 1, OFFTOPIC_REPLY, trace_id)
            yield citations_frame(seq := seq + 1, [], trace_id)
            yield completed_frame(
                seq := seq + 1,
                grounded=False,
                offtopic=True,
                model=_OFFTOPIC_CODE,
                usage=None,
                trace_id=trace_id,
            )
            if persist:
                assert conversation_id is not None
                await self._persist_assistant(conversation_id, OFFTOPIC_REPLY, True)
            return

        yield tool_calls_frame(
            seq := seq + 1,
            [
                {
                    "name": "search_knowledge",
                    "query": search_query,
                    "hits": [{"doc": c.doc, "fragment": c.fragment} for c in candidates],
                }
            ],
            trace_id,
        )
        messages2 = [
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": f"用户问题：{question}\n\n【已知资料】\n{_format_context(candidates)}",
            },
        ]
        try:
            async for kind, payload in self._gateway.answer(messages2):
                if kind != "delta" or not isinstance(payload, str):
                    continue
                deltas.append(payload)
                yield delta_frame(seq := seq + 1, payload, trace_id)
        except GatewayError:
            yield error_frame(seq := seq + 1, _MODEL_ERROR_FRAME, trace_id)
            return
        yield citations_frame(
            seq := seq + 1,
            [{"doc": c.doc, "fragment": c.fragment} for c in candidates],
            trace_id,
        )
        yield completed_frame(
            seq := seq + 1,
            grounded=True,
            offtopic=False,
            model=self._gateway.model_name,
            usage=None,
            trace_id=trace_id,
        )
        if persist:
            assert conversation_id is not None
            await self._persist_assistant(conversation_id, "".join(deltas), False)

    async def _search_candidates(
        self,
        primary: str,
        fallback: str,
        page_key: str,
        project_key: str | None,
    ) -> list[Candidate]:
        """Dual-path recall for the agent tool (TASK-AGENT-TOOLS-002).

        ``primary`` is the model-generated query from the tool call; ``fallback`` is the
        raw question. Both are searched (KB hybrid first, then the static page registry)
        and merged de-duplicated, so a sub-optimal model rewrite can never drop evidence
        the literal question would have found — the grounding stays stable under real
        function-calling decisions (evaluation LITERAL/SEMANTIC keep their numbers).

        IMPORTANT: the merged list must NOT be truncated to the primary path's size. A
        model query whose KB top-6 fills the slots would push every fallback candidate
        out (observed in WSL: LITERAL 8/8 -> 6/8 despite dual-path recall). Each path is
        naturally bounded (KB <= 6, static <= 3; KB non-empty skips static), so the
        merged list is at most ~12 — kept whole so the fallback evidence always survives.
        """
        merged: list[Candidate] = []
        seen: set[tuple[str, int]] = set()
        for query in (primary, fallback):
            kb = await self._knowledge_candidates(query)
            static = retrieve(query, page_key, project_key) if not kb else []
            for candidate in [*kb, *static]:
                key = (candidate.doc, candidate.fragment)
                if key not in seen:
                    seen.add(key)
                    merged.append(candidate)
        return merged

    async def _knowledge_candidates(self, question: str) -> list[Candidate]:
        """Chunk-level hybrid retrieval (vector + BM25 fused with RRF, TASK-KB-RAG-001).
        Empty list falls back to static pages."""

        if self._knowledge_repository is None or self._embedder is None or self._storage is None:
            return []
        try:
            vector = (await asyncio.to_thread(self._embedder.embed, [question]))[0]
            vector_hits = await asyncio.to_thread(
                self._knowledge_repository.search_chunks, vector, min_score=self._min_score
            )
            corpus = await asyncio.to_thread(self._knowledge_repository.load_chunk_corpus)
        except EmbeddingError:
            return []
        # P1 relevance threshold (TASK-KB-THRESHOLD-001): no semantically similar chunk
        # -> no evidence. BM25 single-char overlap alone must NOT ground an answer
        # (CJK single chars always overlap), otherwise irrelevant questions would be
        # answered instead of refused.
        if not vector_hits:
            return []
        bm25_hits = bm25.BM25Index(corpus).search(question, top_k=10)
        vector_ids = [str(hit["chunk_id"]) for hit in vector_hits]
        bm25_ids = [chunk_id for chunk_id, _ in bm25_hits]
        fused = bm25.reciprocal_rank_fusion(
            [
                [(chunk_id, 0.0) for chunk_id in vector_ids],
                [(chunk_id, 0.0) for chunk_id in bm25_ids],
            ],
            top_k=6,
        )
        if not fused:
            return []
        details = await asyncio.to_thread(
            self._knowledge_repository.chunk_rows, [chunk_id for chunk_id, _ in fused]
        )
        candidates: list[Candidate] = []
        for chunk_id, _ in fused:
            row = details.get(chunk_id)
            if row is None:
                continue
            candidates.append(
                Candidate(
                    doc=str(row["doc_name"]),
                    fragment=int(row["seq"]),
                    text=str(row["content"]),
                    score=1.0,
                )
            )
        return candidates

    async def _persist_assistant(
        self, conversation_id: UUID, content: str, is_offtopic: bool
    ) -> None:
        if self._repository is None:
            return
        now = default_now()
        await asyncio.to_thread(
            self._repository.append_message,
            conversation_id,
            role="assistant",
            content=content,
            is_offtopic=is_offtopic,
            now=now,
        )
        await asyncio.to_thread(self._repository.touch, conversation_id, now)
