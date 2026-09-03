#!/usr/bin/env bash
# Production deploy preflight + migration-first startup. Never prints secret values.
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${JIANLI_ENV_FILE:-$PWD/.env}"

die() { echo "[ERR] $*" >&2; exit 1; }
for tool in docker flock; do
  command -v "$tool" >/dev/null 2>&1 || die "missing required tool: $tool"
done
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required"
[ -f "$ENV_FILE" ] || die "production env file not found: $ENV_FILE"
mode="$(stat -c '%a' "$ENV_FILE")"
(( (8#$mode & 077) == 0 )) || die "production env file must not be group/world readable"
if grep -Eqi '^[A-Z0-9_]+=.*(CHANGE_ME|your-domain\.com)' "$ENV_FILE"; then
  die "production env still contains placeholder values"
fi

env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | sed 's/^"//;s/"$//'; }
is_https_dns_origin() {
  local url="$1" host
  [[ "$url" == https://* ]] || return 1
  host="${url#https://}"
  [ "${#host}" -le 253 ] || return 1
  [ "$host" = "${host,,}" ] || return 1
  [[ "$host" =~ ^([A-Za-z0-9][A-Za-z0-9-]{0,62}\.)+[A-Za-z][A-Za-z0-9-]{1,62}$ ]] || return 1
  [[ ".$host." != *.-* && ".$host." != *-.* ]]
}
required=(JIANLI_ENVIRONMENT JIANLI_EMAIL_MODE JIANLI_POSTGRES_PASSWORD
  JIANLI_REDIS_PASSWORD JIANLI_GRAFANA_ADMIN_PASSWORD JIANLI_CSRF_HMAC_KEY
  JIANLI_RATE_LIMIT_HMAC_KEY JIANLI_COMPANY_FINGERPRINT_HMAC_KEY
  JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID
  JIANLI_FIELD_ENCRYPTION_KEYS JIANLI_ALLOWED_ORIGINS JIANLI_WEB_BASE_URL
  JIANLI_SMTP_HOST JIANLI_SMTP_PORT JIANLI_SMTP_USER JIANLI_SMTP_PASSWORD JIANLI_SMTP_FROM
  JIANLI_FEISHU_APP_ID JIANLI_FEISHU_APP_SECRET JIANLI_FEISHU_BITABLE_BASE_TOKEN
  JIANLI_FEISHU_BITABLE_TABLE_ID JIANLI_LLM_BASE_URL JIANLI_LLM_API_KEY
  JIANLI_LLM_MODEL JIANLI_LLM_EMBEDDING_BASE_URL JIANLI_LLM_EMBEDDING_API_KEY
  JIANLI_LLM_EMBEDDING_MODEL JIANLI_LLM_EMBEDDING_DIM)
for key in "${required[@]}"; do
  value="$(env_value "$key")"
  [ -n "$value" ] || die "missing required production variable: $key"
  case "${value,,}" in
    *change_me*|*your-domain.com*|password|changeme|admin|secret)
      die "$key is a placeholder or weak default" ;;
  esac
done
for key in JIANLI_POSTGRES_PASSWORD JIANLI_REDIS_PASSWORD JIANLI_GRAFANA_ADMIN_PASSWORD; do
  value="$(env_value "$key")"
  [ "${#value}" -ge 20 ] || die "$key must contain at least 20 characters"
done
[ "$(env_value JIANLI_ENVIRONMENT)" = "production" ] || die "JIANLI_ENVIRONMENT must be production"
[ "$(env_value JIANLI_EMAIL_MODE)" = "smtp" ] || die "JIANLI_EMAIL_MODE must be smtp"
for key in JIANLI_POSTGRES_PASSWORD JIANLI_REDIS_PASSWORD; do
  value="$(env_value "$key")"
  [[ "$value" =~ ^[A-Za-z0-9_-]{20,}$ ]] || die "$key must be URL-safe (A-Z/a-z/0-9/_/-) and at least 20 characters"
done
[[ "$(env_value JIANLI_SMTP_PORT)" =~ ^[0-9]{1,5}$ ]] || die "JIANLI_SMTP_PORT must be numeric"
[ "$(env_value JIANLI_LLM_EMBEDDING_DIM)" = "1024" ] || die "JIANLI_LLM_EMBEDDING_DIM must match vector(1024)"
for key in JIANLI_WEB_BASE_URL JIANLI_LLM_BASE_URL JIANLI_LLM_EMBEDDING_BASE_URL; do
  value="$(env_value "$key")"
  [[ "$value" =~ ^https:// ]] || die "$key must use https"
done
web_base_url="$(env_value JIANLI_WEB_BASE_URL)"
is_https_dns_origin "$web_base_url" \
  || die "JIANLI_WEB_BASE_URL must be a DNS-only https origin"
IFS=',' read -r -a origins <<< "$(env_value JIANLI_ALLOWED_ORIGINS)"
[ "${#origins[@]}" -gt 0 ] || die "JIANLI_ALLOWED_ORIGINS is empty"
[ "${#origins[@]}" -eq 1 ] || die "production allows exactly one browser origin"
web_origin_allowed=0
for origin in "${origins[@]}"; do
  is_https_dns_origin "$origin" || die "every production origin must be a DNS-only https origin"
  [[ "$origin" != *localhost* && "$origin" != *127.0.0.1* && "$origin" != *\** ]] || die "production origin cannot be localhost or wildcard"
  [ "$origin" != "$web_base_url" ] || web_origin_allowed=1
done
[ "$web_origin_allowed" -eq 1 ] || die "JIANLI_WEB_BASE_URL must be listed exactly in JIANLI_ALLOWED_ORIGINS"
unset origin value web_base_url web_origin_allowed

# Docker Compose gives exported host variables precedence over --env-file.  The
# production env file is the reviewed source of truth, so reject a conflicting
# host value and then unset matching values before rendering the Compose model.
# Never include either value in the error message.
compose_env_keys=(
  JIANLI_POSTGRES_DB JIANLI_POSTGRES_USER JIANLI_POSTGRES_PASSWORD
  JIANLI_REDIS_PASSWORD JIANLI_GRAFANA_ADMIN_PASSWORD JIANLI_ALLOWED_ORIGINS
  JIANLI_FRONTEND_SUBNET JIANLI_BACKEND_SUBNET JIANLI_EGRESS_SUBNET
  JIANLI_ADMIN_SUBNET JIANLI_OBSERVABILITY_SUBNET JIANLI_API_IMAGE JIANLI_WEB_IMAGE
)
for key in "${compose_env_keys[@]}"; do
  if [[ -v "$key" ]]; then
    file_value="$(env_value "$key")"
    [ -n "$file_value" ] && [ "${!key}" = "$file_value" ] ||
      die "host environment overrides production env file: $key"
    unset "$key"
  fi
done
unset file_value key

[ ! -L "$PWD/backups" ] || die "backup directory must not be a symlink"
mkdir -p "$PWD/backups"; chmod 700 "$PWD/backups"
exec 9>>"$PWD/backups/.operations.lock"
flock -n 9 || die "another deploy or backup operation is already running"

export JIANLI_ENV_FILE="$ENV_FILE"
compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
mkdir -p deploy/runtime deploy/certbot/conf deploy/certbot/www
chmod 700 deploy/certbot/conf
[ -s deploy/runtime/default.conf ] || cp deploy/nginx.conf deploy/runtime/default.conf

echo ">> 1/4 Validate compose and production prerequisites"
"${compose[@]}" config >/dev/null
echo ">> 2/4 Build images (network failure is not retried)"
"${compose[@]}" build
echo ">> 3/4 Run migrations, initialize volume permissions, and start stack"
"${compose[@]}" up -d --wait --wait-timeout 120
echo ">> 4/4 Health check"
"${compose[@]}" ps

echo "== Bootstrap stack is healthy; application traffic remains closed until HTTPS is enabled."
echo "   Create owner_admin, initialize the canonical corpus, then issue the certificate:"
echo "   docker compose --profile tools --env-file <env-file> -f $COMPOSE_FILE run --rm seed-kb"
echo "   HTTPS: ./deploy/certbot-init.sh <domain> <email>"
