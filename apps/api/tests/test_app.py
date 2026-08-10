import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.factory import create_app


def test_factory_uses_settings_and_has_no_project_routes() -> None:
    app = create_app(Settings(app_title="Test API", app_version="9.9.9"))

    assert isinstance(app, FastAPI)
    assert app.title == "Test API"
    assert app.version == "9.9.9"
    assert app.openapi()["paths"] == {}


@pytest.mark.asyncio
async def test_framework_openapi_endpoint_starts_without_custom_paths() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["paths"] == {}
