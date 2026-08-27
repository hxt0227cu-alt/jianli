#!/usr/bin/env python3
"""Small provider-backed RRF-vs-Cross-Encoder component benchmark.

The emitted JSON contains only aggregate ranks and case IDs; queries and candidate text
stay in this local script and are never written to the public evaluation report.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from app.aiqa.reranker import CrossEncoderReranker


@dataclass(frozen=True)
class Case:
    case_id: str
    query: str
    expected_index: int
    candidates: list[str]


CASES = [
    Case(
        "agent-permission",
        "项目如何限制 Agent 工具权限？",
        2,
        [
            "Docker Compose 部署",
            "简历下载",
            "工具白名单、RBAC 与 BookingService 共同限制写操作",
            "邮件通知",
        ],
    ),
    Case(
        "rag-ranking",
        "RAG 的混合检索排序是什么？",
        3,
        [
            "会话 Cookie",
            "预约时段",
            "飞书通知",
            "向量与 BM25 召回经 RRF 融合，再由 Cross-Encoder 重排",
        ],
    ),
    Case(
        "observability",
        "如何观察 Agent 的调用质量？",
        1,
        [
            "PostgreSQL 迁移",
            "OpenTelemetry Trace、Prometheus 指标和 Grafana 看板",
            "简历 PDF",
            "邮件退信",
        ],
    ),
    Case(
        "evaluation",
        "如何避免模型改动导致质量回退？",
        2,
        ["静态页面", "Nginx TLS", "版本化评测集与 CI 门禁阻止回归", "预约日历"],
    ),
    Case(
        "grounding",
        "没有知识依据时系统怎么处理？",
        3,
        ["发送通知", "创建预约", "缓存推荐问题", "拒绝编造并返回资料未涵盖"],
    ),
]


def reciprocal_rank(rank: int) -> float:
    return 1 / (rank + 1)


def main() -> int:
    # A one-off benchmark may reuse the existing embedding-provider account without
    # changing production runtime wiring, which still requires dedicated RERANK_* config.
    base_url = os.environ.get("JIANLI_RERANK_BASE_URL") or os.environ.get(
        "JIANLI_LLM_EMBEDDING_BASE_URL"
    )
    api_key = os.environ.get("JIANLI_RERANK_API_KEY") or os.environ.get(
        "JIANLI_LLM_EMBEDDING_API_KEY"
    )
    model = os.environ.get("JIANLI_RERANK_MODEL")
    if not (base_url and api_key and model):
        raise SystemExit("set JIANLI_RERANK_BASE_URL/API_KEY/MODEL for a real provider run")
    gateway = CrossEncoderReranker(base_url, api_key, model, timeout=5)
    baseline_mrr = sum(reciprocal_rank(case.expected_index) for case in CASES) / len(CASES)
    reranked_rr = 0.0
    hit_at_1 = 0
    rows: list[dict[str, object]] = []
    for case in CASES:
        ranked = gateway.rerank(case.query, case.candidates, len(case.candidates))
        order = [result.index for result in ranked]
        rank = order.index(case.expected_index)
        reranked_rr += reciprocal_rank(rank)
        hit_at_1 += int(rank == 0)
        rows.append(
            {
                "case_id": case.case_id,
                "baseline_rank": case.expected_index + 1,
                "reranked_rank": rank + 1,
            }
        )
    report = {
        "evidence_level": "real_provider_component_benchmark",
        "provider_model": gateway.model_name,
        "cases": rows,
        "baseline_mrr": round(baseline_mrr, 4),
        "reranked_mrr": round(reranked_rr / len(CASES), 4),
        "reranked_hit_at_1": f"{hit_at_1}/{len(CASES)}",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
