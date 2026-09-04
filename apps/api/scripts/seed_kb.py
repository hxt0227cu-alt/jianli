#!/usr/bin/env python3
# ruff: noqa: RUF002  # Chinese operator guide intentionally uses full-width punctuation.
"""Seed the knowledge base from the production canonical corpus.

本地运行时可加载 ``apps/api/.env.local``；生产容器只使用继承的运行时环境。脚本通过
进程内 ASGI 客户端走与管理端相同的上传路径，并要求真实 ``owner_admin`` 已先初始化。

用法（WSL，uvicorn 已在跑）：
    cd /mnt/c/Users/<user>/Desktop/jianli/apps/api
    python3 scripts/seed_kb.py            # 清理现存 docs（含 failed）+ 上传 CORPUS（20 篇）
    python3 scripts/seed_kb.py --no-clear # 只上传（新 checksum 新建 doc，旧 doc 保留）

说明：KB 与静态页（content.py）是两个独立检索源——本脚本只更新 KB（pgvector，线上简历域
检索主源）；content.py 静态兜底改动需重启 uvicorn 生效。
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import secrets
import sys
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy import Engine, create_engine, text

# Make ``app`` importable (scripts/ lives under apps/api).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.aiqa.canonical_corpus import CANONICAL_CORPUS as CORPUS
from app.auth.runtime import build_auth_runtime
from app.config import Settings
from app.factory import create_app

# Bare `KEY=value` (the .env.local format) with an optional `export ` prefix
# (TASK-AIQA-KB-DOMAIN-015: the previous regex required `export ` and loaded 0 vars
# from the real .env.local — it only worked when the shell already had the env).
_ENV_LINE = re.compile(r"^(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.+?)\s*$")


def _load_env_local(env_path: Path) -> None:
    """Parse `[export] KEY='value'` lines into os.environ (never overwrite inherited values)."""
    if not env_path.exists():
        print(f"[env] {env_path} not found — rely on inherited env")
        return
    loaded = 0
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _ENV_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        if key not in os.environ:
            os.environ[key] = value
            loaded += 1
    print(f"[env] loaded {loaded} var(s) from {env_path.name}")


def _require_owner(engine: Engine) -> UUID:
    """Reuse the real owner; never create a production account with a known password."""

    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id FROM users "
                "WHERE role='owner_admin' AND verified=true AND deleted_at IS NULL "
                "LIMIT 1"
            )
        ).fetchone()
    if row is None:
        raise RuntimeError("create the real owner_admin before seeding the canonical corpus")
    return UUID(str(row[0]))


def _active_documents(engine: Engine) -> list[dict[str, object]]:
    query = text(
        "SELECT id,name,status,failure_reason FROM knowledge_documents "
        "WHERE retrieval_disabled_at IS NULL ORDER BY name,id"
    )
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(query).mappings()]


def _seed_state_errors(active: list[dict[str, object]], expected_names: set[str]) -> list[str]:
    errors: list[str] = []
    actual_names = {str(item["name"]) for item in active}
    if len(active) != len(expected_names):
        errors.append(f"active count {len(active)} != expected {len(expected_names)}")
    missing = sorted(expected_names - actual_names)
    if missing:
        errors.append(f"missing: {', '.join(missing)}")
    extra = sorted(actual_names - expected_names)
    if extra:
        errors.append(f"unexpected: {', '.join(extra)}")
    for item in active:
        status = str(item["status"])
        if status != "indexed":
            reason = str(item.get("failure_reason") or "no failure reason")
            reason = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-<redacted>", reason)
            errors.append(f"{item['name']}: status={status}, reason={reason[:160]}")
    return errors


async def _main(clear: bool) -> int:
    _load_env_local(Path(__file__).resolve().parent.parent / ".env.local")
    settings = Settings.from_env()
    if not settings.database_url:
        print("[ERR] JIANLI_DATABASE_URL not set（请确认 .env.local 可读）", file=sys.stderr)
        return 2
    engine = create_engine(settings.database_url)
    auth_runtime = build_auth_runtime(settings)
    app = create_app(settings, auth_runtime)

    try:
        owner = _require_owner(engine)
    except RuntimeError as error:
        print(f"[ERR] {error}", file=sys.stderr)
        return 2
    session_token = secrets.token_urlsafe(32)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO auth_sessions "
                "(id,user_id,session_token_hash,expires_at,revoked_at) "
                "VALUES (:id,:user_id,:token_hash,:expires_at,NULL)"
            ),
            {
                "id": uuid4(),
                "user_id": str(owner),
                "token_hash": auth_runtime.tokens.digest(session_token),
                "expires_at": __import__("datetime").datetime.now(
                    __import__("datetime").UTC
                )
                + __import__("datetime").timedelta(hours=1),
            },
        )
    csrf = auth_runtime.tokens.csrf(session_token)

    origin = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:5173"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.cookies.set("__Host-session", session_token)
        client.cookies.set("__Host-csrf", csrf)
        client.headers.update({"Origin": origin, "X-CSRF-Token": csrf})

        if clear:
            listed = (await client.get("/admin/knowledge-documents")).json()["items"]
            for item in listed:
                code = (await client.delete(f"/admin/knowledge-documents/{item['id']}")).status_code
                print(f"  delete {item['name']} -> {code}")
            print(f"== cleared {len(listed)} doc(s)")

        payload = [
            ("files", (name, content.encode("utf-8"), "text/markdown"))
            for name, content in CORPUS.items()
        ]
        # The upload endpoint caps at 20 files per request (router `_MAX_UPLOAD_FILES`,
        # product contract unchanged); the canonical corpus may exceed that, so upload
        # in batches of 20 and require every batch to be accepted (202). Mirrors the
        # batching already used by tests/aiqa/test_rag_eval.py `_upload`.
        responses = []
        for index in range(0, len(payload), 20):
            batch = payload[index : index + 20]
            resp = await client.post("/admin/knowledge-documents", files=batch)
            print(
                f"== upload batch {index // 20 + 1} ({len(batch)} docs) "
                f"-> HTTP {resp.status_code}"
            )
            responses.append(resp)
        if any(resp.status_code != 202 for resp in responses):
            print(
                f"[ERR] upload failed with HTTP {[r.status_code for r in responses]}",
                file=sys.stderr,
            )
            return 1
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        active = _active_documents(engine)
        indexed = sum(1 for item in active if str(item["status"]) == "indexed")
        print(
            f"== KB active {len(active)} doc(s): indexed={indexed}, "
            f"non-indexed={len(active)-indexed}; historical={len(listed)-len(active)}"
        )
        errors = _seed_state_errors(active, set(CORPUS))
        if errors:
            print("[ERR] canonical corpus verification failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        print(f"== verified canonical corpus: {indexed}/{len(CORPUS)} active + indexed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-seed live KB from CORPUS.")
    ap.add_argument("--no-clear", action="store_true", help="skip deleting existing docs")
    args = ap.parse_args()
    return asyncio.run(_main(not args.no_clear))


if __name__ == "__main__":
    raise SystemExit(main())
