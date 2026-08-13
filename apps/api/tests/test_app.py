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
    # Without auth settings the app exposes exactly the Answer domain surface: pages,
    # recommendations, the anonymous answer stream, and (routed but 401 without a
    # session) the conversation and knowledge-document endpoints.
    assert set(app.openapi()["paths"]) == {
        "/pages/{page_key}",
        "/pages/{page_key}/recommendations",
        "/answers:stream",
        "/conversations",
        "/conversations/{conversation_id}/messages",
        "/admin/knowledge-documents",
        "/admin/knowledge-documents/{document_id}",
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
        "/conversations",
        "/conversations/{conversation_id}/messages",
        "/admin/knowledge-documents",
        "/admin/knowledge-documents/{document_id}",
    }


def test_api_entrypoint_runs_configured_app(monkeypatch) -> None:
    calls: list[tuple[FastAPI, str, int, object]] = []

    def fake_run(app: FastAPI, *, host: str, port: int, log_config: object) -> None:
        calls.append((app, host, port, log_config))

    monkeypatch.setattr(main.uvicorn, "run", fake_run)

    main.run()

    assert calls == [(main.app, main.settings.api_host, main.settings.api_port, None)]
