#!/usr/bin/env bash
# TASK-DEPLOY-001: obtain/refresh Let's Encrypt certs for the nginx container.
# Requires the domain to already resolve to this server and ICP filing done.
# Run on the host (NOT inside a container); certs land in ./deploy/certbot.

set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${JIANLI_ENV_FILE:-$PWD/.env}"
DOMAIN="${1:?usage: $0 <your-domain>}"
EMAIL="${2:-}"

die() { echo "[ERR] $*" >&2; exit 1; }
for tool in docker flock openssl; do
  command -v "$tool" >/dev/null 2>&1 || die "missing required tool: $tool"
done
[ -f "$COMPOSE_FILE" ] || die "compose file not found"
[ -f "$ENV_FILE" ] || die "production env file not found"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required"
env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | sed 's/^"//;s/"$//'; }
WEB_BASE_URL="$(env_value JIANLI_WEB_BASE_URL)"
[[ "$WEB_BASE_URL" == https://* ]] || die "JIANLI_WEB_BASE_URL must use https"
EXPECTED_DOMAIN="${WEB_BASE_URL#https://}"
[ "${#EXPECTED_DOMAIN}" -le 253 ] \
  && [ "$EXPECTED_DOMAIN" = "${EXPECTED_DOMAIN,,}" ] \
  && [[ "$EXPECTED_DOMAIN" =~ ^([A-Za-z0-9][A-Za-z0-9-]{0,62}\.)+[A-Za-z][A-Za-z0-9-]{1,62}$ ]] \
  && [[ ".$EXPECTED_DOMAIN." != *.-* && ".$EXPECTED_DOMAIN." != *-.* ]] \
  || die "JIANLI_WEB_BASE_URL must be a DNS-only https origin"
[ "$DOMAIN" = "$EXPECTED_DOMAIN" ] \
  || die "certificate domain must match JIANLI_WEB_BASE_URL"
IFS=',' read -r -a ALLOWED_ORIGINS <<< "$(env_value JIANLI_ALLOWED_ORIGINS)"
ORIGIN_MATCH=0
for origin in "${ALLOWED_ORIGINS[@]}"; do
  [ "$origin" != "$WEB_BASE_URL" ] || ORIGIN_MATCH=1
done
[ "$ORIGIN_MATCH" -eq 1 ] \
  || die "JIANLI_WEB_BASE_URL must be listed exactly in JIANLI_ALLOWED_ORIGINS"
export JIANLI_ENV_FILE="$ENV_FILE"
compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --profile tools)

OPERATION_DIR="$PWD/backups"
[ ! -L "$OPERATION_DIR" ] || die "operation lock directory must not be a symlink"
mkdir -p "$OPERATION_DIR"
[ -d "$OPERATION_DIR" ] && [ ! -L "$OPERATION_DIR" ] || die "operation lock path is not a real directory"
chmod 700 "$OPERATION_DIR"
exec 9>>"$OPERATION_DIR/.operations.lock"
flock -n 9 || die "another deploy, backup, or certificate operation is already running"

mkdir -p deploy/certbot/conf deploy/certbot/www deploy/runtime
chmod 700 deploy/certbot/conf

if ! [[ "${DOMAIN}" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Invalid domain: ${DOMAIN}" >&2
  exit 2
fi

if [ -f "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem" ]; then
  echo ">> Certificate exists; refreshing…"
  "${compose[@]}" run --rm certbot renew
else
  echo ">> Obtaining certificate for ${DOMAIN}…"
  args=(certonly --webroot -w /var/www/certbot -d "${DOMAIN}")
  if [ -n "${EMAIL}" ]; then
    args+=(-m "${EMAIL}" --agree-tos --no-eff-email)
  else
    args+=(--register-unsafely-without-email --agree-tos)
  fi
  "${compose[@]}" run --rm certbot "${args[@]}"
fi

test -f "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem"
openssl x509 -in "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem" \
  -noout -checkhost "$DOMAIN" >/dev/null \
  || die "issued certificate does not cover the requested domain"
openssl x509 -in "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem" \
  -noout -checkend 604800 >/dev/null \
  || die "issued certificate expires within seven days"
NEXT="$(mktemp "$PWD/deploy/runtime/default.conf.next.XXXXXX")"
PREVIOUS="$PWD/deploy/runtime/default.conf.previous.$$"
INSTALLED=0
HAD_PREVIOUS=0
SUCCESS=0
restore_previous() {
  if [ "$HAD_PREVIOUS" -eq 1 ] && [ -f "$PREVIOUS" ]; then
    mv -f -- "$PREVIOUS" deploy/runtime/default.conf
  else
    rm -f -- deploy/runtime/default.conf
  fi
  INSTALLED=0
}
cleanup() {
  rm -f -- "$NEXT"
  if [ "$INSTALLED" -eq 1 ] && [ "$SUCCESS" -eq 0 ]; then
    restore_previous
  fi
  rm -f -- "$PREVIOUS"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

sed "s/__DOMAIN__/${DOMAIN}/g" deploy/nginx-https.conf.template > "$NEXT"
if [ -f deploy/runtime/default.conf ]; then
  cp -- deploy/runtime/default.conf "$PREVIOUS"
  HAD_PREVIOUS=1
fi
INSTALLED=1
mv -- "$NEXT" deploy/runtime/default.conf

"${compose[@]}" exec -T nginx nginx -t || die "nginx rejected HTTPS config; previous config restored"
# Once reload begins, an interrupt could otherwise leave the process using the new
# config while EXIT cleanup restores the old file. Record signals in the parent and
# ignore them only in the reload child; after a successful reload the new disk state
# is durable, then the original signal may terminate the script consistently.
PENDING_SIGNAL=0
trap 'PENDING_SIGNAL=129' HUP
trap 'PENDING_SIGNAL=130' INT
trap 'PENDING_SIGNAL=143' TERM
if (
  trap '' HUP INT TERM
  "${compose[@]}" exec -T nginx nginx -s reload
); then
  SUCCESS=1
else
  restore_previous
  # Reload may have reached nginx even when the CLI reported failure. Best effort:
  # validate and reload the restored configuration before returning non-zero.
  "${compose[@]}" exec -T nginx nginx -t >/dev/null 2>&1 \
    && "${compose[@]}" exec -T nginx nginx -s reload >/dev/null 2>&1 \
    || true
  die "nginx reload failed; previous config restored"
fi
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
[ "$PENDING_SIGNAL" -eq 0 ] || exit "$PENDING_SIGNAL"
rm -f -- "$PREVIOUS"
echo ">> HTTPS enabled for ${DOMAIN}."
