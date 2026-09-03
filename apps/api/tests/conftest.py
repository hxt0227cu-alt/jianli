"""Centralized test fixtures for the Jianli API harness.

Design intent (harness engineering, TASK-HARNESS-001):
- Tests run against an **isolated** database (``jianli_test``) and Redis db (15) that the
  ``verify.sh`` script provisions from the same docker-compose services used for dev.
  This preserves *real* PostgreSQL(pgvector)+Redis validation (no mock downgrade) while
  keeping tests off the developer's ``jianli_dev`` database.
- Fixtures here are **opt-in** where it matters: existing test modules that define their
  own ``client`` / ``app`` / engine fixtures keep using them (pytest resolves the most
  local definition). New tests should prefer ``app_client``.
- ``ensure_test_schema`` (autouse, session-scoped) idempotently migrates the *test*
  database to head. It refuses to operate on anything that is not a test database, so a
  standalone ``pytest`` run without the harness env never migrates ``jianli_dev`` or the
  dedicated ``jianli_tc_ops_002_db`` TC database (the latter is owned by the migration
  acceptance tests and is skipped unless ``JIANLI_TEST_DATABASE_URL`` is set).

The harness (``scripts/verify.sh``) exports ``JIANLI_DATABASE_URL`` / ``JIANLI_REDIS_URL``
pointing at the test instances before invoking pytest.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from app.config import Settings

API_ROOT = Path(__file__).resolve().parent.parent  # apps/api


@pytest.fixture(autouse=True)
def isolate_jianli_logging() -> Iterator[None]:
    """Keep application logging configuration from leaking across tests.

    Importing an API entry point configures the process-wide ``jianli`` logger.  That
    state must not make later ``caplog`` assertions order-dependent, so every test gets
    a neutral, propagating application logger and the pre-test state is restored after
    the test finishes.
    """

    parent = logging.getLogger("jianli")
    registered = {
        name: logger
        for name, logger in list(logging.root.manager.loggerDict.items())
        if (name == "jianli" or name.startswith("jianli.")) and isinstance(logger, logging.Logger)
    }
    registered["jianli"] = parent
    states = {
        name: (
            logger.level,
            logger.disabled,
            logger.propagate,
            list(logger.handlers),
            list(logger.filters),
        )
        for name, logger in registered.items()
    }

    for logger in registered.values():
        logger.handlers.clear()
        logger.filters.clear()
        logger.setLevel(logging.NOTSET)
        logger.disabled = False
        logger.propagate = True

    try:
        yield
    finally:
        for name, logger in list(logging.root.manager.loggerDict.items()):
            if not isinstance(logger, logging.Logger) or not name.startswith("jianli."):
                continue
            if name not in states:
                logger.handlers.clear()
                logger.filters.clear()
                logger.setLevel(logging.NOTSET)
                logger.disabled = False
                logger.propagate = True
        for name, state in states.items():
            level, disabled, propagate, handlers, filters = state
            logger = logging.getLogger(name)
            logger.handlers[:] = handlers
            logger.filters[:] = filters
            logger.setLevel(level)
            logger.disabled = disabled
            logger.propagate = propagate


def _db_name(url: str | None) -> str:
    """Return the database name from a SQLAlchemy/psycopg URL (last path segment)."""

    return (url or "").rstrip("/").rsplit("/", 1)[-1]


def _is_safe_harness_database(url: str) -> bool:
    parsed = urlsplit(url)
    allowed_ports = {55432}
    if os.environ.get("CI", "").lower() == "true":
        allowed_ports.add(5432)
    return (
        parsed.scheme == "postgresql+psycopg"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and parsed.port in allowed_ports
        and parsed.path == "/jianli_test"
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_test_schema() -> None:
    """Idempotently migrate the *test* database to head via Alembic.

    Autouse so that ``pytest`` is self-sufficient even without the verify pre-step, but
    strictly guarded: it only acts when ``JIANLI_DATABASE_URL`` points at the exact
    loopback ``jianli_test`` database on the CI or development-Compose port. Anything
    else (dev DB or a dedicated TC DB) is left untouched. An unsafe URL that still names
    ``jianli_test`` fails closed instead of migrating a remote database.
    """

    url = os.environ.get("JIANLI_DATABASE_URL")
    if not url or _db_name(url) != "jianli_test":
        return
    if not _is_safe_harness_database(url):
        raise pytest.UsageError(
            "JIANLI_DATABASE_URL for jianli_test must use loopback PostgreSQL "
            "on port 55432 (or CI port 5432)"
        )

    from alembic import command
    from alembic.config import Config

    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    # env.py reads JIANLI_DATABASE_URL from the environment; it is already the test DB.
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Application settings as resolved from the environment.

    Under the harness this already points at ``jianli_test`` + Redis db 15 (verify.sh
    overrides ``JIANLI_DATABASE_URL`` / ``JIANLI_REDIS_URL``). Raises a clear skip if the
    required env is missing so the failure mode is obvious rather than a cryptic import
    error inside ``app.main``.
    """

    if not os.environ.get("JIANLI_DATABASE_URL"):
        pytest.skip(
            "JIANLI_DATABASE_URL not set; source apps/api/.env.local (or run scripts/verify.sh)"
        )
    return Settings.from_env()


@pytest.fixture
def app_client(test_settings: Settings) -> object:
    """Sync ``TestClient`` bound to a fully mounted app (auth + booking + admin + AI QA).

    The app is built from ``test_settings`` (test DB + test Redis), so requests exercise
    the real PostgreSQL/Redis stack. Use this for new integration tests.
    """

    from fastapi.testclient import TestClient

    from app.factory import create_app

    with TestClient(create_app(test_settings)) as client:
        yield client
