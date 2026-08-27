#!/usr/bin/env bash
# Local equivalent of Agent Quality Gate. This script never pushes or writes remotely.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/apps/api"
TEST_DATABASE_URL="${JIANLI_AIQA_TEST_DATABASE_URL:-postgresql+psycopg://jianli:jianli_local_only@127.0.0.1:55432/jianli_tc_aiqa_001_db}"
TEST_REDIS_URL="${JIANLI_AIQA_TEST_REDIS_URL:-redis://127.0.0.1:63790/1}"

cd "$REPO_ROOT"
docker compose -f docker-compose.dev.yml up -d postgres redis
docker compose -f docker-compose.dev.yml exec -T postgres sh -c \
  "psql -U jianli -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='jianli_tc_aiqa_001_db'\" | grep -q 1 || createdb -U jianli jianli_tc_aiqa_001_db"

source "$API_DIR/.venv/bin/activate"
python scripts/validate_eval_report.py

cd "$API_DIR"
JIANLI_DATABASE_URL="$TEST_DATABASE_URL" alembic upgrade head
export PYTHONPATH=.
export JIANLI_AIQA_TEST_DATABASE_URL="$TEST_DATABASE_URL"
export JIANLI_AIQA_TEST_REDIS_URL="$TEST_REDIS_URL"
export JIANLI_CSRF_HMAC_KEY="ci-csrf-key-32-bytes-minimum-value"
export JIANLI_RATE_LIMIT_HMAC_KEY="ci-rate-key-32-bytes-minimum-value"

pytest \
  tests/aiqa/test_agent_lab.py \
  tests/aiqa/test_agent_tools.py \
  tests/aiqa/test_aiqa.py \
  tests/aiqa/test_resilience.py \
  tests/aiqa/test_distributed_resilience.py \
  tests/aiqa/test_semantic_cache.py \
  tests/test_observability.py -q

pytest \
  tests/aiqa/test_rag_eval.py::test_rag_literal_hit_cases \
  tests/aiqa/test_rag_eval.py::test_rag_reject_cases \
  tests/aiqa/test_rag_eval.py::test_privacy_questions_refused \
  tests/aiqa/test_rag_eval.py::test_rag_false_reject_cases \
  tests/aiqa/test_distributed_resilience.py::test_real_redis_cross_instance_atomic_probe \
  -q

ruff check \
  app \
  tests/aiqa/test_agent_lab.py \
  tests/aiqa/test_resilience.py \
  tests/aiqa/test_distributed_resilience.py \
  tests/aiqa/test_semantic_cache.py \
  tests/test_observability.py
mypy app

cd "$REPO_ROOT"
CI=1 pnpm install --frozen-lockfile
pnpm test
pnpm typecheck
pnpm build
if command -v git.exe >/dev/null 2>&1; then
  git.exe diff --check
else
  git diff --check
fi
echo "pre-push quality gate passed; no push was performed"
