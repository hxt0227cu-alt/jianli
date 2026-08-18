#!/usr/bin/env python3
"""Re-seed the LIVE knowledge base from the canonical CORPUS (test_rag_eval.py).

修复版（TASK-AIQA-KB-EXPAND-014）：上轮（2026-08-18）因未加载 ``.env.local`` 误连空库、
embedding key 缺失，导致 10 篇文档全部 failed。本次脚本内先解析 ``apps/api/.env.local``
（``export KEY='value'`` 行）写入 os.environ，再 ``Settings.from_env()`` 连 live 库
（``jianli_dev``），进程内 ASGI 客户端上传 CORPUS——与 pytest 上传同一机制，绕开
secure-cookie / HTTP 限制。

用法（WSL，uvicorn 已在跑）：
    cd /mnt/c/Users/hxt02/Desktop/jianli/apps/api
    python3 scripts/seed_kb.py            # 清理现存 docs（含 failed）+ 上传 CORPUS（11 篇）
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

# Make ``app`` and ``tests`` importable (scripts/ lives under apps/api).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.passwords import PasswordHasher  # noqa: E402
from app.auth.runtime import AuthRuntime, build_auth_runtime  # noqa: E402
from app.config import Settings  # noqa: E402
from app.factory import create_app  # noqa: E402
from tests.aiqa.test_rag_eval import CORPUS  # noqa: E402

SEED_EMAIL = os.environ.get("JIANLI_SEED_ADMIN_EMAIL", "seed-kb@jianli.local")
_ENV_LINE = re.compile(r"^export\s+([A-Z0-9_]+)\s*=\s*(.+?)\s*$")


def _load_env_local(env_path: Path) -> None:
    """Parse `export KEY='value'` lines into os.environ (never overwrite inherited values)."""
    if not env_path.exists():
        print(f"[env] {env_path} not found — rely on inherited env")
        return
    loaded = 0
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.startswith("export "):
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


def _seed_owner(engine: Engine) -> UUID:
    user_id = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:password_hash,'owner_admin',true) "
                "ON CONFLICT (email) DO UPDATE SET role='owner_admin', verified=true"
            ),
            {
                "id": user_id,
                "email": SEED_EMAIL,
                "password_hash": PasswordHasher().hash("seed-kb-not-used"),
            },
        )
        row = conn.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": SEED_EMAIL}
        ).fetchone()
    assert row is not None
    return UUID(str(row[0]))


async def _main(clear: bool) -> int:
    _load_env_local(Path(__file__).resolve().parent.parent / ".env.local")
    settings = Settings.from_env()
    if not settings.database_url:
        print("[ERR] JIANLI_DATABASE_URL not set（请确认 .env.local 可读）", file=sys.stderr)
        return 2
    engine = create_engine(settings.database_url)
    auth_runtime = build_auth_runtime(settings)
    app = create_app(settings, auth_runtime)

    owner = _seed_owner(engine)
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
        resp = await client.post("/admin/knowledge-documents", files=payload)
        print(f"== upload CORPUS ({len(CORPUS)} docs) -> HTTP {resp.status_code}")
        if resp.status_code != 202:
            print(f"[ERR] upload failed: {resp.text[:500]}", file=sys.stderr)
            return 1
        listed = (await client.get("/admin/knowledge-documents")).json()["items"]
        indexed = sum(1 for i in listed if i["status"] == "indexed")
        print(f"== KB now {len(listed)} doc(s): indexed={indexed}, failed={len(listed)-indexed}")
        if indexed != len(listed):
            print(
                "[WARN] 存在 failed 文档——请确认 .env.local 的 JIANLI_LLM_EMBEDDING_API_KEY "
                "有效（embedding 失败会 mark_failed）",
                file=sys.stderr,
            )
            return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-seed live KB from CORPUS.")
    ap.add_argument("--no-clear", action="store_true", help="skip deleting existing docs")
    args = ap.parse_args()
    return asyncio.run(_main(not args.no_clear))


if __name__ == "__main__":
    raise SystemExit(main())
