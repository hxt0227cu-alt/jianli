"""FastAPI routes for the approved Answer domain contract (M6 round 1).

Three operations (docs/api/openapi.yaml + docs/api/sse.md §3):

* ``GET /pages/{page_key}`` — public page content (no auth).
* ``GET /pages/{page_key}/recommendations`` — cached-or-fallback suggested questions.
* ``POST /answers:stream`` — SSE grounded answer. Anonymous calls omit the session cookie
  and are never persisted; a present cookie must resolve to a valid session (401 otherwise)
  and then satisfy same-origin + CSRF (403 otherwise). Anonymous requests carrying
  ``conversation_id`` are rejected with 401. Public answer rate limiting applies always.

Round 1 never persists conversations: ``answer.started.conversation_id`` is always null and
DB-backed conversation APIs (``listConversations``/``createConversation``/
``listConversationMessages``) are intentionally not mounted yet (TASK-M6-DB, round 2).
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.auth.errors import AuthError
from app.auth.models import Principal
from app.auth.router import SESSION_COOKIE, _require_csrf
from app.auth.runtime import AuthRuntime

from .models import AnswerRequest, PageContent, RecommendedQuestions
from .service import AnswerService

_VALID_PAGE_KEYS = ("resume", "projects")


def create_aiqa_router(auth_runtime: AuthRuntime | None, service: AnswerService) -> APIRouter:
    """Mount the Answer domain. Public by contract; auth runtime may be absent."""

    router = APIRouter(tags=["Public", "Answer"])

    def _optional_principal(request: Request) -> Principal | None:
        """Valid session → principal; no cookie → None (anonymous); invalid cookie → 401."""

        if auth_runtime is None:
            return None
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return None
        return auth_runtime.service.authenticate(token)

    def _require_page_key(page_key: str) -> None:
        if page_key not in _VALID_PAGE_KEYS:
            raise AuthError(
                "INVALID_REQUEST", 400, "Unknown page", "page_key must be resume or projects"
            )

    @router.get("/pages/{page_key}", response_model=PageContent, operation_id="getPageContent")
    def page_content(page_key: str) -> PageContent:
        _require_page_key(page_key)
        data = service.page_content(page_key)
        if data is None:  # registry invariant; defensive
            raise AuthError("INVALID_REQUEST", 400, "Unknown page", "page content is unavailable")
        return PageContent(
            page_key=data.page_key,
            title=data.title,
            sections=data.sections,
            updated_at=data.updated_at,
        )

    @router.get(
        "/pages/{page_key}/recommendations",
        response_model=RecommendedQuestions,
        operation_id="listRecommendedQuestions",
    )
    def recommended_questions(page_key: str) -> RecommendedQuestions:
        _require_page_key(page_key)
        items, source = service.recommendations(page_key)
        return RecommendedQuestions(items=items, source=source)

    @router.post("/answers:stream", operation_id="streamAnswer")
    def stream_answer(payload: AnswerRequest, request: Request) -> StreamingResponse:
        principal = _optional_principal(request)
        if principal is None:
            if payload.conversation_id is not None:
                raise AuthError(
                    "AUTH_EXPIRED",
                    401,
                    "Authentication required",
                    "conversation_id requires a valid session",
                )
        else:
            assert auth_runtime is not None  # non-None principal implies a configured runtime
            _require_csrf(request, auth_runtime)
        ip = request.client.host if request.client else "unknown"
        service.check_rate_limit(ip)
        return StreamingResponse(
            service.stream_answer(
                question=payload.question,
                page_key=payload.page_key,
                project_key=payload.project_key,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
        )

    return router
