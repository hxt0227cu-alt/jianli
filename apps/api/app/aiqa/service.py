"""Answer service orchestration (M6 rounds 1-2).

Pipeline: retrieve grounded chunks from the static page registry → boundary check
(greeting / off-topic refusal, persona voice) → stream model deltas through the LLM
gateway → emit SSE frames exactly as docs/api/sse.md §3 defines.

Round 2 adds conversation persistence over the approved 0004 tables: with a valid
session **and** a ``conversation_id`` the user question is stored before the stream and
the assistant answer (with its ``is_offtopic`` flag) afterwards; the ``answer.started``
frame echoes that ``conversation_id``. Anonymous calls and logged-in calls without a
``conversation_id`` are never persisted.

Handoff note for Codex: round 3 (knowledge ingestion) plugs a document repository and a
vector/full-text retriever into this same service; the public methods keep their shape.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

from app.auth.errors import AuthError
from app.auth.models import Principal

from .content import PAGES, PageContentData
from .gateway import GatewayError, LLMGateway
from .models import Conversation, ConversationList, Message, MessageList, RecommendationSource
from .persona import GREETING_REPLY, OFFTOPIC_REPLY, build_system_prompt, is_greeting
from .rate_limit import AnswerRateLimiter
from .repository import ConversationRepository, default_now
from .retrieval import Candidate, retrieve
from .sse import (
    citations_frame,
    completed_frame,
    delta_frame,
    error_frame,
    started_frame,
)

_OFFTOPIC_CODE = "OFFTOPIC"
_GREETING_CODE = "GREETING"


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
    """Per-request orchestration; holds the gateway, rate limiter and (optional) repository."""

    def __init__(
        self,
        gateway: LLMGateway,
        rate_limiter: AnswerRateLimiter,
        repository: ConversationRepository | None = None,
    ) -> None:
        self._gateway = gateway
        self._rate_limiter = rate_limiter
        self._repository = repository

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
        candidates = retrieve(question, page_key, project_key)
        if candidates:
            messages = [
                {"role": "system", "content": build_system_prompt()},
                {
                    "role": "user",
                    "content": (
                        f"用户问题：{question}\n\n【已知资料】\n{_format_context(candidates)}"
                    ),
                },
            ]
            try:
                async for delta in self._gateway.answer(messages):
                    deltas.append(delta)
                    yield delta_frame(seq := seq + 1, delta, trace_id)
            except GatewayError:
                yield error_frame(
                    seq := seq + 1,
                    {
                        "type": "urn:jianli:error:model_unavailable",
                        "title": "Model unavailable",
                        "status": 503,
                        "code": "MODEL_UNAVAILABLE",
                        "detail": "The answer service is temporarily unavailable",
                    },
                    trace_id,
                )
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
            return

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

        # Off-topic: persona-styled refusal, no model round-trip (boundary policy).
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
