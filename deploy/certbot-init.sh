#!/usr/bin/env bash
# TASK-DEPLOY-001: obtain/refresh Let's Encrypt certs for the nginx container.
# Requires the domain to already resolve to this server and ICP filing done.
# Run on the host (NOT inside a container); certs land in ./deploy/certbot.

set -euo pipefail

DOMAIN="${1:?usage: $0 <your-domain>}"
EMAIL="${2:-}"

mkdir -p deploy/certbot/conf deploy/certbot/www

if ! [[ "${DOMAIN}" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Invalid domain: ${DOMAIN}" >&2
  exit 2
fi

if [ -f "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem" ]; then
  echo ">> Certificate exists; refreshing…"
  docker compose -f docker-compose.prod.yml --profile tools run --rm certbot renew
else
  echo ">> Obtaining certificate for ${DOMAIN}…"
  args=(certonly --webroot -w /var/www/certbot -d "${DOMAIN}")
  if [ -n "${EMAIL}" ]; then
    args+=(-m "${EMAIL}" --agree-tos --no-eff-email)
  else
    args+=(--register-unsafely-without-email --agree-tos)
  fi
  docker compose -f docker-compose.prod.yml --profile tools run --rm certbot "${args[@]}"
fi

test -f "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem"
mkdir -p deploy/runtime
sed "s/__DOMAIN__/${DOMAIN}/g" deploy/nginx-https.conf.template > deploy/runtime/default.conf.next
mv deploy/runtime/default.conf.next deploy/runtime/default.conf

docker compose -f docker-compose.prod.yml exec nginx nginx -t
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
echo ">> HTTPS enabled for ${DOMAIN}."
