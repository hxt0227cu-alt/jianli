"""LLM gateway for the Answer domain (M6 round 1).

The gateway is the single seam between the Answer service and a model provider. Round 1
ships two implementations behind one protocol:

* ``StubGateway`` — deterministic, in-process, no network. Used whenever the LLM env vars
  are unset, so the site runs and is fully testable with zero external services.
* ``OpenAIGateway`` — streams from any OpenAI-compatible ``/chat/completions`` endpoint.
  ``httpx`` is intentionally *lazy-imported*: it is a dev extra, not a runtime dependency,
  so production installs without it still boot (stub gateway). Enabling the OpenAI gateway
  requires httpx at runtime.

Handoff note for Codex: add providers (Anthropic, local vLLM, …) by implementing
``LLMGateway.answer`` and wiring them in ``runtime.build_aiqa_runtime``. The service only
ever sees the protocol, so nothing else changes.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


class GatewayError(Exception):
    """Raised when the model provider is unreachable or returns an error."""


@runtime_checkable
class LLMGateway(Protocol):
    """Streaming chat completion gateway. Yields answer deltas as plain strings.

    Implementations are async generator functions (``async def ... yield``), which is why
    the protocol method itself is declared without ``async`` and returns ``AsyncIterator``.
    """

    @property
    def model_name(self) -> str: ...

    def answer(self, messages: list[dict[str, str]]) -> AsyncIterator[str]: ...


def _context_from_user(user: str) -> str:
    marker = "【已知资料】"
    if marker not in user:
        return ""
    first_line = user.split(marker, 1)[1].strip().splitlines()[0]
    # Strip the "[doc #fragment]" label the service prepends to each chunk.
    return re.sub(r"^\[[^\]]+\]\s*", "", first_line)


class StubGateway:
    """Deterministic fallback gateway: extractive, grounded, no model call."""

    @property
    def model_name(self) -> str:
        return "stub"

    async def answer(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        user = next((m["content"] for m in messages if m["role"] == "user"), "")
        snippet = _context_from_user(user)
        if snippet:
            yield f"（本地演示回答，尚未接入大模型）根据资料：{snippet}"
        else:
            yield "（本地演示回答）我已收到你的问题，配置模型后将给出更完整的回答。"


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

    async def answer(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        try:
            import httpx  # lazy: httpx is a dev extra, not a runtime dependency
        except ImportError as error:
            raise GatewayError(
                "httpx is required for the OpenAI gateway; install the dev extras"
            ) from error
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            # 关闭 DeepSeek V4-Flash 默认开启的 thinking 模式（避免推理过程以
            # reasoning_content/英文重复 token 形式泄漏到 delta 流里）。
            "thinking": {"type": "disabled"},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client, client.stream(
                "POST", url, headers=headers, json=payload
            ) as resp:
                if resp.status_code >= 400:
                    raise GatewayError(f"provider returned {resp.status_code}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        return
                    yield self._extract_delta(data)
        except httpx.HTTPError as error:  # network/timeout
            raise GatewayError(str(error)) from error

    @staticmethod
    def _extract_delta(data: str) -> str:
        # Minimal, dependency-free JSON scan for the streaming delta content.
        # Avoids pulling in a JSON parser nuance; the field is always shallow.
        marker = '"content":'
        idx = data.find(marker)
        if idx == -1:
            return ""
        start = data.find('"', idx + len(marker))
        if start == -1:
            return ""
        end = data.find('"', start + 1)
        if end == -1:
            return ""
        return data[start + 1 : end].replace("\\n", "\n").replace('\\"', '"')


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
