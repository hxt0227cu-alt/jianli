#!/usr/bin/env python3
"""TASK-DEPLOY-001: 创建/重置生产 owner_admin 账号（幂等）。

用途：初始化或重置「管理员登录」账号（角色 owner_admin，verified=true）。
     部署指南第 4.5 节调用；本地开发亦可直接跑。

安全要求：
  - 邮箱与密码只从环境变量读取（JIANLI_OWNER_EMAIL / JIANLI_OWNER_PASSWORD），
    绝不从命令行参数、文件或日志获取/输出密码。
  - 密码经 BCrypt 哈希后落库，只存哈希。
  - 重复执行幂等：同邮箱再次执行会重置密码（已存在的 owner_admin 保持 verified）。

运行方式：
  服务器（推荐，复用 api 镜像，不经宿主机 Python）：
      JIANLI_OWNER_EMAIL=you@example.com JIANLI_OWNER_PASSWORD='<强密码>' \
        ./scripts/create-owner.sh
  本地开发（WSL，读 apps/api/.env.local 的 JIANLI_DATABASE_URL）：
      JIANLI_OWNER_EMAIL=... JIANLI_OWNER_PASSWORD=... python scripts/create_owner.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
for cand in (BASE / "apps" / "api", BASE):          # 本地: repo/apps/api；容器: /srv/jianli
    if (cand / "app").is_dir():
        sys.path.insert(0, str(cand))
        break
else:
    sys.exit("[ERR] 找不到 app 包（请在仓库根目录或 api 镜像内运行）")

from sqlalchemy import create_engine, text  # noqa: E402

from app.auth.passwords import PasswordHasher  # noqa: E402


def _load_env_local(path: Path) -> None:
    """本地开发兜底：从 .env.local 加载 JIANLI_DATABASE_URL（不覆盖已有环境变量）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    email = os.environ.get("JIANLI_OWNER_EMAIL", "").strip().lower()
    password = os.environ.get("JIANLI_OWNER_PASSWORD", "")
    if not email or not password:
        print("[ERR] 必须通过环境变量提供 JIANLI_OWNER_EMAIL 与 JIANLI_OWNER_PASSWORD", file=sys.stderr)
        return 2

    _load_env_local(BASE / "apps" / "api" / ".env.local")
    database_url = os.environ.get("JIANLI_DATABASE_URL", "").strip()
    if not database_url:
        print("[ERR] JIANLI_DATABASE_URL 未设置（服务器模式由 create-owner.sh 注入）", file=sys.stderr)
        return 2

    try:
        password_hash = PasswordHasher().hash(password)
    except Exception as exc:  # PasswordPolicyError 等
        print(f"[ERR] 密码不符合策略（10-72 UTF-8 字节）: {exc}", file=sys.stderr)
        return 2

    engine = create_engine(database_url)
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                "SELECT email FROM users "
                "WHERE role='owner_admin' AND deleted_at IS NULL AND email <> :e"
            ),
            {"e": email},
        ).mappings().first()
        if existing is not None:
            # 部分唯一索引 uq_active_owner_admin 只允许一个活跃 owner_admin
            print(
                f"[ERR] 已存在其他 owner_admin：{existing['email']}；"
                f"重置密码请改用该邮箱（或先停用/删除原账号）",
                file=sys.stderr,
            )
            return 2
        conn.execute(
            text(
                "INSERT INTO users (id,email,password_hash,role,verified) "
                "VALUES (:id,:email,:hash,'owner_admin',true) "
                "ON CONFLICT (email) DO UPDATE SET "
                "password_hash=EXCLUDED.password_hash, role='owner_admin', verified=true"
            ),
            {"id": uuid.uuid4(), "email": email, "hash": password_hash},
        )
        row = conn.execute(
            text("SELECT id,email,role,verified FROM users WHERE email=:e"), {"e": email}
        ).mappings().first()
    assert row is not None
    print(f"[OK] owner_admin 就绪：{row['email']}（role={row['role']}, verified={row['verified']}）")
    print("[OK] 现在可用该邮箱+密码登录站点「知识库管理 / admin」入口")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
