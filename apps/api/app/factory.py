"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth.errors import AuthError
from .auth.router import create_auth_router, problem_response
from .auth.runtime import AuthRuntime, build_auth_runtime
from .config import Settings


def create_app(
    settings: Settings | None = None,
    auth_runtime: AuthRuntime | None = None,
) -> FastAPI:
    """Create the application and mount auth only with complete secure dependencies."""

    config = settings or Settings.from_env()
    app = FastAPI(title=config.app_title, version=config.app_version)
    runtime = auth_runtime or (build_auth_runtime(config) if config.auth_configured else None)
    if runtime is not None:
        app.state.auth_runtime = runtime
        app.include_router(create_auth_router(runtime))

    @app.exception_handler(AuthError)
    async def handle_auth_error(_request: Request, error: AuthError) -> JSONResponse:
        return problem_response(error)

    return app
