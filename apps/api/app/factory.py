"""FastAPI application factory."""

from __future__ import annotations

import json
import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

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


def create_app(
    settings: Settings | None = None,
    auth_runtime: AuthRuntime | None = None,
) -> FastAPI:
    """Create the application and mount auth only with complete secure dependencies."""

    config = settings or Settings.from_env()
    app = FastAPI(title=config.app_title, version=config.app_version)
    runtime = auth_runtime or (build_auth_runtime(config) if config.auth_configured else None)
    allowed_origins = (
        runtime.allowed_origins if runtime is not None else frozenset(config.allowed_origins)
    )
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

    @app.exception_handler(AuthError)
    async def handle_auth_error(request: Request, error: AuthError) -> JSONResponse:
        request_id = getattr(request.state, "auth_request_id", str(uuid4()))
        _log_auth_rejection(request, error.code, request_id)
        return problem_response(error, request_id)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        if request.url.path.startswith("/auth/"):
            _log_auth_rejection(request, "VALIDATION_FAILED", str(uuid4()))
        return await request_validation_exception_handler(request, error)

    return app
