#!/usr/bin/env bash
# verify.sh — Jianli 一键评测 harness（TASK-HARNESS-001）
#
# 在 WSL 中运行（项目 venv 为 Linux 结构）。复用 docker-compose.dev.yml 的
# PG(pgvector)/Redis 起独立测试库 jianli_test + Redis db15，不重建容器。
#
# 用法：
#   bash scripts/verify.sh            # 全量：pytest + ruff + mypy + 前端 + Playwright
#   bash scripts/verify.sh --quick    # 开发预检：离线后端子集（跳过真实 RAG/前端）
#   bash scripts/verify.sh --tc       # 发布门禁：真实 RAG + 迁移 + 全量前后端
#   bash scripts/verify.sh --quick --external-rag  # 强制在后端预检中运行真实 RAG
#
# 门禁语义（harness 工程核心：失败必须如实暴露，绝不静默通过）：
#   - 硬门禁（失败 → 退出码非 0）：测试库就绪、pytest（任何失败或冻结迁移测试跳过均判红）、
#     ruff check、ruff format、mypy、pnpm test/typecheck/build、Playwright E2E。
#   - 不保留失败基线或“已知存量”豁免；所有测试失败均按原始退出码阻断发布。
#   - production build 与 Playwright 都是发布硬门禁；本地不自动下载浏览器。
#
# 退出码：0=对应门禁通过；非0=失败（原始摘要仅写入已忽略的 _diag_verify.log）。

set -uo pipefail

# ---- WSL 守卫：发布 harness 在错误平台必须 fail closed --------------------------
if [[ ! -r /proc/sys/kernel/osrelease ]] || ! grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  if [[ "$(uname -r 2>/dev/null)" != *microsoft* ]]; then
    echo "[verify] 非 WSL 环境：harness 需在 WSL 中运行（项目 venv 为 Linux 结构）。" >&2
    echo "[verify] 请在 WSL 内执行： bash scripts/verify.sh" >&2
    exit 1
  fi
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="$ROOT/apps/api"
cd "$ROOT" || exit 1

QUICK=0
TC=0
EXTERNAL_RAG=0
for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    --tc) TC=1 ;;
    --external-rag) EXTERNAL_RAG=1 ;;
    *) echo "[verify] 未知参数: $arg" >&2; exit 2 ;;
  esac
done
OFFLINE_RAG=0
if [[ "$QUICK" -eq 1 && "$TC" -eq 0 && "$EXTERNAL_RAG" -eq 0 ]]; then
  OFFLINE_RAG=1
fi

# ---- 0. 失败记录器（必须在 stage 调用前定义）-----------------------------------
record_pit_on_fail() {
  local stage="$1"; local rc="${2:-1}"
  printf '%s\tstage=%s\trc=%s\tcommit=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$stage" "$rc" \
    "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)" \
    >> "$ROOT/_diag_verify.log" || true
}

# ---- 1. 加载 env（去除 CRLF，避免变量值带 \r）---------------------------------
if [[ ! -f "$API/.env.local" ]]; then
  echo "[verify] 缺少 $API/.env.local（密钥仅运行时环境变量）" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source <(sed 's/\r$//' "$API/.env.local")
set +a

# The local developer env may contain live SMTP/LLM/embedding/reranker/Feishu
# credentials. Chat/SMTP/Reranker/Feishu are always disabled here. The short pre-commit
# check is deliberately offline; every complete or --tc release gate must run
# the frozen real-embedding acceptance cases and therefore fails closed when the
# embedding provider is not configured.
unset JIANLI_SMTP_PASSWORD
unset JIANLI_LLM_BASE_URL JIANLI_LLM_API_KEY JIANLI_LLM_MODEL
unset JIANLI_RERANK_BASE_URL JIANLI_RERANK_API_KEY JIANLI_RERANK_MODEL
if [[ "$OFFLINE_RAG" -eq 1 ]]; then
  unset JIANLI_LLM_EMBEDDING_BASE_URL JIANLI_LLM_EMBEDDING_API_KEY JIANLI_LLM_EMBEDDING_MODEL
  echo "==> [verify] offline developer precheck: frozen real-RAG TC not executed"
else
  for key in JIANLI_LLM_EMBEDDING_BASE_URL JIANLI_LLM_EMBEDDING_API_KEY JIANLI_LLM_EMBEDDING_MODEL; do
    [ -n "${!key:-}" ] || { echo "[verify] 发布门禁缺少真实 RAG 配置: $key" >&2; exit 1; }
  done
  echo "==> [verify] frozen real-RAG gate: enabled (credentials redacted)"
fi
unset JIANLI_FEISHU_APP_ID JIANLI_FEISHU_APP_SECRET
unset JIANLI_FEISHU_BITABLE_BASE_TOKEN JIANLI_FEISHU_BITABLE_TABLE_ID
export JIANLI_ENVIRONMENT=test
export JIANLI_EMAIL_MODE=console
export JIANLI_CSRF_HMAC_KEY='test-csrf-key-32-bytes-minimum-value'
export JIANLI_RATE_LIMIT_HMAC_KEY='test-rate-key-32-bytes-minimum-value'
export JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID='k1'
export JIANLI_FIELD_ENCRYPTION_KEYS='{"k1":"AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE="}'
export JIANLI_COMPANY_FINGERPRINT_HMAC_KEY='AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI='
export JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY='AwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM='

# ---- 2. 覆盖为测试实例（复用 docker-compose，隔离 DB/redis）--------------------
if ! "$API/.venv/bin/python" - <<'PY'
import os
import sys
from urllib.parse import urlsplit

db = urlsplit(os.environ.get("JIANLI_DATABASE_URL", ""))
redis = urlsplit(os.environ.get("JIANLI_REDIS_URL", ""))
loopback = {"127.0.0.1", "localhost", "::1"}
safe = (
    db.scheme == "postgresql+psycopg"
    and db.hostname in loopback
    and db.port == 55432
    and db.path == "/jianli_dev"
    and redis.scheme == "redis"
    and redis.hostname in loopback
    and redis.port == 63790
    and redis.path == "/0"
)
if not safe:
    print(
        "[verify] 拒绝非本地测试目标；仅允许开发 Compose 的 "
        "PG loopback:55432/jianli_dev 与 Redis loopback:63790/0",
        file=sys.stderr,
    )
    raise SystemExit(1)
print("==> [verify] 本地测试目标守卫: loopback compose endpoints verified")
PY
then
  exit 1
fi
TEST_DB_URL="${JIANLI_DATABASE_URL%/*}/jianli_test"
export JIANLI_DATABASE_URL="$TEST_DB_URL"
export JIANLI_REDIS_URL="${JIANLI_REDIS_URL%/*}/15"
# 迁移 TC 必须按测试声明的专用库分进程执行，不能把同一个 URL 注入全量 pytest。
unset JIANLI_TEST_DATABASE_URL
VENV="$API/.venv/bin/python"

# A full or --tc invocation is a release gate, so a historical public report
# must fail here as well as in prepush.sh.  A standalone offline --quick remains
# a deliberately narrower developer precheck.
if [[ "$QUICK" -eq 0 || "$TC" -eq 1 ]]; then
  echo "==> [verify] versioned evaluation evidence freshness"
  "$VENV" "$ROOT/scripts/validate_eval_report.py" || exit 1
fi

TEST_DB_NAME="${JIANLI_DATABASE_URL##*/}"
TEST_DB_NAME="${TEST_DB_NAME%%\?*}"
TEST_REDIS_INDEX="${JIANLI_REDIS_URL##*/}"
TEST_REDIS_INDEX="${TEST_REDIS_INDEX%%\?*}"
echo "==> [verify] 测试库: $TEST_DB_NAME"
echo "==> [verify] 测试 Redis DB index: $TEST_REDIS_INDEX"

# ---- 2b. 直接依赖漂移必须失败，不得在验收过程中联网自愈 -----------------------
if ! "$VENV" - "$API/pyproject.toml" <<'PY'
import importlib.metadata
import sys
import tomllib

with open(sys.argv[1], "rb") as stream:
    project = tomllib.load(stream)["project"]
requirements = list(project.get("dependencies", []))
for group in project.get("optional-dependencies", {}).values():
    requirements.extend(group)
mismatches: list[str] = []
for requirement in requirements:
    name, separator, expected = requirement.partition("==")
    if not separator:
        mismatches.append(f"{requirement}: not exactly pinned")
        continue
    try:
        actual = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        mismatches.append(f"{name}: missing (expected {expected})")
    else:
        if actual != expected:
            mismatches.append(f"{name}: installed {actual}, expected {expected}")
if mismatches:
    print("[verify] 直接依赖与 pyproject.toml 不一致：", file=sys.stderr)
    for mismatch in mismatches:
        print(f"  - {mismatch}", file=sys.stderr)
    raise SystemExit(1)
PY
then
  echo "[verify] 请按 apps/api/pyproject.toml 重建 WSL venv；门禁不会联网自愈" >&2
  exit 1
fi
if ! "$VENV" -m pip check; then
  echo "[verify] pip 依赖关系检查失败；请重建 WSL venv" >&2
  exit 1
fi

# ---- 3. 建库 + 迁移（幂等）-----------------------------------------------------
HARNESS_TARGET_DATABASE_URL="$JIANLI_DATABASE_URL" "$VENV" "$API/scripts/harness_setup_db.py" \
  || { echo "[verify] 测试库准备失败" >&2; exit 1; }

AUTH_TEST_URL="${JIANLI_DATABASE_URL%/*}/jianli_auth_001_db"
case "${AUTH_TEST_URL##*/}" in
  jianli_auth_001_db) ;;
  *) echo "[verify] 拒绝非专用认证测试库: ${AUTH_TEST_URL##*/}" >&2; exit 1 ;;
esac
HARNESS_TARGET_DATABASE_URL="$AUTH_TEST_URL" "$VENV" "$API/scripts/harness_setup_db.py" \
  || { echo "[verify] 认证测试库准备失败" >&2; exit 1; }

if [[ "$TC" -eq 1 ]]; then
  TC_OPS_URL="${JIANLI_DATABASE_URL%/*}/jianli_tc_ops_002_db"
  TC_AIQA_URL="${JIANLI_DATABASE_URL%/*}/jianli_tc_aiqa_001_db"
  TC_FEISHU_URL="${JIANLI_DATABASE_URL%/*}/jianli_tc_feishu_001_db"
  for tc_url in "$TC_OPS_URL" "$TC_AIQA_URL" "$TC_FEISHU_URL"; do
    case "${tc_url##*/}" in
      jianli_tc_ops_002_db|jianli_tc_aiqa_001_db|jianli_tc_feishu_001_db) ;;
      *) echo "[verify] 拒绝非专用测试库: ${tc_url##*/}" >&2; exit 1 ;;
    esac
    HARNESS_TARGET_DATABASE_URL="$tc_url" "$VENV" "$API/scripts/harness_setup_db.py" \
      || { echo "[verify] TC 库准备失败: ${tc_url##*/}" >&2; exit 1; }
  done
fi

AIQA_STACK_URL="$JIANLI_DATABASE_URL"
if [[ "$TC" -eq 1 ]]; then
  AIQA_STACK_URL="$TC_AIQA_URL"
fi
export JIANLI_BOOKING_TEST_DATABASE_URL="$JIANLI_DATABASE_URL"
export JIANLI_BOOKING_TEST_REDIS_URL="$JIANLI_REDIS_URL"
export JIANLI_AUTH_TEST_DATABASE_URL="$AUTH_TEST_URL"
export JIANLI_AUTH_TEST_REDIS_URL="$JIANLI_REDIS_URL"
export JIANLI_AIQA_TEST_DATABASE_URL="$AIQA_STACK_URL"
export JIANLI_AIQA_TEST_REDIS_URL="$JIANLI_REDIS_URL"

# ---- 4. 门禁 ------------------------------------------------------------------
# harness 自有的 Python 文件（lint/format 作用域）。不碰 app/**（属本任务禁止修改
# 路径，且存量代码未达 ruff format 标准），只保证 harness 自身交付物整洁。
# 用绝对路径，避免与下方 cd "$API" 拼接出双重前缀。
HARNESS_PY=(
  "$ROOT/scripts/record_pit.py"
  "$ROOT/apps/api/tests/conftest.py"
  "$ROOT/apps/api/scripts/harness_setup_db.py"
)

FAIL=0
FAILED_STAGE=""

# 硬门禁：失败累加 FAIL 并结构化记录
run_stage() {
  local stage="$1"; shift
  echo ""
  echo "===== [verify] $stage ====="
  "$@"
  # 必须在 "$@" 之后立刻捕获 rc；若放在 fi 之后会捕获到 fi 的退出码(0)。
  local rc=$?
  if [[ "$rc" -ne 0 ]]; then
    FAIL=1
    FAILED_STAGE="$stage"
    record_pit_on_fail "$stage" "$rc"
  else
    echo "[verify] ok: $stage"
  fi
  return "$rc"
}

PYTEST_ARGS=(
  -q -p no:cacheprovider
  --ignore=tests/migrations
  --deselect=tests/test_worker.py::test_worker_real_smtp_e2e
)
if [[ "$OFFLINE_RAG" -eq 1 ]]; then
  PYTEST_ARGS+=(
    --deselect=tests/aiqa/test_rag_eval.py::test_rag_semantic_hit_cases
    --deselect=tests/aiqa/test_rag_eval.py::test_rag_extreme_semantic_hit_cases
    --deselect=tests/aiqa/test_rag_eval.py::test_pure_vector_ranking
    --deselect=tests/aiqa/test_rag_eval.py::test_rag_reject_cases
  )
fi

pytest_gate() {
  local out pytest_rc
  out=$("$VENV" -m pytest "${PYTEST_ARGS[@]}" 2>&1)
  pytest_rc=$?
  printf '%s\n' "$out"
  if [[ "$pytest_rc" -ne 0 ]]; then
    echo "[verify] pytest failed (rc=$pytest_rc)" >&2
    return "$pytest_rc"
  fi
  if printf '%s\n' "$out" | grep -Eq '(^|, )[0-9]+ skipped([,[:space:]]|$)'; then
    echo "[verify] pytest 出现未显式排除的 skip；真实栈门禁拒绝静默跳过" >&2
    return 1
  fi

  return 0
}

pytest_no_skip() {
  local out pytest_rc
  out=$("$@" 2>&1)
  pytest_rc=$?
  printf '%s\n' "$out"
  [ "$pytest_rc" -eq 0 ] || return "$pytest_rc"
  if printf '%s\n' "$out" | grep -Eq '(^|, )[0-9]+ skipped([,[:space:]]|$)'; then
    echo "[verify] migration pytest contained an unexpected skip" >&2
    return 1
  fi
}

cd "$API" || exit 1

run_stage "pytest" pytest_gate

if [[ "$TC" -eq 1 ]]; then
  run_stage "migration TC: ops" pytest_no_skip env JIANLI_TEST_DATABASE_URL="$TC_OPS_URL" \
    "$VENV" -m pytest -q -ra \
    tests/migrations/test_identity_schema.py \
    tests/migrations/test_booking_schema.py \
    tests/migrations/test_booking_constraints.py \
    tests/migrations/test_booking_referential.py \
    tests/migrations/test_outbox_audit_schema.py
  run_stage "migration TC: aiqa" pytest_no_skip env JIANLI_TEST_DATABASE_URL="$TC_AIQA_URL" \
    "$VENV" -m pytest -q -ra \
    tests/migrations/test_aiqa_schema.py \
    tests/migrations/test_aiqa_observations.py
  run_stage "migration TC: feishu" pytest_no_skip env JIANLI_TEST_DATABASE_URL="$TC_FEISHU_URL" \
    "$VENV" -m pytest -q -ra tests/migrations/test_feishu_schema.py
fi

run_stage "ruff check" "$VENV" -m ruff check --config "$API/pyproject.toml" .
run_stage "ruff format --check (harness files)" "$VENV" -m ruff format --check --config "$API/pyproject.toml" "${HARNESS_PY[@]}"
run_stage "mypy" "$VENV" -m mypy

# 前端发布门禁不安装依赖或浏览器；缺浏览器时给出一次性安装命令并快速失败。
playwright_gate() {
  local browser_path
  browser_path=$(node --input-type=module -e \
    "import { chromium } from '@playwright/test'; process.stdout.write(chromium.executablePath())") \
    || return 1
  if [[ ! -x "$browser_path" ]]; then
    echo "[verify] 未找到 Playwright Chromium: $browser_path" >&2
    echo "[verify] 请联网时一次性执行: pnpm exec playwright install --with-deps chromium" >&2
    return 1
  fi
  pnpm exec playwright test
}

if [[ "$QUICK" -eq 0 ]]; then
  cd "$ROOT" || exit 1
  if command -v pnpm >/dev/null 2>&1; then
    run_stage "pnpm test" pnpm test
    run_stage "pnpm typecheck" pnpm typecheck
    run_stage "pnpm build" pnpm build
    run_stage "Playwright E2E" playwright_gate
  else
    echo "[verify] pnpm 不可用；无法执行前端发布门禁" >&2
    FAIL=1
    FAILED_STAGE="pnpm availability"
    record_pit_on_fail "$FAILED_STAGE" 127
  fi
else
  echo ""
  echo "===== [verify] 前端：跳过（--quick）====="
fi

if [[ "$OFFLINE_RAG" -eq 1 ]]; then
  echo "===== [verify] 真实 BGE-M3 冻结 TC 4 项：开发预检未执行；本结果不可作为发布证据 ====="
fi

# ---- 5. 收尾 ------------------------------------------------------------------
if [[ "$FAIL" -ne 0 ]]; then
  echo ""
  echo "[verify] ✗ 有硬门禁失败（stage=$FAILED_STAGE），详见上方输出与本地 _diag_verify.log"
  exit 1
fi

echo ""
if [[ "$QUICK" -eq 1 ]]; then
  if [[ "$OFFLINE_RAG" -eq 1 ]]; then
    echo "[verify] ✓ 离线开发预检通过；真实 RAG、前端与 Playwright 未执行，不是发布通过"
  else
    echo "[verify] ✓ 后端发布门禁通过（含真实 RAG 与 migration TC（如启用））；前端与 Playwright 已按 --quick 跳过"
  fi
else
  echo "[verify] ✓ 全量硬门禁通过（pytest / migration TC（如启用）/ ruff / mypy / 前端 / Playwright 全绿）"
fi
exit 0
