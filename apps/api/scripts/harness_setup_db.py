"""Provision the harness test database (idempotent) and run Alembic to head.

Invoked by ``scripts/verify.sh`` (and the git hooks). It:
1. Connects to the *maintenance* database (``jianli_dev`` — same role/credentials as the
   test database) with autocommit and creates the target test database if it does not
   already exist (``CREATE DATABASE`` is not idempotent in PostgreSQL, so we pre-check
   ``pg_database``).
2. Runs ``alembic upgrade head`` against the target so the schema is current.
3. Pings Redis to fail fast with an actionable message if the container is down.

Target database URL comes from ``HARNESS_TARGET_DATABASE_URL`` (set by verify.sh). The
maintenance database is derived by swapping the database name for ``jianli_dev``.

Reuses the existing docker-compose services — it never starts or recreates containers.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlsplit

import psycopg
import redis
from alembic import command
from alembic.config import Config

ALLOWED_DATABASES = {
    "jianli_test",
    "jianli_auth_001_db",
    "jianli_tc_ops_002_db",
    "jianli_tc_aiqa_001_db",
    "jianli_tc_feishu_001_db",
}


def _allowed_port(local_port: int, ci_port: int, actual: int | None) -> bool:
    return actual == local_port or (
        os.environ.get("CI", "").lower() == "true" and actual == ci_port
    )


def _safe_target(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.scheme == "postgresql+psycopg"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and _allowed_port(55432, 5432, parsed.port)
        and parsed.path.removeprefix("/") in ALLOWED_DATABASES
        and not parsed.query
        and not parsed.fragment
    )


def _safe_redis(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.scheme == "redis"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and _allowed_port(63790, 6379, parsed.port)
        and parsed.path == "/15"
        and not parsed.query
        and not parsed.fragment
    )


def _normalize(url: str) -> str:
    """Strip the SQLAlchemy ``+psycopg`` dialect marker so ``psycopg.connect`` accepts it."""

    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _db_name(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _maintenance_url(url: str) -> str:
    """Same host/role but pointed at the always-present ``jianli_dev`` database."""

    base = url.rsplit("/", 1)[0]
    return f"{base}/jianli_dev"


def main() -> int:
    target = os.environ.get("HARNESS_TARGET_DATABASE_URL")
    if not target:
        print("[harness_setup_db] HARNESS_TARGET_DATABASE_URL 未设置", file=sys.stderr)
        return 2
    if not _safe_target(target):
        print("[harness_setup_db] 拒绝非 loopback/allowlist 测试库", file=sys.stderr)
        return 2

    redis_url = os.environ.get("JIANLI_REDIS_URL")
    if not redis_url or not _safe_redis(redis_url):
        print("[harness_setup_db] 拒绝非 loopback Redis db15", file=sys.stderr)
        return 2

    maintenance = _normalize(_maintenance_url(target))

    try:
        with psycopg.connect(maintenance, autocommit=True) as conn:
            exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", [target_db := _db_name(target)]
            ).fetchone()
            if not exists:
                print(f"[harness_setup_db] 创建测试库 {target_db} ...")
                conn.execute(f'CREATE DATABASE "{target_db}"')
            else:
                print(f"[harness_setup_db] 测试库 {target_db} 已存在，跳过创建")
    except psycopg.Error as exc:
        print(
            "[harness_setup_db] 无法连接维护库（PG 是否启动？"
            f"docker compose -f docker-compose.dev.yml up -d）: {exc}",
            file=sys.stderr,
        )
        return 1

    # Redis reachability (fail fast with a clear message).
    try:
        redis.from_url(redis_url).ping()
    except redis.exceptions.RedisError as exc:
        print(f"[harness_setup_db] Redis 不可达（是否启动？）: {exc}", file=sys.stderr)
        return 1

    # Migrate the target to head. env.py reads JIANLI_DATABASE_URL from the environment,
    # so point it at the target for the duration of the upgrade.
    api_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["JIANLI_DATABASE_URL"] = target
    cfg = Config(os.path.join(api_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(api_root, "migrations"))
    print(f"[harness_setup_db] alembic upgrade head -> {target_db}")
    command.upgrade(cfg, "head")
    print("[harness_setup_db] 测试库就绪")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
