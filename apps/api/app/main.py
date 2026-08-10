"""API process entry point."""

from __future__ import annotations

import uvicorn  # type: ignore[import-untyped]

from .config import Settings
from .factory import create_app
from .logging_config import configure_logging


settings = Settings.from_env()
configure_logging(settings.log_level)
app = create_app(settings)


def run() -> None:
    """Run the ASGI process using environment-backed host and port settings."""

    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_config=None)


if __name__ == "__main__":
    run()
