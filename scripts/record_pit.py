"""Record a pitfall (坑) in a structured, machine-readable + human-readable form.

Part of the harness "留痕" loop (TASK-HARNESS-001). The machine records; the AI reviews
and proposes Skill extraction; the human decides. Entries are appended to:
  - docs/devlog/pitfalls/pitfalls.jsonl   (one JSON object per line, machine-friendly)
  - docs/devlog/pitfalls/pitfalls.md      (human-readable, newest appended at bottom)

Usage:
  python scripts/record_pit.py \
    --source "verify.sh" --severity high \
    --symptom "..." --root-cause "..." --fix "..." --avoidance "..." \
    --context "stage=pytest; commit=abcd123"

Only --symptom is required; other fields default to "（待分析）" so an automatic failure
recording can be enriched later during AI review.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PIT_DIR = Path(__file__).resolve().parent.parent / "docs" / "devlog" / "pitfalls"
JSONL = PIT_DIR / "pitfalls.jsonl"
MD = PIT_DIR / "pitfalls.md"

SEVERITIES = {"low", "med", "high"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a harness pitfall.")
    parser.add_argument("--symptom", required=True)
    parser.add_argument("--root-cause", default="（待分析）")
    parser.add_argument("--fix", default="（待分析）")
    parser.add_argument("--avoidance", default="（待分析）")
    parser.add_argument("--severity", choices=sorted(SEVERITIES), default="med")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--context", default="")
    parser.add_argument("--auto", action="store_true", help="标记为由脚本自动记录、待 AI 复盘")
    parser.add_argument(
        "--skill-candidate",
        action="store_true",
        help="AI 复盘后提议：此坑值得提炼为 Skill（最终由用户拍板）",
    )
    parser.add_argument(
        "--skill-name",
        default=None,
        help="提议的 Skill 名称（与 --skill-candidate 配合）",
    )
    args = parser.parse_args()

    PIT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    record = {
        "timestamp": ts,
        "severity": args.severity,
        "source": args.source,
        "auto": args.auto,
        "symptom": args.symptom,
        "root_cause": args.root_cause,
        "fix": args.fix,
        "avoidance": args.avoidance,
        "context": args.context,
        "skill_candidate": args.skill_candidate,  # AI 复盘提议，最终由用户拍板
        "skill_name": args.skill_name,
    }

    with JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    header = (
        f"## {ts} · {args.severity.upper()} · {args.source}{' · AUTO' if args.auto else ''}\n\n"
    )
    body = (
        f"- **现象**：{args.symptom}\n"
        f"- **根因**：{args.root_cause}\n"
        f"- **修复**：{args.fix}\n"
        f"- **规避**：{args.avoidance}\n"
        f"- **上下文**：{args.context}\n"
        f"- **Skill 候选**：{'是 → ' + (args.skill_name or '（待命名）') if args.skill_candidate else '否（待复盘拍板）'}\n\n"
        "---\n\n"
    )
    if not MD.exists():
        MD.write_text(
            "# Harness 坑记录（Pitfalls）\n\n"
            "> 由 `scripts/record_pit.py` 自动追加；机器如实记录，AI 复盘提建议，用户拍板是否提炼为 Skill。\n"
            "> 新条目追加在文末。\n\n---\n\n",
            encoding="utf-8",
        )
    with MD.open("a", encoding="utf-8") as fh:
        fh.write(header + body)

    print(f"[record_pit] 已记录 -> {MD.relative_to(PIT_DIR.parent.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
