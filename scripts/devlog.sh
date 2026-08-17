#!/usr/bin/env bash
# devlog.sh — 自动聚合开发日志（git 近期提交 + TASK 状态 + 坑记录），不手填。
# 用法：
#   bash scripts/devlog.sh           # 输出到 stdout
#   bash scripts/devlog.sh --save    # 同时写 docs/devlog/DEVLOG-YYYY-MM-DD.md
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

SAVE=0
[[ "${1:-}" == "--save" ]] && SAVE=1

OUT=""
emit() { OUT+="$1"$'\n'; }

emit "# 开发日志 $(date -u +%Y-%m-%dT%H:%M:%SZ)"
emit ""
emit "## 近期提交 (git log --oneline -15)"
emit '```'
emit "$(git log --oneline -15 2>/dev/null || echo '(无 git 历史)')"
emit '```'
emit ""
emit "## 任务态 (tasks/TASK-*.md)"
if compgen -G 'tasks/TASK-*.md' >/dev/null; then
  for f in tasks/TASK-*.md; do
    title=$(grep -m1 '^# ' "$f" 2>/dev/null | sed 's/^# //')
    emit "- ${f##*/} :: ${title:-（无标题）}"
  done
else
  emit "- (暂无 TASK 文件)"
fi
emit ""
emit "## 坑记录统计 (docs/devlog/pitfalls/)"
if [[ -f docs/devlog/pitfalls/pitfalls.jsonl ]]; then
  emit "- 总条数: $(wc -l < docs/devlog/pitfalls/pitfalls.jsonl)"
  emit "- 按严重度:"
  while read -r line; do emit "    $line"; done < <(grep -o '"severity": "[a-z]*"' docs/devlog/pitfalls/pitfalls.jsonl | sort | uniq -c)
else
  emit "- (暂无坑记录)"
fi

printf '%s\n' "$OUT"
if [[ "$SAVE" -eq 1 ]]; then
  mkdir -p docs/devlog
  fn="docs/devlog/DEVLOG-$(date -u +%Y-%m-%d).md"
  printf '%s\n' "$OUT" > "$fn"
  echo "[devlog] 已保存 -> $fn"
fi
