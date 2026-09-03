#!/usr/bin/env bash
# TASK-DEPLOY-001: 生产环境创建/重置 owner_admin 账号（幂等）。
# 前置：docker compose up -d 已完成（postgres 健康）。
#
# 用法（密码只走环境变量，不落盘、不进 shell 历史之外的任何文件）：
#   JIANLI_OWNER_EMAIL=you@example.com JIANLI_OWNER_PASSWORD='<强密码>' ./scripts/create-owner.sh
#
# 说明：通过 docker run 复用 api 镜像（含 SQLAlchemy/psycopg/BCrypt），
#       挂载 scripts/ 只读，不经宿主机 Python 环境。
set -euo pipefail

cd "$(dirname "$0")/.."                        # 项目根
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$PWD/.env}"

[ -f "$ENV_FILE" ] || { echo "[ERR] $ENV_FILE 不存在（先按部署指南第 2 节创建）" >&2; exit 1; }
get_env() { grep "^$1=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//'; }

PGUSER="${JIANLI_POSTGRES_USER:-$(get_env JIANLI_POSTGRES_USER)}"; PGUSER="${PGUSER:-jianli}"
PGDB="${JIANLI_POSTGRES_DB:-$(get_env JIANLI_POSTGRES_DB)}"; PGDB="${PGDB:-jianli_prod}"
PGPASS="${JIANLI_POSTGRES_PASSWORD:-$(get_env JIANLI_POSTGRES_PASSWORD)}"
[ -n "$PGPASS" ] || { echo "[ERR] .env 缺少 JIANLI_POSTGRES_PASSWORD" >&2; exit 1; }

OWNER_EMAIL="${JIANLI_OWNER_EMAIL:-}"
OWNER_PASSWORD="${JIANLI_OWNER_PASSWORD:-}"
if [ -z "$OWNER_EMAIL" ] || [ -z "$OWNER_PASSWORD" ]; then
  echo "[ERR] 请提供环境变量 JIANLI_OWNER_EMAIL 与 JIANLI_OWNER_PASSWORD（密码只走环境变量）" >&2
  exit 1
fi
# URL 拼装安全性：密码含 @ : / % 等会破坏连接串，直接拒绝
if printf '%s' "$PGPASS" | grep -qE '[@:/%]'; then
  echo "[ERR] JIANLI_POSTGRES_PASSWORD 含 @ : / % 字符，会破坏连接串，请改密码" >&2
  exit 1
fi

API_IMG="$(docker compose -f "$COMPOSE_FILE" images -q api)"
[ -n "$API_IMG" ] || { echo "[ERR] api 镜像未构建，先跑 ./scripts/deploy.sh" >&2; exit 1; }
API_CTN="$(docker compose -f "$COMPOSE_FILE" ps -q api)"
NET="$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$API_CTN" | awk '{print $1}')"
[ -n "$NET" ] || { echo "[ERR] 取不到 compose 网络（api 容器是否已启动？）" >&2; exit 1; }

echo "[owner] 写入 owner_admin（幂等，已存在则重置密码）…"
docker run --rm \
  --network "$NET" \
  -v "$PWD/scripts:/srv/jianli/scripts:ro" \
  -e "JIANLI_DATABASE_URL=postgresql+psycopg://${PGUSER}:${PGPASS}@postgres:5432/${PGDB}" \
  -e "JIANLI_OWNER_EMAIL=$OWNER_EMAIL" \
  -e "JIANLI_OWNER_PASSWORD=$OWNER_PASSWORD" \
  -w /srv/jianli \
  "$API_IMG" python scripts/create_owner.py
