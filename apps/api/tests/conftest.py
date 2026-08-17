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

import os
from pathlib import Path

import pytest

from app.config import Settings

API_ROOT = Path(__file__).resolve().parent.parent  # apps/api


def _db_name(url: str | None) -> str:
    """Return the database name from a SQLAlchemy/psycopg URL (last path segment)."""

    return (url or "").rstrip("/").rsplit("/", 1)[-1]


@pytest.fixture(scope="session", autouse=True)
def ensure_test_schema() -> None:
    """Idempotently migrate the *test* database to head via Alembic.

    Autouse so that ``pytest`` is self-sufficient even without the verify pre-step, but
    strictly guarded: it only acts when ``JIANLI_DATABASE_URL`` points at a database whose
    name contains ``test``. Anything else (dev DB, the dedicated TC DB) is left untouched
    and the fixture is a no-op.
    """

    url = os.environ.get("JIANLI_DATABASE_URL")
    if not url or "test" not in _db_name(url):
        return

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
