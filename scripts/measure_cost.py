#!/usr/bin/env python3
"""Measure real token usage + cost of jianli streamAnswer (task ②).

Hits the running API at http://127.0.0.1:8000/answers:stream and parses the
`answer.completed` SSE frame's `usage` payload.

Retrieval is page-scoped (retrieval.py `_corpus` only searches PAGES[page_key]),
so each question must carry the scope where its answer lives. A project-design
question (e.g. "怎么保证不编造经历") lives under page_key="projects" +
project_key="jianli"; asking it with page_key="resume" returns 0 hits -> refusal.

PREREQUISITES (else usage comes back null and you get no numbers):
  1. API server running:  uvicorn app.main:app --port 8000  (in apps/api)
  2. A REAL LLM key configured (OpenAI-compatible, e.g. SiliconFlow DeepSeek-V4-Flash).
     If JIANLI_LLM_* env vars are absent the Stub gateway is used and emits
     usage=None  ->  this script prints a warning and cannot compute cost.
  3. Embedding gateway = BGE-M3 (SiliconFlow). Input is ¥0/1K (confirmed by 用户).

Prices (confirmed 2026-08-16 from provider screenshots):
  LLM (DeepSeek-V4-Flash): input  ¥0.001 / 1K tokens, output ¥0.002 / 1K tokens
  Embedding (BGE-M3):       input  ¥0.000 / 1K tokens  (free)

Run:
  python scripts/measure_cost.py
  python scripts/measure_cost.py "你做过哪些高并发系统"            # resume scope
  python scripts/measure_cost.py "scope:projects:jianli:jianli 是怎么保证不编造经历的？"
"""
from __future__ import annotations

import json
import sys
import urllib.request

URL = "http://127.0.0.1:8000/answers:stream"
LLM_INPUT_PRICE_PER_1K = 0.001   # DeepSeek-V4-Flash input
LLM_OUTPUT_PRICE_PER_1K = 0.002  # DeepSeek-V4-Flash output
EMBED_PRICE_PER_1K = 0.0         # BGE-M3 input is free

# Each default question carries its own scope. Retrieval is page-scoped, so a
# project-design question must use page_key="projects" + project_key="jianli"
# to find the anti-fabrication / RAG content (it lives under the jianli page,
# NOT under "resume").
DEFAULT_QUESTIONS: list[tuple[str, str, str | None]] = [
    ("介绍一下 jianli 这个项目的技术选型。", "resume", None),
    ("jianli 的检索是怎么做的？", "resume", None),
    ("你做过哪些高并发相关的系统？", "resume", None),
    ("jianli 是怎么保证不编造经历的？", "projects", "jianli"),
    ("jianli 的拒答门槛是怎么设计的？", "projects", "jianli"),
]


def parse_arg(arg: str) -> tuple[str, str, str | None]:
    """Parse a CLI question.

    Plain text                      -> resume scope.
    `scope:<page_key>[:<project_key>]:<question>` -> explicit scope.
    """

    if arg.startswith("scope:"):
        rest = arg[len("scope:"):]
        head, sep, q = rest.partition(":")
        if not sep:
            return arg, "resume", None
        if ":" in head:
            page_key, _, project_key = head.partition(":")
        else:
            page_key, project_key = head, None
        return q, page_key, (project_key or None)
    return arg, "resume", None


def parse_sse_usage(body: str) -> dict | None:
    """Return the `usage` dict from the first `answer.completed` frame."""

    for block in body.split("\n\n"):
        event = data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
        if event == "answer.completed" and data:
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            return payload.get("usage")
    return None


def measure(question: str, page_key: str, project_key: str | None) -> dict:
    body_dict: dict[str, object] = {"question": question, "page_key": page_key}
    if project_key:
        body_dict["project_key"] = project_key
    req = urllib.request.Request(
        URL,
        data=json.dumps(body_dict).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    usage = parse_sse_usage(body)
    return {
        "question": question,
        "page_key": page_key,
        "project_key": project_key,
        "usage": usage,
        "raw_tail": body.strip().split("\n\n")[-1][:200],
    }


def main() -> int:
    if len(sys.argv) > 1:
        items = [parse_arg(a) for a in sys.argv[1:]]
    else:
        items = DEFAULT_QUESTIONS
    print(
        f"== measure_cost.py | LLM in ¥{LLM_INPUT_PRICE_PER_1K}/1K out "
        f"¥{LLM_OUTPUT_PRICE_PER_1K}/1K | embed ¥{EMBED_PRICE_PER_1K}/1K =="
    )
    tot_in = tot_out = 0
    for q, pk, pkp in items:
        r = measure(q, pk, pkp)
        u = r["usage"]
        scope = f"[{pk}/{pkp}]" if pkp else f"[{pk}]"
        if not u:
            print(
                f"[WARN] usage=None (Stub gateway / no real LLM key / off-topic?)  "
                f"{scope} q={q!r}"
            )
            print(f"       last frame: {r['raw_tail']}")
            continue
        pin = u.get("prompt_tokens", 0)
        pout = u.get("completion_tokens", 0)
        cost = pin / 1000 * LLM_INPUT_PRICE_PER_1K + pout / 1000 * LLM_OUTPUT_PRICE_PER_1K
        tot_in += pin
        tot_out += pout
        print(f"prompt={pin:5d} completion={pout:5d}  cost=¥{cost:.5f}  {scope} | {q}")
    grand = tot_in / 1000 * LLM_INPUT_PRICE_PER_1K + tot_out / 1000 * LLM_OUTPUT_PRICE_PER_1K
    print(f"== totals: prompt={tot_in} completion={tot_out}  grand_cost=¥{grand:.5f} ==")
    if tot_in + tot_out == 0:
        print("[STOP] No real usage captured. Set JIANLI_LLM_* and rerun.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
