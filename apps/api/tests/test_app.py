import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import main
from app.config import Settings
from app.factory import create_app


def test_factory_uses_settings_and_mounts_only_public_routes() -> None:
    app = create_app(Settings(app_title="Test API", app_version="9.9.9"))

    assert isinstance(app, FastAPI)
    assert app.title == "Test API"
    assert app.version == "9.9.9"
    # Without auth settings the app exposes exactly the public Answer domain (M6 round 1):
    # page content, recommended questions and the anonymous answer stream.
    assert set(app.openapi()["paths"]) == {
        "/pages/{page_key}",
        "/pages/{page_key}/recommendations",
        "/answers:stream",
    }


@pytest.mark.asyncio
async def test_framework_openapi_endpoint_lists_public_paths() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert set(response.json()["paths"]) == {
        "/pages/{page_key}",
        "/pages/{page_key}/recommendations",
        "/answers:stream",
    }


def test_api_entrypoint_runs_configured_app(monkeypatch) -> None:
    calls: list[tuple[FastAPI, str, int, object]] = []

    def fake_run(app: FastAPI, *, host: str, port: int, log_config: object) -> None:
        calls.append((app, host, port, log_config))

    monkeypatch.setattr(main.uvicorn, "run", fake_run)

    main.run()

    assert calls == [(main.app, main.settings.api_host, main.settings.api_port, None)]
