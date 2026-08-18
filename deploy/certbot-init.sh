#!/usr/bin/env bash
# TASK-DEPLOY-001: obtain/refresh Let's Encrypt certs for the nginx container.
# Requires the domain to already resolve to this server and ICP filing done.
# Run on the host (NOT inside a container); certs land in ./deploy/certbot.

set -euo pipefail

DOMAIN="${1:?usage: $0 <your-domain>}"
EMAIL="${2:-}"

mkdir -p deploy/certbot/conf deploy/certbot/www

if [ -f "deploy/certbot/conf/live/${DOMAIN}/fullchain.pem" ]; then
  echo ">> Certificate exists; refreshing…"
  docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
    certbot renew" certbot
else
  echo ">> Obtaining certificate for ${DOMAIN}…"
  docker compose -f docker-compose.prod.yml run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
      -d ${DOMAIN} ${EMAIL:+-m ${EMAIL} --agree-tos --no-eff-email}" certbot
fi

echo ">> Done. Reload nginx to pick up certs:"
echo "   docker compose -f docker-compose.prod.yml exec nginx nginx -s reload"
