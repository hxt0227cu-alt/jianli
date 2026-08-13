"""FastAPI routes for the approved Answer domain contract.

Operations (docs/api/openapi.yaml + docs/api/sse.md §3):

* ``GET /pages/{page_key}`` — public page content (no auth).
* ``GET /pages/{page_key}/recommendations`` — cached-or-fallback suggested questions.
* ``POST /answers:stream`` — SSE grounded answer. Anonymous calls omit the session cookie
  and are never persisted; a present cookie must resolve to a valid session (401 otherwise)
  and then satisfy same-origin + CSRF (403 otherwise). Anonymous requests carrying
  ``conversation_id`` are rejected with 401. Public answer rate limiting applies always.
* ``GET /conversations`` / ``POST /conversations`` / ``GET /conversations/{id}/messages``
  (round 2, over the approved 0004 tables): session-required; POST enforces CSRF; message
  history is owner-only (403 otherwise).

Persistence rule: a valid session AND a ``conversation_id`` are both required for the
answer to be stored (``answer.started.conversation_id`` echoes the value then); otherwise
the stream is anonymous and never persisted.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.auth.errors import AuthError
from app.auth.models import Principal
from app.auth.router import SESSION_COOKIE, _principal, _require_csrf
from app.auth.runtime import AuthRuntime

from .models import (
    AnswerRequest,
    Conversation,
    ConversationList,
    KnowledgeDocumentList,
    MessageList,
    PageContent,
    RecommendedQuestions,
)
from .service import AnswerService

_VALID_PAGE_KEYS = ("resume", "projects")
_MAX_UPLOAD_FILES = 20  # openapi uploadKnowledgeDocuments files.maxItems


def create_aiqa_router(auth_runtime: AuthRuntime | None, service: AnswerService) -> APIRouter:
    """Mount the Answer domain. Public routes work with no auth; session routes need it."""

    router = APIRouter(tags=["Public", "Answer"])

    def _optional_principal(request: Request) -> Principal | None:
        """Valid session → principal; no cookie → None (anonymous); invalid cookie → 401."""

        if auth_runtime is None:
            return None
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return None
        return auth_runtime.service.authenticate(token)

    def _require_session(request: Request) -> Principal:
        if auth_runtime is None:
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "interviewer")

    def _session_with_csrf(request: Request) -> Principal:
        if auth_runtime is None:
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
        _require_csrf(request, auth_runtime)
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "interviewer")

    def _admin_session(request: Request) -> Principal:
        if auth_runtime is None:
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "owner_admin")

    def _admin_write(request: Request) -> Principal:
        if auth_runtime is None:
            raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
        _require_csrf(request, auth_runtime)
        return auth_runtime.service.require_role(_principal(request, auth_runtime), "owner_admin")

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
                principal=principal,
                conversation_id=payload.conversation_id,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
        )

    # -- conversation endpoints (round 2) -------------------------------------------------

    @router.get(
        "/conversations", response_model=ConversationList, operation_id="listConversations"
    )
    def list_conversations(request: Request) -> ConversationList:
        return service.list_conversations(_require_session(request).id)

    @router.post(
        "/conversations",
        response_model=Conversation,
        status_code=201,
        operation_id="createConversation",
    )
    def create_conversation(request: Request) -> Conversation:
        return service.create_conversation(_session_with_csrf(request).id)

    @router.get(
        "/conversations/{conversation_id}/messages",
        response_model=MessageList,
        operation_id="listConversationMessages",
    )
    def list_conversation_messages(conversation_id: UUID, request: Request) -> MessageList:
        return service.list_messages(_require_session(request).id, conversation_id)

    # -- knowledge-base endpoints (round 3, owner_admin) ----------------------------------

    @router.get(
        "/admin/knowledge-documents",
        response_model=KnowledgeDocumentList,
        operation_id="listKnowledgeDocuments",
    )
    def list_knowledge_documents(request: Request) -> KnowledgeDocumentList:
        _admin_session(request)
        return service.list_knowledge_documents()

    @router.post(
        "/admin/knowledge-documents",
        status_code=202,
        operation_id="uploadKnowledgeDocuments",
    )
    async def upload_knowledge_documents(
        request: Request,
        files: Annotated[list[UploadFile], File(description="md/txt documents")],
    ) -> None:
        _admin_write(request)
        if len(files) > _MAX_UPLOAD_FILES:
            raise AuthError("INVALID_REQUEST", 400, "Too many files", "max 20 files per request")
        await service.upload_knowledge_documents(files)

    @router.delete(
        "/admin/knowledge-documents/{document_id}",
        status_code=204,
        operation_id="deleteKnowledgeDocument",
    )
    def delete_knowledge_document(document_id: UUID, request: Request) -> None:
        _admin_write(request)
        service.delete_knowledge_document(document_id)

    return router
