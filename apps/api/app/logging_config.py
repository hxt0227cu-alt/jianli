"""Small JSON logging foundation with an intentionally fixed, non-sensitive schema."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Serialize standard log metadata plus caller-provided event message and optional fields.

    Optional fields (trace_id / conversation_id / latency_ms / grounded / offtopic / model /
    prompt_tokens / completion_tokens) are attached via ``logger.info(msg, extra={...})`` and
    only emitted when present, so the schema stays fixed for plain events (TASK-M6-HARDENING-001).
    """

    _OPTIONAL_FIELDS = (
        "trace_id",
        "conversation_id",
        "request_id",
        "latency_ms",
        "grounded",
        "offtopic",
        "model",
        "prompt_tokens",
        "completion_tokens",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key in self._OPTIONAL_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def configure_logging(level: str) -> None:
    """Configure the application logger without changing unrelated library loggers."""

    logger = logging.getLogger("jianli")
    logger.disabled = False
    for name, registered_logger in logging.root.manager.loggerDict.items():
        if name.startswith("jianli.") and isinstance(registered_logger, logging.Logger):
            registered_logger.disabled = False
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
