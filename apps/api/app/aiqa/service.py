"""Answer service orchestration (M6 round 1).

Pipeline: retrieve grounded chunks from the static page registry → boundary check
(greeting / off-topic refusal, persona voice) → stream model deltas through the LLM
gateway → emit SSE frames exactly as docs/api/sse.md §3 defines.

Round-1 scope is deliberately narrow: nothing here persists (no conversations tables yet)
and nothing touches the database. The knowledge source and retrieval are swappable behind
stable functions so rounds 2/3 (conversation persistence, DB-backed knowledge ingestion,
vector retrieval) extend this file without changing its public methods.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from .content import PAGES, PageContentData
from .gateway import GatewayError, LLMGateway
from .models import RecommendationSource
from .persona import GREETING_REPLY, OFFTOPIC_REPLY, build_system_prompt, is_greeting
from .rate_limit import AnswerRateLimiter
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


class AnswerService:
    """Stateless per-request orchestration; holds the gateway and public rate limiter."""

    def __init__(self, gateway: LLMGateway, rate_limiter: AnswerRateLimiter) -> None:
        self._gateway = gateway
        self._rate_limiter = rate_limiter

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

    # -- streaming pipeline ---------------------------------------------------------------

    async def stream_answer(
        self,
        *,
        question: str,
        page_key: str,
        project_key: str | None,
    ) -> AsyncIterator[str]:
        """Yield SSE frames for one answer (started → deltas → citations → completed)."""

        trace_id = str(uuid4())
        seq = 0
        answer_id = str(uuid4())
        yield started_frame(seq := seq + 1, answer_id, None, trace_id)

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
