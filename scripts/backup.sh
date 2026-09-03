#!/usr/bin/env bash
# Encrypted PostgreSQL + knowledge-volume backup. Local outputs are .enc + .sha256 only.
set -euo pipefail
umask 077

cd "$(dirname "$0")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${JIANLI_ENV_FILE:-$PWD/.env}"
BACKUP_DIR="${BACKUP_DIR:-$PWD/backups}"
OPERATION_DIR="$PWD/backups"
KEEP_DAYS="${KEEP_DAYS:-14}"
OSS_BUCKET="${OSS_BUCKET:-}"

die() { echo "[ERR] $*" >&2; exit 1; }
for tool in docker python3 tar sha256sum openssl mktemp readlink flock; do
  command -v "$tool" >/dev/null 2>&1 || die "missing required tool: $tool"
done
[ -f "$ENV_FILE" ] || die "production env file not found"
[ ! -L "$BACKUP_DIR" ] || die "backup directory must not be a symlink"
BACKUP_DIR="$(readlink -m "$BACKUP_DIR")"
case "$BACKUP_DIR" in /|/tmp|/var|/srv|/home|"$PWD") die "unsafe backup directory" ;; esac
case "$(basename "$BACKUP_DIR")" in *backup*) ;; *) die "backup directory must be dedicated and contain 'backup' in its basename" ;; esac
case "$PWD/" in "$BACKUP_DIR"/*) die "backup directory must not contain the repository" ;; esac
mkdir -p "$BACKUP_DIR"
[ -d "$BACKUP_DIR" ] && [ ! -L "$BACKUP_DIR" ] || die "backup path is not a real directory"
chmod 700 "$BACKUP_DIR"
[[ "$KEEP_DAYS" =~ ^[0-9]+$ ]] || die "KEEP_DAYS must be a non-negative integer"
[ ! -L "$OPERATION_DIR" ] || die "operation lock directory must not be a symlink"
mkdir -p "$OPERATION_DIR"
[ -d "$OPERATION_DIR" ] && [ ! -L "$OPERATION_DIR" ] || die "operation lock path is not a real directory"
chmod 700 "$OPERATION_DIR"
exec 9>>"$OPERATION_DIR/.operations.lock"
flock -n 9 || die "another deploy or backup operation is already running"

env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | sed 's/^"//;s/"$//'; }
PGUSER="${JIANLI_POSTGRES_USER:-$(env_value JIANLI_POSTGRES_USER)}"; PGUSER="${PGUSER:-jianli}"
PGDB="${JIANLI_POSTGRES_DB:-$(env_value JIANLI_POSTGRES_DB)}"; PGDB="${PGDB:-jianli_prod}"
PASSPHRASE="${JIANLI_BACKUP_PASSPHRASE:-}"
[ "${#PASSPHRASE}" -ge 20 ] || die "strong backup passphrase missing"
export JIANLI_BACKUP_PASSPHRASE="$PASSPHRASE" JIANLI_ENV_FILE="$ENV_FILE"
compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/jianli-backup.XXXXXX")"; chmod 700 "$TMP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%S%NZ)-$$"
ARCHIVE="$BACKUP_DIR/jianli-backup-$STAMP.tar.gz.enc"
CHECKSUM="$ARCHIVE.sha256"; PART="$ARCHIVE.part"; SUCCESS=0; API_WAS_RUNNING=0
cleanup() {
  if [ "$API_WAS_RUNNING" -eq 1 ]; then
    "${compose[@]}" start api >/dev/null 2>&1 || true
  fi
  case "$TMP_DIR" in */jianli-backup.*) rm -rf -- "$TMP_DIR" ;; esac
  [ "$SUCCESS" -eq 1 ] || rm -f -- "$PART" "$ARCHIVE" "$CHECKSUM"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[backup] creating encrypted backup"
running_services="$("${compose[@]}" ps --status running --services)"
if printf '%s\n' "$running_services" | grep -qx 'seed-kb'; then
  die "seed-kb is running; retry after knowledge initialization completes"
fi
if printf '%s\n' "$running_services" | grep -qx 'api'; then
  API_WAS_RUNNING=1
  "${compose[@]}" stop -t 60 api
fi
"${compose[@]}" exec -T postgres pg_dump -U "$PGUSER" -d "$PGDB" -F c > "$TMP_DIR/database.dump"
"${compose[@]}" exec -T postgres psql -XAtq -v ON_ERROR_STOP=1 -U "$PGUSER" -d "$PGDB" \
  -c "SELECT regexp_replace(storage_key, '^knowledge/', '')
      FROM knowledge_documents
      WHERE status = 'indexed' AND retrieval_disabled_at IS NULL
      ORDER BY storage_key" > "$TMP_DIR/active-knowledge.txt"
"${compose[@]}" run --rm --no-deps -T api python - > "$TMP_DIR/knowledge.tar" <<'PY'
import os
import stat
import sys
import tarfile

knowledge_dir = os.environ["JIANLI_KNOWLEDGE_STORAGE_DIR"]


def validate_tree() -> None:
    try:
        root_mode = os.lstat(knowledge_dir).st_mode
    except FileNotFoundError as error:
        raise SystemExit("knowledge storage directory is missing") from error
    if not stat.S_ISDIR(root_mode):
        raise SystemExit("knowledge storage path must be a real directory")
    for current_dir, directory_names, file_names in os.walk(
        knowledge_dir, topdown=True, followlinks=False
    ):
        for name in directory_names + file_names:
            entry = os.lstat(os.path.join(current_dir, name))
            if stat.S_ISDIR(entry.st_mode):
                continue
            if stat.S_ISREG(entry.st_mode) and entry.st_nlink == 1:
                continue
            raise SystemExit("knowledge storage contains an unsafe member type")


def safe_member(member: tarfile.TarInfo) -> tarfile.TarInfo:
    if not (member.isfile() or member.isdir()):
        raise SystemExit("knowledge storage changed to an unsafe member type")
    return member


validate_tree()
with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
    archive.add(knowledge_dir, arcname=".", recursive=True, filter=safe_member)
validate_tree()
PY
python3 - "$TMP_DIR/knowledge.tar" "$TMP_DIR/active-knowledge.txt" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

archive_path, manifest_path = sys.argv[1:]
expected = {line.strip() for line in open(manifest_path, encoding="utf-8") if line.strip()}
with tarfile.open(archive_path, mode="r:") as archive:
    members = archive.getmembers()
    if any(not (member.isfile() or member.isdir()) for member in members):
        raise SystemExit("knowledge snapshot contains an unsafe member type")
    present = {
        PurePosixPath(member.name).name
        for member in members
        if member.isfile()
    }
missing = sorted(expected - present)
if missing:
    raise SystemExit(f"knowledge snapshot missing {len(missing)} active object(s)")
PY
if [ "$API_WAS_RUNNING" -eq 1 ]; then
  "${compose[@]}" start api >/dev/null
  API_WAS_RUNNING=0
fi
tar -C "$TMP_DIR" -czf - database.dump knowledge.tar |
  openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass env:JIANLI_BACKUP_PASSPHRASE -out "$PART"
mv "$PART" "$ARCHIVE"
(cd "$BACKUP_DIR" && sha256sum "$(basename "$ARCHIVE")" > "$(basename "$CHECKSUM")")
chmod 600 "$ARCHIVE" "$CHECKSUM"; SUCCESS=1

find "$BACKUP_DIR" -type f \( -name 'jianli-backup-*.tar.gz.enc' -o -name 'jianli-backup-*.tar.gz.enc.sha256' \) -mtime +"$KEEP_DAYS" -delete
if [ -n "$OSS_BUCKET" ]; then
  command -v ossutil >/dev/null 2>&1 || die "OSS_BUCKET set but ossutil is unavailable"
  ossutil cp "$ARCHIVE" "$OSS_BUCKET/$(basename "$ARCHIVE")"
  ossutil cp "$CHECKSUM" "$OSS_BUCKET/$(basename "$CHECKSUM")"
fi
echo "[backup] complete: $ARCHIVE and $CHECKSUM"
