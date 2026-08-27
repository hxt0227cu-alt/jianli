"""TC-OPS-010: privacy-safe metrics and deployable observability assets."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app
from app.observability import observe_agent_tool, observe_rerank

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_observability_is_opt_in() -> None:
    with TestClient(create_app(Settings())) as client:
        assert client.get("/internal/metrics").status_code == 404


def test_metrics_are_hidden_low_cardinality_and_content_free() -> None:
    marker = "PRIVATE-MARKER-7f918b"
    app = create_app(Settings(observability_enabled=True))

    with TestClient(app) as client:
        response = client.get("/pages/resume/recommendations")
        assert response.status_code == 200
        answer = client.post(
            "/answers:stream",
            json={"question": f"你好 {marker}", "page_key": "resume"},
        )
        assert answer.status_code == 200
        observe_agent_tool(marker, "blocked", 1)
        observe_rerank("completed", 8, 6, model=marker)
        metrics = client.get("/internal/metrics")

    assert metrics.status_code == 200
    body = metrics.text
    assert 'route="/pages/{page_key}/recommendations"' in body
    assert 'outcome="greeting"' in body
    assert 'status="blocked",tool="rejected_unknown"' in body
    assert 'jianli_aiqa_rerank_attempts_total{status="completed"}' in body
    assert marker not in body
    assert "resume/recommendations" not in body
    assert "/internal/metrics" not in app.openapi()["paths"]


def test_observability_environment_settings() -> None:
    settings = Settings.from_env(
        {
            "JIANLI_OBSERVABILITY_ENABLED": "true",
            "JIANLI_OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318/v1/traces",
            "JIANLI_OTEL_SERVICE_NAME": "portfolio-agent",
        }
    )
    assert settings.observability_enabled is True
    assert settings.otel_exporter_otlp_endpoint == "http://collector:4318/v1/traces"
    assert settings.otel_service_name == "portfolio-agent"


def test_deployment_assets_keep_internal_surfaces_private() -> None:
    nginx_http = (REPO_ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")
    nginx_https = (REPO_ROOT / "deploy/nginx-https.conf.template").read_text(
        encoding="utf-8"
    )
    dev_compose = (REPO_ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
    prod_compose = (REPO_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    dashboard = json.loads(
        (REPO_ROOT / "deploy/observability/grafana/dashboards/agent-overview.json").read_text(
            encoding="utf-8"
        )
    )

    assert "location = /internal/metrics { return 404; }" in nginx_http
    assert nginx_https.count("location = /internal/metrics { return 404; }") == 2
    assert '"127.0.0.1:3000:3000"' in dev_compose
    assert '"127.0.0.1:3000:3000"' in prod_compose
    assert '"127.0.0.1:9090:9090"' in prod_compose
    assert len(dashboard["panels"]) == 8
    expressions = " ".join(
        target["expr"] for panel in dashboard["panels"] for target in panel["targets"]
    )
    assert "jianli_aiqa_answers_total" in expressions
    assert "jianli_aiqa_tool_calls_total" in expressions
    assert "jianli_aiqa_rerank_attempts_total" in expressions
