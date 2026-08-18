#!/usr/bin/env bash
# TASK-DEPLOY-001: one-shot production deploy on the Aliyun lightweight server.
# Prereqs: Docker + Compose v2 installed; .env populated; frontend built (dist/);
# domain DNS → this server; ICP filing complete (for CN mainland access).
# Run from the repository root on the server.

set -euo pipefail

cd "$(dirname "$0")/.."

echo ">> 1/4 Validate compose file"
docker compose -f docker-compose.prod.yml config > /dev/null

echo ">> 2/4 Build images"
docker compose -f docker-compose.prod.yml build

echo ">> 3/4 Start stack"
docker compose -f docker-compose.prod.yml up -d

echo ">> 4/4 Health check"
sleep 5
docker compose -f docker-compose.prod.yml ps

echo ""
echo "== Done =="
echo "  HTTP site:   http://<server-ip>  (HTTPS after certbot + domain config)"
echo "  HTTPS certs: ./deploy/certbot-init.sh <your-domain>"
echo "  Logs:        docker compose -f docker-compose.prod.yml logs -f api worker"
