"""Low-cardinality metrics and privacy-safe OpenTelemetry tracing."""

from __future__ import annotations

import time
from typing import Literal

from fastapi import FastAPI, Response
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Settings

REGISTRY = CollectorRegistry(auto_describe=True)
HTTP_REQUESTS = Counter(
    "jianli_http_requests",
    "Completed HTTP requests",
    ("method", "route", "status"),
    registry=REGISTRY,
)
HTTP_DURATION = Histogram(
    "jianli_http_request_duration_seconds",
    "HTTP request duration including streamed response bodies",
    ("method", "route"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
    registry=REGISTRY,
)
AIQA_ANSWERS = Counter(
    "jianli_aiqa_answers",
    "AIQA terminal outcomes",
    ("outcome",),
    registry=REGISTRY,
)
AIQA_DURATION = Histogram(
    "jianli_aiqa_answer_duration_seconds",
    "AIQA end-to-end answer duration",
    ("outcome",),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
    registry=REGISTRY,
)
AIQA_TOKENS = Counter(
    "jianli_aiqa_tokens",
    "Model tokens reported by the gateway",
    ("kind",),
    registry=REGISTRY,
)
AIQA_TOOL_CALLS = Counter(
    "jianli_aiqa_tool_calls",
    "Allowlisted Agent tool outcomes",
    ("tool", "status"),
    registry=REGISTRY,
)
AIQA_RERANK = Counter(
    "jianli_aiqa_rerank_attempts",
    "Cross-Encoder rerank outcomes",
    ("status",),
    registry=REGISTRY,
)
AIQA_RERANK_DURATION = Histogram(
    "jianli_aiqa_rerank_duration_seconds",
    "Cross-Encoder rerank duration",
    ("status",),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5),
    registry=REGISTRY,
)
AIQA_SEMANTIC_CACHE = Counter(
    "jianli_aiqa_semantic_cache",
    "Semantic answer cache outcomes",
    ("status",),
    registry=REGISTRY,
)
AIQA_SEMANTIC_CACHE_DURATION = Histogram(
    "jianli_aiqa_semantic_cache_duration_seconds",
    "Semantic answer cache operation duration",
    ("status",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
    registry=REGISTRY,
)
AIQA_CIRCUIT_BREAKER = Counter(
    "jianli_aiqa_circuit_breaker",
    "AI provider circuit breaker transitions and rejections",
    ("component", "event"),
    registry=REGISTRY,
)

AnswerOutcome = Literal["grounded", "offtopic", "greeting", "tool", "error"]
ToolStatus = Literal["completed", "blocked", "failed"]
RerankStatus = Literal["completed", "fallback", "disabled"]
SemanticCacheStatus = Literal["hit", "miss", "bypass", "error", "invalidated"]
CircuitComponent = Literal["llm", "reranker"]
CircuitEvent = Literal["opened", "rejected", "recovered"]
_TOOLS = {
    "search_knowledge",
    "request_interview_booking",
    "list_my_appointments",
    "cancel_appointment",
    "reschedule_appointment",
}
_enabled = False
_provider: TracerProvider | None = None


class ObservabilityMiddleware:
    """Measure the complete ASGI response and emit a normalized server span."""

    def __init__(self, app: ASGIApp, tracer: Tracer) -> None:
        self.app = app
        self.tracer = tracer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = str(scope.get("method", "UNKNOWN")).upper()
        status_code = 500
        started = time.monotonic()
        carrier = dict(Headers(scope=scope).items())
        parent = propagate.extract(carrier)

        async def capture(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        with self.tracer.start_as_current_span(
            f"HTTP {method}", context=parent, kind=SpanKind.SERVER
        ) as span:
            try:
                await self.app(scope, receive, capture)
            except Exception:
                span.set_status(Status(StatusCode.ERROR))
                raise
            finally:
                route_object = scope.get("route")
                route = str(getattr(route_object, "path", "unmatched"))
                duration = time.monotonic() - started
                span.update_name(f"{method} {route}")
                span.set_attribute("http.request.method", method)
                span.set_attribute("http.route", route)
                span.set_attribute("http.response.status_code", status_code)
                HTTP_REQUESTS.labels(method, route, str(status_code)).inc()
                HTTP_DURATION.labels(method, route).observe(duration)


def configure_observability(app: FastAPI, settings: Settings) -> None:
    """Enable metrics and tracing only when explicitly configured."""

    global _enabled, _provider
    if not settings.observability_enabled:
        return
    _enabled = True
    if _provider is None:
        _provider = TracerProvider(
            resource=Resource.create({"service.name": settings.otel_service_name})
        )
        if settings.otel_exporter_otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            _provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(_provider)
    tracer = _provider.get_tracer("jianli.api")
    app.add_middleware(ObservabilityMiddleware, tracer=tracer)

    @app.get("/internal/metrics", include_in_schema=False)
    async def internal_metrics() -> Response:
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def observe_aiqa_answer(
    outcome: AnswerOutcome,
    duration_ms: int,
    *,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    """Record one terminal AIQA outcome without user or document attributes."""

    if not _enabled:
        return
    AIQA_ANSWERS.labels(outcome).inc()
    AIQA_DURATION.labels(outcome).observe(max(duration_ms, 0) / 1000)
    if prompt_tokens > 0:
        AIQA_TOKENS.labels("prompt").inc(prompt_tokens)
    if completion_tokens > 0:
        AIQA_TOKENS.labels("completion").inc(completion_tokens)
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("jianli.aiqa.outcome", outcome)
        span.set_attribute("jianli.aiqa.model", model[:80])
        span.set_attribute("jianli.aiqa.prompt_tokens", max(prompt_tokens, 0))
        span.set_attribute("jianli.aiqa.completion_tokens", max(completion_tokens, 0))


def observe_agent_tool(tool_name: str, status: ToolStatus, duration_ms: int) -> None:
    """Record a bounded tool event; unknown names collapse to one safe label."""

    if not _enabled:
        return
    tool = tool_name if tool_name in _TOOLS else "rejected_unknown"
    AIQA_TOOL_CALLS.labels(tool, status).inc()
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(
            "agent.tool",
            {
                "jianli.agent.tool": tool,
                "jianli.agent.status": status,
                "jianli.agent.duration_ms": max(duration_ms, 0),
            },
        )


def observe_rerank(
    status: RerankStatus, duration_ms: int, candidates: int, *, model: str
) -> None:
    """Record bounded rerank metadata without query or candidate content."""

    if not _enabled:
        return
    AIQA_RERANK.labels(status).inc()
    AIQA_RERANK_DURATION.labels(status).observe(max(duration_ms, 0) / 1000)
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(
            "aiqa.rerank",
            {
                "jianli.rerank.status": status,
                "jianli.rerank.candidates": max(candidates, 0),
                "jianli.rerank.duration_ms": max(duration_ms, 0),
                "jianli.rerank.model": model[:80],
            },
        )


def observe_semantic_cache(status: SemanticCacheStatus, duration_ms: int) -> None:
    """Record only bounded cache status and duration."""

    if not _enabled:
        return
    AIQA_SEMANTIC_CACHE.labels(status).inc()
    AIQA_SEMANTIC_CACHE_DURATION.labels(status).observe(max(duration_ms, 0) / 1000)
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(
            "aiqa.semantic_cache",
            {
                "jianli.semantic_cache.status": status,
                "jianli.semantic_cache.duration_ms": max(duration_ms, 0),
            },
        )


def observe_circuit_breaker(component: CircuitComponent, event: CircuitEvent) -> None:
    """Record a fixed provider component and state event, never provider content."""

    if not _enabled:
        return
    AIQA_CIRCUIT_BREAKER.labels(component, event).inc()
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(
            "aiqa.circuit_breaker",
            {
                "jianli.circuit.component": component,
                "jianli.circuit.event": event,
            },
        )
