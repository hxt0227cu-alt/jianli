"""One-shot Worker process entry point."""

from __future__ import annotations

import logging

from .config import Settings
from .logging_config import configure_logging

LOGGER = logging.getLogger("jianli.worker")


def run_worker(settings: Settings | None = None) -> int:
    """Record one startup smoke event and exit without I/O or polling."""

    config = settings or Settings.from_env()
    configure_logging(config.log_level)
    LOGGER.info("worker_smoke_completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_worker())
