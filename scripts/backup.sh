#!/usr/bin/env bash
# TASK-DEPLOY-001: 生产数据自动备份（cron 友好）。
# 备份内容：
#   1) PostgreSQL 逻辑备份（pg_dump -F c），预约/用户/会话/知识库元数据全量；
#   2) 知识库对象存储卷（jianli_knowledge）tar 打包，上传文档实际文件。
# 可选：OSS 异地备份（装 ossutil + 配置凭证，设 OSS_BUCKET 后自动上传）。
# 保留策略：默认保留 14 天（KEEP_DAYS 可调），旧备份自动清理。
#
# 用法：
#   手动：  ./scripts/backup.sh
#   cron：  crontab -e  →  0 3 * * * cd /root/jianli && ./scripts/backup.sh >> backups/backup.log 2>&1
#   （cron 若找不到 docker/compose，在 crontab 行首加 PATH=/usr/bin:/usr/local/bin）
set -euo pipefail

cd "$(dirname "$0")/.."                        # 项目根（脚本所在上级）
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$PWD/.env}"
BACKUP_DIR="${BACKUP_DIR:-$PWD/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
OSS_BUCKET="${OSS_BUCKET:-}"                   # 可选：oss://<bucket>/<prefix>

[ -f "$ENV_FILE" ] || { echo "[ERR] $ENV_FILE 不存在（生产密钥在该文件，未配置不备份）" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%F-%H%M)"

get_env() { grep "^$1=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//'; }
PGUSER="${JIANLI_POSTGRES_USER:-$(get_env JIANLI_POSTGRES_USER)}"; PGUSER="${PGUSER:-jianli}"
PGDB="${JIANLI_POSTGRES_DB:-$(get_env JIANLI_POSTGRES_DB)}"; PGDB="${PGDB:-jianli_prod}"
PGPASS="${JIANLI_POSTGRES_PASSWORD:-$(get_env JIANLI_POSTGRES_PASSWORD)}"
[ -n "$PGPASS" ] || { echo "[ERR] .env 缺少 JIANLI_POSTGRES_PASSWORD（compose 亦强制要求）" >&2; exit 1; }

# ── 1. PostgreSQL 逻辑备份 ──────────────────────────────────────────────
echo "[backup] $(date -Is) 开始 PG 逻辑备份（pg_dump -F c）…"
docker compose -f "$COMPOSE_FILE" exec -T -e "PGPASSWORD=$PGPASS" postgres \
  pg_dump -U "$PGUSER" -d "$PGDB" -F c -f /tmp/jianli-pg.dump
docker compose -f "$COMPOSE_FILE" cp postgres:/tmp/jianli-pg.dump "$BACKUP_DIR/jianli-pg-$STAMP.dump"
echo "[backup] PG 完成：$BACKUP_DIR/jianli-pg-$STAMP.dump"

# ── 2. 知识库对象存储卷（上传文档实际文件） ────────────────────────────
KNOW_VOL="$(docker volume ls -q | grep 'jianli_knowledge' | head -1)"
if [ -n "$KNOW_VOL" ]; then
  docker run --rm -v "$KNOW_VOL:/data:ro" -v "$BACKUP_DIR:/backup" alpine \
    tar czf "/backup/jianli-knowledge-$STAMP.tar.gz" -C /data .
  echo "[backup] 知识库卷完成：$BACKUP_DIR/jianli-knowledge-$STAMP.tar.gz"
else
  echo "[warn] 未找到 jianli_knowledge 卷，跳过知识库备份"
fi

# ── 3. 清理过期备份（默认保留 14 天） ───────────────────────────────────
find "$BACKUP_DIR" -name 'jianli-pg-*.dump' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'jianli-knowledge-*.tar.gz' -mtime +"$KEEP_DAYS" -delete

# ── 4. 可选：OSS 异地备份（防服务器磁盘故障/换机） ──────────────────────
if [ -n "$OSS_BUCKET" ]; then
  if command -v ossutil >/dev/null 2>&1; then
    ossutil cp "$BACKUP_DIR/jianli-pg-$STAMP.dump" "$OSS_BUCKET/jianli-pg-$STAMP.dump"
    [ -f "$BACKUP_DIR/jianli-knowledge-$STAMP.tar.gz" ] && \
      ossutil cp "$BACKUP_DIR/jianli-knowledge-$STAMP.tar.gz" "$OSS_BUCKET/jianli-knowledge-$STAMP.tar.gz"
    echo "[backup] OSS 上传完成"
  else
    echo "[warn] 未安装 ossutil（阿里云 OSS 客户端），跳过 OSS 上传"
  fi
fi

echo "[backup] 完成 ✅（保留 $KEEP_DAYS 天）"
