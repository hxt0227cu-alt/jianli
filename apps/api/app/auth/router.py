"""FastAPI routes for the approved authentication contract."""

from __future__ import annotations

from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from .errors import AuthError
from .models import (
    EmailRequest,
    LoginRequest,
    Principal,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRequest,
    UserSummary,
)
from .runtime import AuthRuntime

SESSION_COOKIE = "__Host-session"
CSRF_COOKIE = "__Host-csrf"


def problem_response(error: AuthError, trace_id: str | None = None) -> JSONResponse:
    body: dict[str, object] = {
        "type": f"urn:jianli:error:{error.code.lower()}",
        "title": error.title,
        "status": error.status,
        "code": error.code,
        "detail": error.detail,
        "trace_id": trace_id or str(uuid4()),
    }
    headers: dict[str, str] = {}
    if error.retry_after_seconds is not None:
        body["retry_after_seconds"] = error.retry_after_seconds
        headers["Retry-After"] = str(error.retry_after_seconds)
    return JSONResponse(
        body, status_code=error.status, headers=headers, media_type="application/problem+json"
    )


def _request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    referer = request.headers.get("referer")
    if not referer:
        return None
    parsed = urlsplit(referer)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None


def _require_same_origin(request: Request, runtime: AuthRuntime) -> None:
    if _request_origin(request) not in runtime.allowed_origins:
        raise AuthError("PERM_DENIED", 403, "Origin rejected", "Request origin is not allowed")


def _session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def _principal(request: Request, runtime: AuthRuntime) -> Principal:
    return runtime.service.authenticate(_session_token(request))


def _require_csrf(request: Request, runtime: AuthRuntime) -> str:
    token = _session_token(request)
    if not token:
        raise AuthError("AUTH_EXPIRED", 401, "Authentication required", "Login required")
    _require_same_origin(request, runtime)
    if not runtime.tokens.valid_csrf(
        token,
        request.cookies.get(CSRF_COOKIE),
        request.headers.get("X-CSRF-Token"),
    ):
        raise AuthError("PERM_DENIED", 403, "CSRF rejected", "CSRF validation failed")
    return token


def create_auth_router(runtime: AuthRuntime) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Auth"])

    @router.post("/login", status_code=204, operation_id="login")
    def login(payload: LoginRequest, request: Request, response: Response) -> None:
        _require_same_origin(request, runtime)
        request_id = str(uuid4())
        request.state.auth_request_id = request_id
        ip = request.client.host if request.client else "unknown"
        grant = runtime.service.login(
            payload.email,
            payload.password,
            payload.remember_me,
            ip,
            request.headers.get("user-agent"),
            _session_token(request),
            request_id,
        )
        response.set_cookie(
            SESSION_COOKIE,
            grant.token,
            max_age=grant.max_age_seconds,
            secure=True,
            httponly=True,
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            CSRF_COOKIE,
            grant.csrf_token,
            max_age=grant.max_age_seconds,
            secure=True,
            httponly=False,
            samesite="lax",
            path="/",
        )
        response.headers["X-CSRF-Token"] = grant.csrf_token

    @router.post("/logout", status_code=204, operation_id="logout")
    def logout(request: Request, response: Response) -> None:
        token = _require_csrf(request, runtime)
        runtime.service.logout(token)
        response.delete_cookie(SESSION_COOKIE, secure=True, httponly=True, samesite="lax", path="/")
        response.delete_cookie(CSRF_COOKIE, secure=True, httponly=False, samesite="lax", path="/")

    @router.get("/me", response_model=UserSummary, operation_id="getCurrentUser")
    def current_user(request: Request) -> UserSummary:
        return UserSummary.model_validate(_principal(request, runtime), from_attributes=True)

    @router.post("/register", status_code=202, operation_id="registerInterviewer")
    def register(payload: RegisterRequest, request: Request) -> None:
        # Anonymous entry point: same-origin only, no session/CSRF required.
        # Returns 202 (generic); a verification email is queued when SMTP is configured.
        _require_same_origin(request, runtime)
        ip = request.client.host if request.client else "unknown"
        runtime.service.register(payload.email, payload.password, ip)

    @router.post("/verify-email", status_code=204, operation_id="verifyEmail")
    def verify_email(payload: TokenRequest, request: Request) -> None:
        _require_same_origin(request, runtime)
        runtime.service.verify_email(payload.token)

    @router.post(
        "/password-reset/request", status_code=202, operation_id="requestPasswordReset"
    )
    def request_password_reset(payload: EmailRequest, request: Request) -> None:
        # Anonymous entry point: same-origin only. Always 202; never reveals existence.
        _require_same_origin(request, runtime)
        ip = request.client.host if request.client else "unknown"
        runtime.service.request_password_reset(payload.email, ip)

    @router.post("/password-reset/confirm", status_code=204, operation_id="confirmPasswordReset")
    def confirm_password_reset(payload: ResetPasswordRequest, request: Request) -> None:
        _require_same_origin(request, runtime)
        runtime.service.reset_password(payload.token, payload.new_password)

    return router
