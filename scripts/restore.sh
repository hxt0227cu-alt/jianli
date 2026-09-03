#!/usr/bin/env bash
# Restore an encrypted backup only into an explicitly isolated DB and new directory.
set -euo pipefail
umask 077

cd "$(dirname "$0")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
die() { echo "[ERR] $*" >&2; exit 1; }
for tool in docker python3 psql pg_restore sha256sum openssl mktemp readlink stat; do
  command -v "$tool" >/dev/null 2>&1 || die "missing required tool: $tool"
done
docker info >/dev/null 2>&1 || die "Docker daemon is unavailable; production volume safety cannot be checked"
[ "$#" -eq 1 ] || { echo "usage: $0 <jianli-backup-*.tar.gz.enc>" >&2; exit 2; }
ARCHIVE="$(readlink -f "$1")"; CHECKSUM="$ARCHIVE.sha256"
ENV_FILE="${JIANLI_ENV_FILE:-$PWD/.env}"
[ -f "$ARCHIVE" ] && [ -f "$CHECKSUM" ] || die "archive or adjacent checksum is missing"
[ -f "$ENV_FILE" ] || die "production env file is required for safety comparison"
[ -f "$COMPOSE_FILE" ] || die "production compose file is required for volume safety comparison"
[ "${JIANLI_RESTORE_CONFIRM:-}" = "ISOLATED_RESTORE" ] || die "set JIANLI_RESTORE_CONFIRM=ISOLATED_RESTORE"

env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | sed 's/^"//;s/"$//'; }
PASSPHRASE="${JIANLI_BACKUP_PASSPHRASE:-}"
MAX_RESTORE_BYTES="${JIANLI_RESTORE_MAX_BYTES:-10737418240}"
DB_HOST="${JIANLI_RESTORE_DB_HOST:-}"; DB_PORT="${JIANLI_RESTORE_DB_PORT:-}"
DB_NAME="${JIANLI_RESTORE_DB_NAME:-}"; DB_USER="${JIANLI_RESTORE_DB_USER:-}"
DB_PASS="${JIANLI_RESTORE_DB_PASSWORD:-}"; KNOW_DIR="${JIANLI_RESTORE_KNOWLEDGE_DIR:-}"
RESTORE_ROOT="${JIANLI_RESTORE_ROOT:-}"
[ "${#PASSPHRASE}" -ge 20 ] || die "strong backup passphrase is required"
[[ "$MAX_RESTORE_BYTES" =~ ^[1-9][0-9]*$ ]] || die "JIANLI_RESTORE_MAX_BYTES must be a positive integer"
for value in "$DB_HOST" "$DB_PORT" "$DB_NAME" "$DB_USER" "$DB_PASS" "$KNOW_DIR" "$RESTORE_ROOT"; do
  [ -n "$value" ] || die "all isolated restore variables are required"
done
[[ "$DB_HOST" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]*$ ]] \
  || die "restore DB host must be a bare hostname or IP address"
[[ "$DB_PORT" =~ ^[0-9]{1,5}$ ]] && (( 10#$DB_PORT >= 1 && 10#$DB_PORT <= 65535 )) \
  || die "restore DB port must be between 1 and 65535"
[[ "$DB_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]] \
  || die "restore DB name must be a plain PostgreSQL identifier"
[[ "$DB_USER" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]] \
  || die "restore DB user must be a plain PostgreSQL identifier"
PROD_DB="$(env_value JIANLI_POSTGRES_DB)"; PROD_DB="${PROD_DB:-jianli_prod}"
PROD_USER="$(env_value JIANLI_POSTGRES_USER)"; PROD_USER="${PROD_USER:-jianli}"
PROD_PASS="$(env_value JIANLI_POSTGRES_PASSWORD)"
[ "$DB_NAME" != "$PROD_DB" ] || die "restore DB name must differ from production"
[ "$DB_USER" != "$PROD_USER" ] || die "restore DB user must differ from production"
[ -z "$PROD_PASS" ] || [ "$DB_PASS" != "$PROD_PASS" ] || die "restore DB password must differ from production"
KNOW_DIR="$(readlink -m "$KNOW_DIR")"
RESTORE_ROOT="$(readlink -m "$RESTORE_ROOT")"
PROD_KNOW_DIR="$(env_value JIANLI_KNOWLEDGE_STORAGE_DIR)"
PROD_KNOW_DIR="$(readlink -m "${PROD_KNOW_DIR:-/srv/jianli/var/knowledge}")"
[ "$PROD_KNOW_DIR" != "/" ] || die "production knowledge directory in env is unsafe"
case "$RESTORE_ROOT" in /|/tmp|/var|/srv|/home|"$PWD"|"$PWD"/*|"$PROD_KNOW_DIR"|"$PROD_KNOW_DIR"/*) die "unsafe restore root" ;; esac
case "$(basename "$RESTORE_ROOT")" in jianli-restore|jianli-restore-*) ;; *) die "restore root basename must start with jianli-restore" ;; esac
case "$KNOW_DIR" in "$RESTORE_ROOT"/*) ;; *) die "restore knowledge directory must be a child of restore root" ;; esac
[ "$(dirname "$KNOW_DIR")" = "$RESTORE_ROOT" ] || die "restore knowledge directory must be a direct child of restore root"
[ ! -e "$KNOW_DIR" ] || die "restore knowledge directory must not already exist"
if ! compose_json="$(JIANLI_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" \
  -f "$COMPOSE_FILE" config --format json 2>/dev/null)"; then
  die "cannot render the production compose model for volume safety comparison"
fi
if ! VOLUME_NAME="$(python3 -c \
  'import json,sys; print(json.load(sys.stdin)["volumes"]["jianli_knowledge"]["name"])' \
  <<< "$compose_json")" || [ -z "$VOLUME_NAME" ]; then
  die "cannot resolve the production knowledge volume name"
fi
unset compose_json
if volume_mount="$(docker volume inspect "$VOLUME_NAME" --format '{{ .Mountpoint }}' 2>/dev/null)"; then
  volume_mount="$(readlink -m "$volume_mount")"
  case "$RESTORE_ROOT" in "$volume_mount"|"$volume_mount"/*) die "restore root overlaps the production knowledge volume" ;; esac
else
  volume_error="$(docker volume inspect "$VOLUME_NAME" 2>&1 || true)"
  printf '%s' "$volume_error" | grep -qi 'no such volume' \
    || die "cannot verify the production knowledge volume"
  unset volume_error
fi
if [ -e "$RESTORE_ROOT" ]; then
  [ -d "$RESTORE_ROOT" ] && [ ! -L "$RESTORE_ROOT" ] && [ -O "$RESTORE_ROOT" ] || die "restore root must be a real directory owned by the current user"
  root_mode="$(stat -c '%a' "$RESTORE_ROOT")"
  (( (8#$root_mode & 077) == 0 )) || die "restore root must not be group/world accessible"
else
  mkdir -p -m 700 "$RESTORE_ROOT"
fi
probe="$RESTORE_ROOT/.write-probe-$$"
: > "$probe" && rm -f -- "$probe" || die "restore root is not writable"

if ! db_empty="$(PGPASSWORD="$DB_PASS" psql -XAtq -v ON_ERROR_STOP=1 \
  -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -c "SELECT NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
          AND n.nspname !~ '^pg_toast'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
      )")"; then
  die "cannot connect to the isolated restore database"
fi
[ "$db_empty" = "t" ] || die "restore database must already exist and be empty"

read -r expected recorded extra < "$CHECKSUM"
[[ "$expected" =~ ^[0-9a-fA-F]{64}$ ]] && [ "$recorded" = "$(basename "$ARCHIVE")" ] \
  && [ -z "${extra:-}" ] && [ "$(wc -l < "$CHECKSUM")" -eq 1 ] || die "invalid checksum file"
actual="$(sha256sum "$ARCHIVE")"; actual="${actual%% *}"
[ "$actual" = "$expected" ] || die "archive checksum mismatch"
[ "$(stat -c '%s' "$ARCHIVE")" -le "$MAX_RESTORE_BYTES" ] \
  || die "encrypted archive exceeds restore size limit"
echo "$(basename "$ARCHIVE"): OK"
export JIANLI_BACKUP_PASSPHRASE="$PASSPHRASE"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/jianli-restore.XXXXXX")"; chmod 700 "$TMP_DIR"
SAFE_DB_NAME="${DB_NAME//[^A-Za-z0-9_.-]/_}"
STAGE_DIR="$RESTORE_ROOT/.staging-$SAFE_DB_NAME-$$"
mkdir -m 700 "$STAGE_DIR"
cleanup() {
  case "$TMP_DIR" in */jianli-restore.*) rm -rf -- "$TMP_DIR" ;;
  esac
  if [ -n "${STAGE_DIR:-}" ] && [ "$(dirname "$STAGE_DIR")" = "$RESTORE_ROOT" ]; then
    rm -rf -- "$STAGE_DIR"
  fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:JIANLI_BACKUP_PASSPHRASE \
  -in "$ARCHIVE" -out "$TMP_DIR/package.tar.gz"
python3 - "$TMP_DIR/package.tar.gz" "$TMP_DIR" "$MAX_RESTORE_BYTES" <<'PY'
import shutil
import sys
import tarfile

archive_path, target_dir, max_bytes_raw = sys.argv[1:]
max_bytes = int(max_bytes_raw)
expected = {"database.dump", "knowledge.tar"}
seen: set[str] = set()
total = 0
with tarfile.open(archive_path, mode="r|gz") as archive:
    for member in archive:
        if member.name not in expected or member.name in seen or not member.isfile():
            raise SystemExit("unexpected encrypted package contents")
        seen.add(member.name)
        total += member.size
        if total > max_bytes:
            raise SystemExit("encrypted package exceeds restore size limit")
        source = archive.extractfile(member)
        if source is None:
            raise SystemExit("cannot read encrypted package member")
        with source, open(f"{target_dir}/{member.name}", "xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
if seen != expected:
    raise SystemExit("unexpected encrypted package contents")
PY
python3 - "$TMP_DIR/knowledge.tar" "$STAGE_DIR" "$MAX_RESTORE_BYTES" <<'PY'
import sys
import tarfile
from pathlib import PurePosixPath

archive_path, target_dir, max_bytes_raw = sys.argv[1:]
seen: set[str] = set()
total = 0
count = 0
with tarfile.open(archive_path, mode="r|") as archive:
    for member in archive:
        count += 1
        if count > 10000:
            raise SystemExit("knowledge archive contains excessive members")
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit("unsafe knowledge archive path")
        normalized = str(path)
        if normalized in seen:
            raise SystemExit("knowledge archive contains duplicate members")
        seen.add(normalized)
        if not (member.isfile() or member.isdir()):
            raise SystemExit("unsafe knowledge archive member type")
        total += member.size
        if total > int(max_bytes_raw):
            raise SystemExit("knowledge archive exceeds restore size limit")
        archive.extract(member, target_dir, filter="data")
PY
chmod -R go-rwx "$STAGE_DIR"
echo "[restore] restoring into isolated database $DB_NAME"
PGPASSWORD="$DB_PASS" pg_restore --exit-on-error --single-transaction --no-owner --no-privileges \
  -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" "$TMP_DIR/database.dump"
mv -T -- "$STAGE_DIR" "$KNOW_DIR"
STAGE_DIR=""
echo "[restore] complete: database=$DB_NAME knowledge=$KNOW_DIR"
