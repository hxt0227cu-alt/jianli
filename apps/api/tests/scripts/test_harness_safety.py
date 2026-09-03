from __future__ import annotations

import logging

import pytest

from scripts import harness_setup_db
from tests.conftest import _is_safe_harness_database, isolate_jianli_logging


def test_local_and_ci_database_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    local = "postgresql+psycopg://u:p@127.0.0.1:55432/jianli_test"
    ci = "postgresql+psycopg://u:p@localhost:5432/jianli_tc_aiqa_001_db"
    monkeypatch.delenv("CI", raising=False)
    assert _is_safe_harness_database(local)
    assert harness_setup_db._safe_target(local)
    assert not harness_setup_db._safe_target(ci)

    monkeypatch.setenv("CI", "true")
    assert harness_setup_db._safe_target(ci)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://u:p@db.example.com:55432/jianli_test",
        "postgresql+psycopg://u:p@127.0.0.1:55432/jianli_prod",
        "postgresql+psycopg://u:p@127.0.0.1:55432/jianli_test_copy",
        "postgresql+psycopg://u:p@127.0.0.1:55432/jianli_test?sslmode=require",
        "postgresql://u:p@127.0.0.1:55432/jianli_test",
    ],
)
def test_database_guard_rejects_unsafe_targets(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.delenv("CI", raising=False)
    assert not harness_setup_db._safe_target(url)


def test_redis_guard_requires_loopback_db15(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    assert harness_setup_db._safe_redis("redis://127.0.0.1:63790/15")
    assert not harness_setup_db._safe_redis("redis://127.0.0.1:63790/0")
    assert not harness_setup_db._safe_redis("rediss://127.0.0.1:63790/15")
    assert not harness_setup_db._safe_redis("redis://cache.example.com:63790/15")


def test_main_rejects_before_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HARNESS_TARGET_DATABASE_URL",
        "postgresql+psycopg://u:p@db.example.com:55432/jianli_test",
    )
    monkeypatch.setenv("JIANLI_REDIS_URL", "redis://127.0.0.1:63790/15")
    monkeypatch.setattr(
        harness_setup_db.psycopg,
        "connect",
        lambda *args, **kwargs: pytest.fail("unsafe target reached psycopg.connect"),
    )
    assert harness_setup_db.main() == 2


def test_logging_fixture_restores_existing_and_cleans_new_logger() -> None:
    existing = logging.getLogger("jianli.fixture-existing")
    handler = logging.NullHandler()
    existing.handlers[:] = [handler]
    existing.setLevel(logging.ERROR)
    existing.disabled = True
    existing.propagate = False

    fixture = isolate_jianli_logging.__wrapped__()
    next(fixture)
    assert existing.handlers == []
    assert existing.level == logging.NOTSET
    assert existing.disabled is False
    assert existing.propagate is True

    created = logging.getLogger("jianli.fixture-created")
    created.handlers[:] = [logging.NullHandler()]
    created.setLevel(logging.CRITICAL)
    created.disabled = True
    created.propagate = False
    with pytest.raises(StopIteration):
        next(fixture)

    assert existing.handlers == [handler]
    assert existing.level == logging.ERROR
    assert existing.disabled is True
    assert existing.propagate is False
    assert created.handlers == []
    assert created.level == logging.NOTSET
    assert created.disabled is False
    assert created.propagate is True
