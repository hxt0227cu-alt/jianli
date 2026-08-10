"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an app with framework defaults and no project-defined public routes."""

    config = settings or Settings.from_env()
    return FastAPI(title=config.app_title, version=config.app_version)
