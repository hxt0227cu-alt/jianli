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

import json
import re
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


class GatewayError(Exception):
    """Raised when the model provider is unreachable or returns an error."""


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

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model

    async def answer(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[tuple[str, str | dict[str, object]]]:
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
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client, client.stream(
                "POST", url, headers=headers_obj, json=payload
            ) as resp:
                if resp.status_code >= 400:
                    raise GatewayError(f"provider returned {resp.status_code}")
                # Accumulate incremental tool-call deltas (name + arguments chunks).
                pending_tool_name: list[str] = []
                pending_tool_args: list[str] = []
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    delta_text, tool_name, tool_args = self._extract_delta_and_tools(data)
                    if delta_text:
                        yield ("delta", delta_text)
                    if tool_name:
                        pending_tool_name.append(tool_name)
                    if tool_args:
                        pending_tool_args.append(tool_args)
                if pending_tool_name:
                    yield (
                        "tool_call",
                        {
                            "name": "".join(pending_tool_name),
                            "arguments": "".join(pending_tool_args),
                        },
                    )
        except httpx.HTTPError as error:  # network/timeout
            raise GatewayError(str(error)) from error

    @staticmethod
    def _extract_delta_and_tools(
        data: str,
    ) -> tuple[str, str, str]:
        """Parse one streaming chunk: (content delta, tool-call name delta, tool args delta).

        Standard JSON parse of the chunk (OpenAI-compatible format); missing fields
        return "". Tool-call deltas arrive as incremental fragments of ``function.arguments``
        which the caller concatenates.
        """
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            return "", "", ""
        choices = chunk.get("choices") or []
        if not choices:
            return "", "", ""
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or ""
        tool_calls = delta.get("tool_calls") or []
        name = ""
        arguments = ""
        for call in tool_calls:
            fn = call.get("function") or {}
            name = (name or "") + (fn.get("name") or "")
            arguments = (arguments or "") + (fn.get("arguments") or "")
        return content, name, arguments


def build_gateway(
    *,
    base_url: str | None,
    api_key: str | None,
    model: str | None,
    timeout: float,
) -> LLMGateway:
    """Pick the gateway implementation from configuration (OpenAI if configured)."""

    if base_url and api_key and model:
        return OpenAIGateway(base_url, api_key, model, timeout)
    return StubGateway()
