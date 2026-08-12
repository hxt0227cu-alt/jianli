"""Worker process entry point.

Runs the notification Outbox consumer (M3) when SMTP is configured; otherwise records
a startup smoke event and exits (no I/O, no polling) — the previous default behavior.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, create_engine

from .appointments.runtime import build_booking_runtime
from .auth.repository import AuthRepository
from .auth.runtime import AuthRuntime, build_auth_runtime
from .config import Settings
from .logging_config import configure_logging
from .notifications.worker import run_notification_worker

LOGGER = logging.getLogger("jianli.worker")


def run_worker(settings: Settings | None = None) -> int:
    config = settings or Settings.from_env()
    configure_logging(config.log_level)

    if not config.notification_configured:
        LOGGER.info("worker_smoke_completed", extra={"notification_configured": False})
        return 0

    engine: Engine = create_engine(config.database_url)
    auth_runtime: AuthRuntime = build_auth_runtime(config)
    booking = build_booking_runtime(config, auth_runtime)
    auth_repo = AuthRepository(engine)
    return run_notification_worker(config, engine, booking, auth_repo)


if __name__ == "__main__":
    raise SystemExit(run_worker())
