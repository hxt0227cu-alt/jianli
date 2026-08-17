#!/usr/bin/env bash
# install-hooks.sh — 把 scripts/git-hooks/* 安装到 .git/hooks/（TASK-HARNESS-001）
#
# .git/hooks/ 不被 git 跟踪（不入库）；hook 源文件在 scripts/git-hooks/ 受版本控制。
# 幂等：重复运行会覆盖，不影响其他已存在的 hook。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
SRC="$ROOT/scripts/git-hooks"
HOOKS="$ROOT/.git/hooks"

if [[ ! -d "$SRC" ]]; then
  echo "[install-hooks] 缺少 $SRC" >&2
  exit 1
fi
mkdir -p "$HOOKS"

for h in pre-commit pre-push; do
  if [[ -f "$SRC/$h" ]]; then
    cp "$SRC/$h" "$HOOKS/$h"
    chmod +x "$HOOKS/$h"
    echo "[install-hooks] 已安装 $h -> $HOOKS/$h"
  else
    echo "[install-hooks] 缺少 $SRC/$h" >&2
  fi
done

echo ""
echo "[install-hooks] 完成。hooks 在 WSL 中于 commit/push 时自动评测；非 WSL 自动跳过。"
echo "[install-hooks] 应急跳过：提交前设 JIANLI_SKIP_HOOK=1"
