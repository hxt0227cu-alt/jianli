#!/usr/bin/env bash
# Local release gate equivalent to Agent Quality Gate. It never pushes or writes remotely.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"
"$REPO_ROOT/apps/api/.venv/bin/python" scripts/validate_eval_report.py
docker compose -f docker-compose.dev.yml up -d --pull never --wait --wait-timeout 60 postgres redis
bash scripts/verify.sh --tc
# WSL interop may expose git.exe in PATH while refusing to execute it. Linux Git
# with the repository's CRLF policy gives the same whitespace result; suppress only
# line-ending conversion warnings, while preserving the command's exit status.
git -c core.autocrlf=true diff --check 2>/dev/null
echo "pre-push quality gate passed; no push was performed"
