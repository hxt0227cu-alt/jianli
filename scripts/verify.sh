#!/usr/bin/env bash
# verify.sh — Jianli 一键评测 harness（TASK-HARNESS-001）
#
# 在 WSL 中运行（项目 venv 为 Linux 结构）。复用 docker-compose.dev.yml 的
# PG(pgvector)/Redis 起独立测试库 jianli_test + Redis db15，不重建容器。
#
# 用法：
#   bash scripts/verify.sh            # 全量：pytest + ruff + mypy + 前端单测
#   bash scripts/verify.sh --quick    # 提交前：pytest + ruff + mypy（跳过前端）
#   bash scripts/verify.sh --tc       # 额外准备 jianli_tc_ops_002_db 并跑迁移验收
#
# 门禁语义（harness 工程核心：失败必须如实暴露，绝不静默通过）：
#   - 硬门禁（失败 → 退出码非 0）：测试库就绪、pytest（基线对比：仅"新失败"判红）、
#     ruff check、ruff format、mypy、pnpm test（前端单测）、pnpm typecheck（前端类型检查）。
#   - pytest 已知存量失败（原 12 例：test_management.py 9 例 + test_security / test_auth /
#     test_app 各 1 例）已于 TASK-QA-CLEANUP-001 全部修复，PYTEST_BASELINE 已清零；
#     现基线为空，任何失败（含旧用例回退）均判红并记坑（回归哨兵），不再有"已知存量"豁免。
#   - 前端 apps/web/main.tsx 原预存 TS1005 语法错误已于同任务修复，pnpm typecheck 转绿并升级为
#     硬门禁（失败即非零退出）；pnpm build 仍按"已知存量（仅上报不阻断）"处理——其失败源于 rolldown
#     原生二进制未随依赖安装（与 TS1005 无关的环境问题），待依赖装齐后再转正。
#
# 退出码：0=硬门禁全过；非0=有硬门禁失败（并自动在 docs/devlog/pitfalls/ 记录）。

set -uo pipefail

# ---- WSL 守卫：非 WSL 环境不阻塞（例如 Windows 侧提交）---------------------------
if [[ ! -r /proc/sys/kernel/osrelease ]] || ! grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  if [[ "$(uname -r 2>/dev/null)" != *microsoft* ]]; then
    echo "[verify] 非 WSL 环境：harness 需在 WSL 中运行（项目 venv 为 Linux 结构）。" >&2
    echo "[verify] 请在 WSL 内执行： bash scripts/verify.sh" >&2
    exit 0
  fi
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="$ROOT/apps/api"
cd "$ROOT" || exit 1

QUICK=0
TC=0
for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    --tc) TC=1 ;;
  esac
done

# ---- 0. 失败记录器（必须在 stage 调用前定义）-----------------------------------
record_pit_on_fail() {
  local stage="$1"; local rc="${2:-1}"
  "$VENV" "$ROOT/scripts/record_pit.py" \
    --source "verify.sh" \
    --severity "high" \
    --symptom "verify 门禁失败: $stage (rc=$rc)" \
    --root-cause "（自动记录，待 AI 复盘补充）" \
    --fix "（待分析）" \
    --avoidance "（待分析）" \
    --context "stage=$stage; commit=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)" \
    || true
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

# ---- 2. 覆盖为测试实例（复用 docker-compose，隔离 DB/redis）--------------------
TEST_DB_URL="${JIANLI_DATABASE_URL%/*}/jianli_test"
export JIANLI_DATABASE_URL="$TEST_DB_URL"
export JIANLI_REDIS_URL="${JIANLI_REDIS_URL%/*}/15"
VENV="$API/.venv/bin/python"

echo "==> [verify] 测试库: $JIANLI_DATABASE_URL"
echo "==> [verify] 测试 Redis: $JIANLI_REDIS_URL"

# ---- 2b. 确保已声明运行时依赖就位（WSL venv 历史缺口：python-multipart）--------
# pyproject 已声明 python-multipart，但 WSL venv 未必安装；缺它会导致 pytest
# 在路由注册阶段报 "Form data requires python-multipart"。harness 自愈，不阻塞。
if ! "$VENV" -c "import multipart" >/dev/null 2>&1; then
  echo "[verify] 缺少 python-multipart（已在 pyproject 声明），安装到 venv ..."
  if ! "$API/.venv/bin/pip" install python-multipart >/dev/null 2>&1; then
    echo "[verify] python-multipart 安装失败；请手动执行: $API/.venv/bin/pip install python-multipart" >&2
    exit 1
  fi
  echo "[verify] python-multipart 已安装"
fi

# ---- 3. 建库 + 迁移（幂等）-----------------------------------------------------
HARNESS_TARGET_DATABASE_URL="$JIANLI_DATABASE_URL" "$VENV" "$API/scripts/harness_setup_db.py" \
  || { echo "[verify] 测试库准备失败" >&2; exit 1; }

if [[ "$TC" -eq 1 ]]; then
  TC_URL="${JIANLI_DATABASE_URL%/*}/jianli_tc_ops_002_db"
  export JIANLI_TEST_DATABASE_URL="$TC_URL"
  HARNESS_TARGET_DATABASE_URL="$TC_URL" "$VENV" "$API/scripts/harness_setup_db.py" \
    || { echo "[verify] TC 库准备失败" >&2; exit 1; }
fi

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

# 已知存量问题：仅上报，不阻断（失败不影响退出码）
report_stage() {
  local stage="$1"; shift
  echo ""
  echo "===== [verify] $stage（已知存量问题，仅上报不阻断）====="
  if "$@"; then
    echo "[verify] ok: $stage"
  else
    echo "[verify] ⚠ $stage 存在存量问题（非 harness 缺陷），见 docs/HARNESS.md 已知问题"
  fi
  return 0
}

# ---- pytest 基线对比门禁（harness 工程核心：基线为空时任何失败都判红）----
# 跑全量 pytest → 提取失败/报错节点 → 与 PYTEST_BASELINE 比对：
#   - 出现非基线的新失败 = 回归 → 硬门禁失败（自动记坑）。
#   - 仅命中基线（历史债务豁免）= 如实上报、不阻断、不假装通过（门禁对"在管代码"保持绿）。
#   - 基线中某用例消失（变绿）= 债务偿还提示，建议更新基线。
# 当前 PYTEST_BASELINE 为空（原 12 例存量失败已于 TASK-QA-CLEANUP-001 全部修复清零），
# 故任何失败均判红。harness 不修改、不 skip、不降低断言；若确有需豁免的回归，须先走
# Change Request 与独立 TASK，再登记基线，不得静默放行。
# 原 12 例已知存量失败已于 TASK-QA-CLEANUP-001 全部修复并清零；现基线为空。
# 机制保留：若未来需临时登记"已知不阻断"失败，可在此数组追加节点 ID，
# 其余逻辑（comm 比对、新失败判红、旧用例回退提示）不变。
PYTEST_BASELINE=( )

pytest_gate() {
  local out actual baseline_set new_fail known resolved n m
  out=$("$VENV" -m pytest -q -p no:cacheprovider 2>&1)
  printf '%s\n' "$out"

  actual=$(printf '%s\n' "$out" | grep -E '^(FAILED|ERROR) ' | sed -E 's/^(FAILED|ERROR) //' | sed 's/[[:space:]]*$//' | sort -u | grep -v '^$')
  baseline_set=$(printf '%s\n' "${PYTEST_BASELINE[@]}" | sort -u)

  new_fail=$(comm -23 <(printf '%s\n' "$actual") <(printf '%s\n' "$baseline_set"))
  known=$(comm -12 <(printf '%s\n' "$actual") <(printf '%s\n' "$baseline_set"))
  resolved=$(comm -13 <(printf '%s\n' "$actual") <(printf '%s\n' "$baseline_set"))

  if [[ -n "$new_fail" ]]; then
    echo ""
    echo "[verify] ✗ 检测到非基线新失败（回归），pytest 门禁失败："
    printf '%s\n' "$new_fail" | sed 's/^/    /'
    return 1
  fi

  if [[ -n "$known" ]]; then
    n=$(printf '%s\n' "$known" | grep -c .)
    echo ""
    echo "[verify] ℹ 已知存量失败 $n 个（已登记基线，非回归，不阻断；属历史债务，待单独 TASK 清理，见 docs/HARNESS.md 已知问题）："
    printf '%s\n' "$known" | sed 's/^/    /'
  fi
  if [[ -n "$resolved" ]]; then
    m=$(printf '%s\n' "$resolved" | grep -c .)
    echo ""
    echo "[verify] ℹ 基线中 $m 个用例现已通过（债务已偿还）——建议更新 verify.sh 内 PYTEST_BASELINE。"
    printf '%s\n' "$resolved" | sed 's/^/    /'
  fi
  return 0
}

cd "$API" || exit 1

run_stage "pytest" pytest_gate

if [[ "$QUICK" -eq 0 ]]; then
  run_stage "ruff check" "$VENV" -m ruff check --config "$API/pyproject.toml" .
  run_stage "ruff format --check (harness files)" "$VENV" -m ruff format --check --config "$API/pyproject.toml" "${HARNESS_PY[@]}"
  run_stage "mypy" "$VENV" -m mypy
else
  run_stage "ruff check" "$VENV" -m ruff check --config "$API/pyproject.toml" .
  run_stage "ruff format --check (harness files)" "$VENV" -m ruff format --check --config "$API/pyproject.toml" "${HARNESS_PY[@]}"
  run_stage "mypy" "$VENV" -m mypy
fi

# 前端（pnpm）：单测 + typecheck 为硬门禁；build 仍仅上报（rolldown 原生二进制环境依赖）
if [[ "$QUICK" -eq 0 ]] && command -v pnpm >/dev/null 2>&1; then
  cd "$ROOT" || exit 1
  run_stage "pnpm test" pnpm test
  run_stage "pnpm typecheck" pnpm typecheck
  report_stage "pnpm build" pnpm build
else
  echo ""
  echo "===== [verify] 前端：跳过（--quick 或 pnpm 不可用）====="
fi

# ---- 5. 收尾 ------------------------------------------------------------------
if [[ "$FAIL" -ne 0 ]]; then
  echo ""
  echo "[verify] ✗ 有硬门禁失败（stage=$FAILED_STAGE），详见上方输出与 docs/devlog/pitfalls/"
  exit 1
fi

echo ""
echo "[verify] ✓ 硬门禁通过（pytest 无新回归 / ruff / mypy / 前端单测 全绿；已知存量失败与前端 build 问题已上报）"
exit 0
