"""FastAPI application factory."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .admin.router import create_admin_router
from .aiqa.router import create_aiqa_router
from .aiqa.runtime import build_aiqa_runtime
from .appointments.router import create_appointment_router
from .appointments.runtime import build_booking_runtime
from .appointments.service import BookingService
from .auth.errors import AuthError
from .auth.router import create_auth_router, problem_response
from .auth.runtime import AuthRuntime, build_auth_runtime
from .config import Settings

SECURITY_LOGGER = logging.getLogger("jianli.security.auth")


def _ip_prefix(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    return ip.rsplit(".", 1)[0] if "." in ip else ip[:19]


def _log_auth_rejection(request: Request, result: str, request_id: str) -> None:
    SECURITY_LOGGER.warning(
        json.dumps(
            {
                "event": "auth_rejected",
                "account_id": "unknown",
                "request_id": request_id,
                "result": result,
                "ip_prefix": _ip_prefix(request),
            },
            separators=(",", ":"),
        )
    )


def _validated_origins(origins: frozenset[str]) -> frozenset[str]:
    normalized: set[str] = set()
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            origin == "*"
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("allowed origins must be explicit HTTP(S) origins without paths")
        normalized.add(f"{parsed.scheme}://{parsed.netloc}")
    return frozenset(normalized)


def create_app(
    settings: Settings | None = None,
    auth_runtime: AuthRuntime | None = None,
    booking_runtime: BookingService | None = None,
) -> FastAPI:
    """Create the application and mount auth only with complete secure dependencies."""

    config = settings or Settings.from_env()
    app = FastAPI(title=config.app_title, version=config.app_version)
    runtime = auth_runtime or (build_auth_runtime(config) if config.auth_configured else None)
    allowed_origins = _validated_origins(
        runtime.allowed_origins if runtime is not None else frozenset(config.allowed_origins)
    )
    if runtime is not None:
        runtime.allowed_origins = allowed_origins
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=sorted(allowed_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "Last-Event-ID"],
        )
    if runtime is not None:
        app.state.auth_runtime = runtime
        app.include_router(create_auth_router(runtime))
        appointments = booking_runtime or (
            build_booking_runtime(config, runtime) if config.booking_configured else None
        )
        if appointments is not None:
            app.state.booking_runtime = appointments
            app.include_router(create_appointment_router(runtime, appointments))
            app.include_router(create_admin_router(runtime, appointments))

    # AI QA domain is public by contract: mounted for every configuration. Anonymous
    # answers never require a session; a present-but-invalid cookie still resolves to a
    # 401 via the (optional) auth runtime. When auth is configured its engine is shared so
    # round-2 conversation persistence works; otherwise the service stays memory-only.
    aiqa_service = build_aiqa_runtime(
        config,
        runtime.engine if runtime is not None else None,
        booking_service=appointments,
    )
    app.include_router(create_aiqa_router(runtime, aiqa_service))

    @app.exception_handler(AuthError)
    async def handle_auth_error(request: Request, error: AuthError) -> JSONResponse:
        request_id = getattr(request.state, "auth_request_id", str(uuid4()))
        _log_auth_rejection(request, error.code, request_id)
        return problem_response(error, request_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        if not (
            request.url.path.startswith("/auth/")
            or request.url.path == "/slots/snapshot"
            or request.url.path == "/appointment-confirmations"
            or request.url.path == "/appointments"
            or request.url.path == "/answers:stream"
            or request.url.path.startswith("/pages/")
        ):
            return await request_validation_exception_handler(request, error)
        request_id = str(uuid4())
        _log_auth_rejection(request, "INVALID_REQUEST", request_id)
        return problem_response(
            AuthError(
                "INVALID_REQUEST",
                422,
                "Invalid request",
                "Request validation failed",
            ),
            request_id,
        )

    return app
