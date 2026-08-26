"""Runtime wiring for the Answer domain (M6 rounds 1-3).

No new dependencies: the service is built from the static page registry, a pure-Python
retriever, the persona layer and an LLM gateway picked by configuration (OpenAI-compatible
when ``JIANLI_LLM_*`` is set, otherwise the deterministic stub). When an SQLAlchemy engine
is supplied (the auth runtime's engine when auth is configured), conversation persistence
(round 2) and the pgvector knowledge base (round 3) are wired in over the approved
0004/0005 schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Engine

from app.config import Settings

from .embeddings import build_embedding_gateway
from .gateway import build_gateway
from .rate_limit import AnswerRateLimiter
from .repository import ConversationRepository, KnowledgeRepository
from .service import AnswerService
from .storage import KnowledgeStorage

if TYPE_CHECKING:
    from app.appointments.service import BookingService


def build_aiqa_runtime(
    settings: Settings,
    engine: Engine | None = None,
    booking_service: BookingService | None = None,
) -> AnswerService:
    """Construct the Answer service; pass ``engine`` to enable DB-backed features.

    ``booking_service`` (the appointments domain's BookingService) is injected so the
    agent can autonomously book interviews in-process (TASK-AIQA-BOOKING-001). It is
    optional: when None the booking tool yields a graceful "unavailable" outcome.
    """

    gateway = build_gateway(
        base_url=settings.llm_base_url,
        api_key=(
            settings.llm_api_key.get_secret_value()
            if settings.llm_api_key is not None
            else None
        ),
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
    embedder = build_embedding_gateway(
        base_url=settings.llm_embedding_base_url,
        api_key=(
            settings.llm_embedding_api_key.get_secret_value()
            if settings.llm_embedding_api_key is not None
            else None
        ),
        model=settings.llm_embedding_model,
        dimension=settings.llm_embedding_dim,
        timeout=settings.llm_timeout_seconds,
    )
    repository = ConversationRepository(engine) if engine is not None else None
    knowledge_repository = KnowledgeRepository(engine) if engine is not None else None
    storage = KnowledgeStorage(settings.knowledge_storage_dir)
    return AnswerService(
        gateway,
        AnswerRateLimiter(),
        repository,
        embedder,
        knowledge_repository,
        storage,
        min_score=settings.kb_min_score or 0.0,
        booking_service=booking_service,
    )
