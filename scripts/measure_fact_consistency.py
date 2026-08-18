#!/usr/bin/env python3
"""Fact-consistency measurement harness (Task ① scaffold).

Sends each question in the fact bank to ``POST /answers:stream``, captures the
full streamed answer text + offtopic/grounded markers, and dumps
``scripts/fact_consistency_results.json`` for human scoring against
``docs/fact-consistency/fact-bank.md`` + ``rubric.md``.

This script is READ-ONLY against the running service and the repo: it only
emits HTTP requests and writes the local result JSON. It never mutates code,
config, or runtime state.

Usage (WSL, with uvicorn already running on 127.0.0.1:8000):
    python3 scripts/measure_fact_consistency.py
    python3 scripts/measure_fact_consistency.py --only 11,12,17,18
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

HOST = os.environ.get("JIANLI_AIQA_HOST", "127.0.0.1")
PORT = os.environ.get("JIANLI_AIQA_PORT", "8000")
ENDPOINT = f"http://{HOST}:{PORT}/answers:stream"
TIMEOUT = float(os.environ.get("JIANLI_AIQA_TIMEOUT", "60"))

# Scope note: retrieval is page-isolated. Resume facts live under page_key=resume;
# jianli project facts live under page_key=projects + project_key=jianli.
# Ground truth for every item is in docs/fact-consistency/fact-bank.md.
QUESTION_BANK = [
    # ---- A 组 · 简历域 ----
    {"id": "FQ-01", "q": "你主要是什么技术方向的工程师？", "page_key": "resume", "project_key": None},
    {"id": "FQ-02", "q": "你平时重点关注哪些技术领域？", "page_key": "resume", "project_key": None},
    {"id": "FQ-03", "q": "你做过哪些类型的系统后端架构？", "page_key": "resume", "project_key": None},
    {"id": "FQ-04", "q": "你在预约系统里落地过哪些关键设计？", "page_key": "resume", "project_key": None},
    {"id": "FQ-05", "q": "你的工程方法论是什么？", "page_key": "resume", "project_key": None},
    {"id": "FQ-06", "q": "你做工程时特别看重什么？", "page_key": "resume", "project_key": None},
    {"id": "FQ-07", "q": "你的主要技术栈有哪些？", "page_key": "resume", "project_key": None},
    {"id": "FQ-08", "q": "你熟悉哪些 AI 问答相关技术？", "page_key": "resume", "project_key": None},
    {"id": "FQ-09", "q": "除了后端架构，你还做过什么方向的功能？", "page_key": "resume", "project_key": None},
    {"id": "FQ-10", "q": "你做的这个站点本质是用来做什么的？", "page_key": "resume", "project_key": None},
    # ---- B 组 · jianli 项目域 ----
    {"id": "FQ-11", "q": "jianli 这个项目是做什么的？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-12", "q": "jianli 处理越界或无依据问题的原则是什么？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-13", "q": "jianli 的后端技术栈是什么？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-14", "q": "jianli 用什么模型和 embedding？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-15", "q": "jianli 的检索是怎么做的？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-16", "q": "jianli 把 embedding 换成 BGE-M3 后检索质量有什么变化？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-17", "q": "jianli 怎么判断一个问题该拒答？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-18", "q": "jianli 的拒答率现在是多少？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-19", "q": "jianli 的 Agent 能调用哪些工具？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-20", "q": "jianli 的 Agent 是怎么决定要不要检索的？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-21", "q": "jianli 用什么来量化检索质量？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-22", "q": "jianli 的检索评测达到了什么水平？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-23", "q": "jianli 的预约业务闭环有哪些关键保障？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-24", "q": "jianli 的集成测试情况如何？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-25", "q": "jianli 的 embedding 经历过什么演进？", "page_key": "projects", "project_key": "jianli"},
    {"id": "FQ-26", "q": "jianli 开发中有过什么值得记录的坑？", "page_key": "projects", "project_key": "jianli"},
    # ---- C 组 · Litchi 毕设域（TASK-AIQA-KB-EXPAND-014 新增）----
    {"id": "FQ-27", "q": "litchi 毕设用了什么技术栈？", "page_key": "projects", "project_key": "litchi"},
    {"id": "FQ-28", "q": "litchi 的四段受控 Agent 是怎么实现的？", "page_key": "projects", "project_key": "litchi"},
    {"id": "FQ-29", "q": "litchi 的 LLM 和向量是怎么选的？", "page_key": "projects", "project_key": "litchi"},
    {"id": "FQ-30", "q": "litchi 的并发压测结果如何？", "page_key": "projects", "project_key": "litchi"},
    # ---- D 组 · sleep 泰益智域 ----
    {"id": "FQ-31", "q": "泰益智的 84 例评测怎么分类？", "page_key": "projects", "project_key": "sleep202603_an"},
    {"id": "FQ-32", "q": "泰益智 51 条重复的根因是什么？", "page_key": "projects", "project_key": "sleep202603_an"},
    {"id": "FQ-33", "q": "泰益智同一套代码出了几个端？", "page_key": "projects", "project_key": "sleep202603_an"},
    # ---- E 组 · 行为/动机/竞赛（interview-story.md）----
    {"id": "FQ-34", "q": "你在泰益智是怎么带人的？", "page_key": "resume", "project_key": None},
    {"id": "FQ-35", "q": "你工程上最大的教训是什么？", "page_key": "resume", "project_key": None},
    {"id": "FQ-36", "q": "你的求职动机和职业规划是什么？", "page_key": "resume", "project_key": None},
    {"id": "FQ-37", "q": "慧眼识蚁项目是做什么的？", "page_key": "projects", "project_key": None},
    {"id": "FQ-38", "q": "慧眼识蚁做到了什么程度？", "page_key": "projects", "project_key": None},
]


def _post_stream(question: str, page_key: str, project_key: str | None) -> dict:
    """POST one question, return {answer_text, grounded, offtopic, model, usage, error}."""
    body = {"question": question, "page_key": page_key}
    if project_key:
        body["project_key"] = project_key
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    answer_text = []
    result = {"grounded": None, "offtopic": None, "model": None, "usage": None, "error": None}
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    # SSE frames look like: "id: 1\nevent: answer.delta\ndata: {...}\n\n"
    # The block may start with "id:" (not "event:"), so don't require event-prefix.
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event = None
        data_parts: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_parts.append(line[len("data:"):].strip())
        if not event or not data_parts:
            continue
        payload_raw = "\n".join(data_parts)
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            continue
        if event == "answer.delta":
            answer_text.append(payload.get("text", ""))
        elif event == "answer.completed":
            result["grounded"] = payload.get("grounded")
            result["offtopic"] = payload.get("offtopic")
            result["model"] = payload.get("model")
            result["usage"] = payload.get("usage")
        elif event == "answer.error":
            result["error"] = payload
    result["answer_text"] = "".join(answer_text)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure jianli fact-consistency (Q+A transcripts).")
    ap.add_argument("--only", help="Comma-separated FQ ids to run, e.g. 11,12,17,18")
    args = ap.parse_args()

    bank = QUESTION_BANK
    if args.only:
        want = {f"FQ-{x.strip().zfill(2)}" for x in args.only.split(",") if x.strip()}
        bank = [b for b in bank if b["id"] in want]
        if not bank:
            print(f"[ERR] no matching FQ ids in --only={args.only}", file=sys.stderr)
            return 2

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fact_consistency_results.json")
    records = []
    print(f"== measure_fact_consistency | endpoint={ENDPOINT} | {len(bank)} questions ==\n")
    for item in bank:
        scope = item["page_key"] + (f"/{item['project_key']}" if item["project_key"] else "")
        res = _post_stream(item["q"], item["page_key"], item["project_key"])
        status = "ERR" if res.get("error") else ("OFFTOPIC" if res.get("offtopic") else "OK")
        ans_preview = (res.get("answer_text") or "").replace("\n", " ")[:60]
        print(f"[{item['id']}] {scope:16} {status:8} | {ans_preview}")
        records.append({
            "id": item["id"],
            "question": item["q"],
            "page_key": item["page_key"],
            "project_key": item["project_key"],
            "answer_text": res.get("answer_text", ""),
            "grounded": res.get("grounded"),
            "offtopic": res.get("offtopic"),
            "model": res.get("model"),
            "usage": res.get("usage"),
            "error": res.get("error"),
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT,
        "question_count": len(records),
        "records": records,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n[OK] wrote {len(records)} transcripts -> {out_path}")
    print("Next: score each answer against docs/fact-consistency/fact-bank.md per rubric.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
