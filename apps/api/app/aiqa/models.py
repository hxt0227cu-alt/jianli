"""Request/response models for the AI QA (Answer) domain.

Mirrors ``docs/api/openapi.yaml``: ``AnswerRequest`` + SSE frame contract (docs/api/sse.md
§3) from round 1; conversation models (``Conversation`` / ``Message``) added in round 2
over the approved 0004 tables. Rounds are gated by ``TASK-M6-DB`` (approved 2026-08-13).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PageKey = Literal["resume", "projects"]
ProjectKey = Literal["jianli", "sleep202603_an"]
RecommendationSource = Literal["cache", "fallback"]


class AnswerRequest(BaseModel):
    """POST /answers:stream body. ``extra="forbid"`` keeps the contract strict."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    page_key: PageKey
    project_key: ProjectKey | None = None
    conversation_id: UUID | None = None


class PageContent(BaseModel):
    """Response of ``getPageContent`` (docs/api/openapi.yaml ``PageContent``)."""

    page_key: str
    title: str
    sections: list[dict[str, object]]
    updated_at: datetime


class RecommendedQuestions(BaseModel):
    """Response of ``listRecommendedQuestions`` (cache or static fallback)."""

    items: list[str]
    source: RecommendationSource


class Conversation(BaseModel):
    """Response of ``listConversations`` items / ``createConversation``."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationList(BaseModel):
    items: list[Conversation]


class Message(BaseModel):
    """Response of ``listConversationMessages`` items."""

    id: UUID
    role: Literal["user", "assistant"]
    content: str
    is_offtopic: bool = False
    created_at: datetime


class MessageList(BaseModel):
    items: list[Message]
