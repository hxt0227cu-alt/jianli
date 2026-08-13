"""Request/response models for the AI QA (Answer) domain, M6 round 1.

Mirrors ``docs/api/openapi.yaml`` ``AnswerRequest`` and the SSE frame contract in
``docs/api/sse.md`` §3. No new tables are introduced in round 1: the knowledge source
is the static page registry in ``.content`` and retrieval is pure-Python (see
``.retrieval``). Conversation persistence and DB-backed knowledge ingestion are later
rounds gated by ``TASK-M6-DB``.
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
