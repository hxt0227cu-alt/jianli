"""Runtime wiring for the Answer domain (M6 round 1).

No database and no new dependencies: the service is built from the static page registry,
a pure-Python retriever, the persona layer and an LLM gateway picked by configuration
(OpenAI-compatible when ``JIANLI_LLM_*`` is set, otherwise the deterministic stub).
"""

from __future__ import annotations

from app.config import Settings

from .gateway import build_gateway
from .rate_limit import AnswerRateLimiter
from .service import AnswerService


def build_aiqa_runtime(settings: Settings) -> AnswerService:
    """Construct the Answer service from settings (stub gateway when no LLM is configured)."""

    gateway = build_gateway(
        base_url=settings.llm_base_url,
        api_key=(
            settings.llm_api_key.get_secret_value()
            if settings.llm_api_key is not None
            else None
        ),
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
    )
    return AnswerService(gateway, AnswerRateLimiter())
