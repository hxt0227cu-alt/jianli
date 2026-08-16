"""LLM gateway for the Answer domain (M6 round 1; Agent tooling TASK-AGENT-TOOLS-001).

The gateway is the single seam between the Answer service and a model provider. Round 1
ships two implementations behind one protocol:

* ``StubGateway`` — deterministic, in-process, no network. Used whenever the LLM env vars
  are unset, so the site runs and is fully testable with zero external services. With
  Agent tooling it simulates a ``search_knowledge`` tool call (query = original question)
  so the DB-free pipeline stays deterministic.
* ``OpenAIGateway`` — streams from any OpenAI-compatible ``/chat/completions`` endpoint.
  ``httpx`` is intentionally *lazy-imported*: it is a dev extra, not a runtime dependency,
  so production installs without it still boot (stub gateway). Enabling the OpenAI gateway
  requires httpx at runtime.

``answer`` yields one of two kinds of events (TASK-AGENT-TOOLS-001):
  ("delta", str)                      — answer text chunk
  ("tool_call", dict)                 — {"name", "arguments"} model-initiated tool request
Tool execution is owned by the service; the gateway never executes tools itself.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


class GatewayError(Exception):
    """Raised when the model provider is unreachable or returns an error."""


class _RetryableError(GatewayError):
    """Transient provider failure (5xx / network) that the gateway may retry.

    Subclasses ``GatewayError`` so the service's ``except GatewayError`` still maps it to
    the SSE error frame, while the retry loop can recognise it as retryable vs the
    non-retryable 4xx ``GatewayError`` raised inline.
    """


@runtime_checkable
class LLMGateway(Protocol):
    """Streaming chat completion gateway. Yields ("delta"|"tool_call", payload) tuples.

    Implementations are async generator functions (``async def ... yield``), which is why
    the protocol method itself is declared without ``async`` and returns ``AsyncIterator``.
    """

    @property
    def model_name(self) -> str: ...

    def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]: ...


def _context_from_user(user: str) -> str:
    marker = "【已知资料】"
    if marker not in user:
        return ""
    first_line = user.split(marker, 1)[1].strip().splitlines()[0]
    # Strip the "[doc #fragment]" label the service prepends to each chunk.
    return re.sub(r"^\[[^\]]+\]\s*", "", first_line)


class StubGateway:
    """Deterministic fallback gateway: extractive, grounded, no model call.

    Agent tooling: if tools were offered, simulate the model deciding to call
    ``search_knowledge`` with the original question as the query. The service executes it
    and feeds results back in a second turn, keeping the DB-free pipeline deterministic.
    """

    @property
    def model_name(self) -> str:
        return "stub"

    async def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        if tools:
            user = next((m["content"] for m in messages if m["role"] == "user"), "")
            question = (
                user.split("用户问题：", 1)[1].splitlines()[0]
                if "用户问题：" in user
                else user
            )
            yield (
                "tool_call",
                {
                    "name": "search_knowledge",
                    "arguments": json.dumps({"query": question}),
                },
            )
            return
        user = next((m["content"] for m in messages if m["role"] == "user"), "")
        snippet = _context_from_user(user)
        if snippet:
            yield ("delta", f"（本地演示回答，尚未接入大模型）根据资料：{snippet}")
        else:
            yield ("delta", "（本地演示回答）我已收到你的问题，配置模型后将给出更完整的回答。")


class OpenAIGateway:
    """Stream SSE deltas from an OpenAI-compatible chat completions endpoint via httpx."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max(1, int(max_retries))

    @property
    def model_name(self) -> str:
        return self._model

    def _backoff(self, attempt: int) -> float:
        """Deterministic exponential backoff (no jitter): 0.3s, 0.6s, capped at 3s.

        Deterministic so retries are reproducible in tests and the added latency is
        predictable in production (no random sleeps).
        """
        return min(0.3 * (2 ** attempt), 3.0)

    async def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        """Stream (delta|tool_call|usage) events, transparently retrying transient failures.

        A transient failure (5xx or network error) before any event has been yielded is
        retried with exponential backoff up to ``_max_retries`` attempts. Mid-stream
        failures (after events were already sent to the client) cannot be cleanly retried,
        so they surface immediately as a ``GatewayError`` (→ SSE error frame). 4xx provider
        responses are permanent and never retried.
        """
        last_error: GatewayError | None = None
        for attempt in range(self._max_retries):
            emitted = False
            try:
                async for kind, payload in self._stream_once(messages, tools):
                    emitted = True
                    yield kind, payload
            except _RetryableError as error:
                last_error = error
                if emitted:
                    # Partial answer already streamed to the client; cannot safely retry.
                    raise GatewayError(str(error)) from error
                await asyncio.sleep(self._backoff(attempt))
                continue
            else:
                return
        if last_error is not None:
            raise GatewayError(str(last_error)) from last_error
        raise GatewayError("LLM gateway exhausted retries with no response")

    async def _stream_once(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
        """Single upstream attempt; raises ``_RetryableError`` on transient failures."""
        try:
            import httpx  # lazy: httpx is a dev extra, not a runtime dependency
        except ImportError as error:
            raise GatewayError(
                "httpx is required for the OpenAI gateway; install the dev extras"
            ) from error
        url = f"{self._base_url}/chat/completions"
        # 显式 utf-8 编码：避免在 zh_CN 等非英文 locale 下 httpx 默认 ascii codec
        # 把消息里的中文误判到 header 归一化路径上时报 UnicodeEncodeError。
        # Content-Type 加 charset=utf-8 让 provider 知道 body 也是 utf-8。
        headers_obj = httpx.Headers(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "text/event-stream",
            },
            encoding="utf-8",
        )
        payload: dict[str, object] = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            # 关闭 DeepSeek V4-Flash 默认开启的 thinking 模式（避免推理过程以
            # reasoning_content/英文重复 token 形式泄漏到 delta 流里）。
            "thinking": {"type": "disabled"},
            # Ask the provider to attach a final usage chunk so token cost is measurable.
            "stream_options": {"include_usage": True},
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client, client.stream(
                "POST", url, headers=headers_obj, json=payload
            ) as resp:
                if resp.status_code >= 500:
                    raise _RetryableError(f"provider returned {resp.status_code}")
                if resp.status_code >= 400:
                    raise GatewayError(f"provider returned {resp.status_code}")
                # Accumulate incremental tool-call deltas (name + arguments chunks).
                pending_tool_name: list[str] = []
                pending_tool_args: list[str] = []
                usage_payload: dict[str, object] | None = None
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    delta_text, tool_name, tool_args, usage = self._extract_delta_and_tools(data)
                    if delta_text:
                        yield ("delta", delta_text)
                    if tool_name:
                        pending_tool_name.append(tool_name)
                    if tool_args:
                        pending_tool_args.append(tool_args)
                    if usage is not None:
                        usage_payload = usage
                if pending_tool_name:
                    yield (
                        "tool_call",
                        {
                            "name": "".join(pending_tool_name),
                            "arguments": "".join(pending_tool_args),
                        },
                    )
                if usage_payload is not None:
                    yield ("usage", usage_payload)
        except httpx.HTTPError as error:  # network/timeout — transient, retryable
            raise _RetryableError(str(error)) from error

    @staticmethod
    def _extract_delta_and_tools(
        data: str,
    ) -> tuple[str, str, str, dict[str, object] | None]:
        """Parse one streaming chunk: (content, tool name, tool args, usage|None).

        Standard JSON parse of the chunk (OpenAI-compatible format); missing fields
        return "". Tool-call deltas arrive as incremental fragments of ``function.arguments``
        which the caller concatenates. The final chunk may carry ``usage`` (no ``choices``)
        when ``stream_options.include_usage`` is set; returned separately so the caller can
        emit a ``("usage", dict)`` event.
        """
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            return "", "", "", None
        choices = chunk.get("choices") or []
        if not choices:
            usage = chunk.get("usage")
            return "", "", "", (usage if isinstance(usage, dict) else None)
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or ""
        tool_calls = delta.get("tool_calls") or []
        name = ""
        arguments = ""
        for call in tool_calls:
            fn = call.get("function") or {}
            name = (name or "") + (fn.get("name") or "")
            arguments = (arguments or "") + (fn.get("arguments") or "")
        usage = chunk.get("usage")
        return content, name, arguments, (usage if isinstance(usage, dict) else None)


def build_gateway(
    *,
    base_url: str | None,
    api_key: str | None,
    model: str | None,
    timeout: float,
    max_retries: int = 3,
) -> LLMGateway:
    """Pick the gateway implementation from configuration (OpenAI if configured)."""

    if base_url and api_key and model:
        return OpenAIGateway(base_url, api_key, model, timeout, max_retries)
    return StubGateway()
