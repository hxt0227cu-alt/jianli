"""Small JSON logging foundation with an intentionally fixed, non-sensitive schema."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Serialize only standard log metadata and the caller-provided event message."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
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
