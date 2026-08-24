"""Static public page knowledge registry (M6 round 1).

This is the *only* place page content lives in round 1. It serves two contract
endpoints (``getPageContent``, ``listRecommendedQuestions``) and is the grounding
corpus for the RAG answer (``streamAnswer``). It deliberately requires **no database
table** so round 1 ships with zero migrations.

Handoff note for Codex: replace ``build_pages()`` with a DB-backed loader once
``knowledge_documents`` / ``knowledge_index_versions`` land (TASK-M6-DB, round 3).
Keep the ``PageContentData`` shape so retrieval, persona and the router need no change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# Single, explicit updated_at so the public API is stable and cacheable.
_UPDATED_AT = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class PageChunk:
    """One retrievable fragment. ``doc`` is a human label (never a storage_key)."""

    doc: str
    fragment: int
    text: str


@dataclass(slots=True)
class PageContentData:
    page_key: str
    title: str
    sections: list[dict[str, object]]
    updated_at: datetime
    chunks: list[PageChunk]
    recommendations: list[str]


def _chunk(doc: str, lines: list[str]) -> list[PageChunk]:
    return [PageChunk(doc=doc, fragment=i, text=text) for i, text in enumerate(lines)]


def build_pages() -> dict[str, PageContentData]:
    """Construct the in-memory page registry (placeholder content, ready to swap)."""

    resume_sections: list[dict[str, object]] = [
        {
            "heading": "简介",
            "body": (
                "我是一名后端与平台方向的工程师，关注高并发服务、数据建模与开发者体验。"
                "这个站点是我本人的数字分身，用来回答关于我经历的问题并承接面试预约。"
            ),
        },
        {
            "heading": "教育背景",
            "body": (
                "[学校已脱敏]（广州 · 公办本科）计算机科学与技术专业，2026 届本科，"
                "中共党员，专业排名 3/153（前 2%）。"
            ),
        },
        {
            "heading": "工作经历",
            "body": (
                "在泰益智医疗科技主导睡眠健康 AI Agent 平台（FastAPI + LangGraph + K8s），"
                "把 Agent 长任务失序、循环失控压到 RC 阶段吞吐 +393.9%、P95 延迟 1.35s→229ms；"
                "独立开发荔枝农技 AI Agent 协同平台（毕设，90.4 分）与本项目 jianli"
                "（AI Agent 问答与面试预约系统）。偏好先设计后编码，重视可观测与可演进。"
            ),
        },
        {
            "heading": "技术栈",
            "body": (
                "Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React；"
                "K8s / ArgoCD / LangGraph；熟悉 RAG 与人格层问答、受约束的 AI Agent 编排。"
            ),
        },
    ]
    resume_chunks = _chunk(
        "简历",
        [
            "我叫[姓名已脱敏]，[学校已脱敏]（广州 · 公办本科）计算机科学与技术专业"
            "2026 届本科毕业生，中共党员，专业排名 3/153（前 2%）。",
            "我在泰益智医疗科技（广州）有限公司实习（2025.12—2026.06），岗位 AI 全栈开发工程师，"
            "主导睡眠健康 AI Agent 平台（FastAPI + LangGraph + K8s）：解决 Agent 长任务失序、"
            "循环失控问题，RC 阶段压测吞吐提升 393.9%（近 4 倍），P95 延迟由 1.35s 压降至 229ms；"
            "封装 6 个受治理工具及 15 个 Agent REST API，基于 pgvector RAG、ClickHouse 特征服务"
            "与 Tool Calling 打通「数据检索—模型推理—设备执行—结果回传」业务闭环。",
            "我建立 L0—L4 风险治理与 Human-in-the-loop 高风险审批机制，落地 Prompt Injection 检测、"
            "工具白名单、参数边界、租户隔离及设备二次确认；建设覆盖正确性、引用、拒答、工具选择、"
            "越权、健康合规、延迟和成本的 8 维评测基线（84 条回归用例 + 120 条红队用例），"
            "设备写操作恶意绕过 0 次。",
            "我的毕业设计是《基于大模型 RAG 的荔枝智能问答平台设计与实现》"
            "（2026 届优秀毕业设计，得分 90.4），独立开发荔枝农技 AI Agent 协同平台"
            "（Spring Boot 3.2 + Vue3 + TypeScript，22 个业务页面，Docker Compose 编排 9 服务并"
            " Helm 化 K8s 部署）；基于 Milvus + Neo4j 双路 RAG 与 YOLOv8 三级诊断，"
            "病害识别准确率由 20% 提升至 93.75%，Chat P95 由 5s 降至 124ms"
            "（约 1/50），50 并发成功率 100%。",
            "技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、K8s / ArgoCD /"
            "LangGraph；熟悉 RAG 与人格层问答、受约束的 AI Agent 编排（工具白名单 + RBAC + 预算熔断"
            "+ HITL 审批），用过 Kafka / Flink / ClickHouse 数据平台。",
            "我偏好先设计后编码，重视可观测性、可演进性与契约测试。",
            "我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约。",
            "我曾负责预约与协作类系统的后端架构，落地过插槽快照、实时刷新与幂等写入；"
            "也做过内容问答与检索相关功能。偏好先设计后编码，重视可观测与可演进。",
        ],
    )

    projects_jianli: dict[str, object] = {
        "heading": "个人 AI 问答网站（jianli）",
        "body": (
            "面向个人求职的作品集站点：公开 RAG 问答（基于本人资料、越界拒答、决策链 "
            "SSE 可见）、第一人称人格层、动态面试表实时刷新、对话式面试预约代理。核心"
            "约束是面试场景真实性优先，绝不编造经历。技术栈 FastAPI + PostgreSQL"
            "(pgvector) + Redis + React 19 + DeepSeek + BGE-M3。"
        ),
    }
    projects_sleep: dict[str, object] = {
        "heading": "睡眠分析（sleep202603_an）",
        "body": "泰益智睡眠健康 AI Agent 平台：FastAPI + LangGraph + K8s，"
        "RC 阶段吞吐 +393.9%、P95 1.35s→229ms。",
    }
    projects_litchi: dict[str, object] = {
        "heading": "荔枝问答平台（litchi，毕设）",
        "body": (
            "2026 届优秀毕业设计（90.4 分）：基于大模型 RAG 的荔枝智能问答平台，"
            "一人独立完成（Spring Boot 3.2 后端 / Vue3 前端 / YOLOv8 诊断 / 数据平台 / "
            "可观测 / Helm 部署 / 评测 / 语料）；Milvus + Neo4j 双路检索 + 本地 Ollama 小模型，"
            "22 个业务页面，50 并发成功率 100%。"
        ),
    }
    projects_sections: list[dict[str, object]] = [projects_jianli, projects_sleep, projects_litchi]
    projects_chunks = [
        *_chunk(
            "jianli",
            [
                (
                    "jianli 是个人 AI 问答网站（本项目自身）：把简历问答、项目追问与面试"
                    "预约做成一条可验证的产品链。核心约束是面试场景真实性优先——越界或无"
                    "依据的问题一律拒答，绝不编造经历。"
                ),
                (
                    "jianli 技术栈：FastAPI + SQLAlchemy + Alembic（0001-0007 迁移共 15 张表，"
                    "up→down→up 可逆）+ PostgreSQL 16 + pgvector + Redis 7 + React 19/Vite "
                    "+ TypeScript；LLM 用 DeepSeek V4 Flash（chat），embedding 用硅基流动 "
                    "BGE-M3（1024 维）。"
                ),
                (
                    "jianli 混合检索：向量 top10 + BM25 top10 经 RRF 融合取 top6 作为引用；"
                    "CJK 单字 BM25 索引对 embedding 退化鲁棒，语义向量优势须在纯向量层量化"
                    "（BGE-M3 avg-rank 1.3 vs 本地哈希 1.8）。"
                ),
                (
                    "jianli 越界拒答双层门槛：① 知识库向量相关性阈值 0.47（数据校准：拒答 "
                    "top1 max 0.464 / 命中 min 0.463，接受边缘取舍）；② 静态检索加 CJK 停用词"
                    "过滤，功能字不参与重叠计数。拒答率从 0% 提升到 100%（评测 REJECT 10/10）。"
                ),
                (
                    "jianli Agent 工具化：search_knowledge 注册为白名单只读工具，模型通过 "
                    "function calling 自主决策是否检索并生成检索词（tool_choice=auto）；决策"
                    "链经 SSE answer.tool_calls 帧可观测；双路召回（模型 query + 原问题对照）"
                    "防次优改写丢证据。预约域开放 list_my_appointments / cancel_appointment / "
                    "reschedule_appointment 三个 RBAC 守卫的预约管理工具（面试官仅本人、"
                    "owner_admin 可管理全部含他人），MAX_STEPS=4 防死循环，5 种异常优雅映射"
                    "为结构化 outcome，28KB 测试覆盖全路径。"
                ),
                (
                    "jianli 评测闭环：tests/aiqa/test_rag_eval.py 基于真实语料（10 篇上传→"
                    "分块→混合检索→streamAnswer 全链路）量化检索质量：LITERAL 8/8、REJECT "
                    "10/10、语义/极端改写用例 6/6；评测先暴露缺陷（拒答率 0%）再驱动修复闭环。"
                ),
                (
                    "jianli 业务闭环：Slot 快照与并发锁、3 分钟预览不预占、原子创建、字段级 "
                    "AES-256-GCM 加密、Outbox 通知、审计日志、SSE 恢复契约；真实 PG16 + Redis7 "
                    "集成测试 53+ passed，ruff/mypy 门禁全绿。"
                ),
                (
                    "jianli 真实演进记录：embedding 从本地哈希换成 BGE-M3（哈希无语义）；"
                    "Agent 模型自主决策上线后评测一度 8/8→6/8，最终根因是 greeting 判定里 "
                    "'hi' 子串误匹配 'litchi'（改整词匹配修复）——诚实记录踩坑过程，不粉饰。"
                ),
            ],
        ),
        *_chunk(
            "sleep202603_an",
            [
                "sleep202603_an（泰益智睡眠健康 AI Agent 平台）是我实习主导的 AI 睡眠健康 "
                "Agent 平台（FastAPI + LangGraph + K8s）：解决 Agent 长任务失序、循环失控问题，"
                "RC 阶段压测吞吐提升 393.9%（近 4 倍），P95 延迟由 1.35s 压降至 229ms；"
                "封装 6 个受治理工具及 15 个 Agent REST API，基于 pgvector RAG、ClickHouse "
                "特征服务与 Tool Calling 打通「数据检索—模型推理—设备执行—结果回传」业务闭环。",
                "sleep202603_an 安全与质量：建立 L0—L4 风险治理与 Human-in-the-loop 高风险审批，"
                "落地 Prompt Injection 检测、工具白名单、参数边界、租户隔离及设备二次确认；"
                "8 维评测基线（84 条回归用例 + 120 条红队用例），设备写操作恶意绕过 0 次；"
                "全栈贯通 Taro/React 小程序、React 运营台、NestJS 业务后端、FastAPI Agent 服务"
                "及 K8s/ArgoCD 部署链路。",
            ],
        ),
        *_chunk(
            "litchi",
            [
                (
                    "litchi 荔枝问答平台是我的 2026 届优秀毕业设计（90.4 分）：《基于大模型 RAG 的"
                    "荔枝智能问答平台设计与实现》，一人独立完成（Spring Boot 3.2 后端 / "
                    "Vue3 前端 / YOLOv8 诊断服务 / 数据平台 / 可观测 / Helm 部署 / 评测 / 语料），"
                    "22 个业务页面，Docker Compose 编排 9 服务并 Helm 化 K8s 部署。"
                ),
                (
                    "litchi 技术要点：受控 Agent（5 类 Tool、7 状态、4 步边界、写操作强审批），"
                    "Milvus + Neo4j 双路 RAG（6 类文档摄入 / 480 字符分块 / 1024 维向量）与 "
                    "YOLOv8 三级诊断，病害识别准确率由 20% 提升至 93.75%；Chat P95 由 5s 降至 "
                    "124ms（约 1/50），50 并发成功率 100%；本地 Ollama qwen2.5:0.5b"
                    "（无 GPU 笔记本可演示）。"
                ),
                (
                    "litchi 论文版（毕设论文真源，90.4 分）：系统为「荔枝智能问答与协同诊断平台」，"
                    "五层架构（Vue3 表现层 / Nginx+Spring Boot 接入层 / Spring Boot 3.2 业务层 / "
                    "AI 服务层 / MySQL+Neo4j+Milvus 数据层，Docker Compose 10 服务）；RAG 链路 = "
                    "查询→向量+图谱并行检索→候选筛选→Qwen2.5:0.5b 生成→证据约束与降级"
                    "（分块 480/120）；病害识别 = YOLOv8 + 标签映射 + 三级降级"
                    "（yolo→dataset-vision→"
                    "demo-rule）；四大亮点 = 双增强架构 / 三级降级 / 多角色闭环 / 可进化评测；"
                    "验证报告 = 30 分钟稳定性 119 轮全成功 + 50 并发问答全成功。"
                ),
            ],
        ),
    ]

    return {
        "resume": PageContentData(
            page_key="resume",
            title="个人简历",
            sections=resume_sections,
            updated_at=_UPDATED_AT,
            chunks=resume_chunks,
            recommendations=[
                "你的实习做了哪些 AI Agent 平台相关的工作？",
                "你最骄傲的一个性能优化结果是什么？",
                "你独立做的毕业设计是什么？",
            ],
        ),
        "projects": PageContentData(
            page_key="projects",
            title="项目作品",
            sections=projects_sections,
            updated_at=_UPDATED_AT,
            chunks=projects_chunks,
            recommendations=[
                "介绍一下 jianli 这个项目的技术选型。",
                "sleep202603_an 的吞吐和延迟优化做到了什么程度？",
                "荔枝问答平台（litchi）这个项目是做什么的？",
                "你在项目里最得意的一个设计决策是什么？",
            ],
        ),
    }


PAGES = build_pages()


def build_resume_facts_card() -> str:
    """Hard, always-injected resume facts for the digital-twin voice.

    These are verbatim anchors distilled from the ``resume`` page chunks
    (R0-R6 + the R5 digital-twin chunk added by TASK-AIQA-GROUNDING-001 + the
    R6 工作经历 chunk added by TASK-AIQA-FACTCOVERAGE-013).
    They are injected into the *system* prompt (higher weight than the
    retrieved 【已知资料】 block) and pinned with a "use verbatim" constraint,
    so open-ended questions (methodology / what-you-value / other-directions)
    cannot be answered with generic paraphrases that drift from the source.

    MUST stay in sync with ``resume_chunks`` and ``docs/fact-consistency/fact-bank.md``.
    """

    return (
        "【硬性事实卡·简历】(以下事实优先级最高，回答对应主题时必须逐字使用，"
        "不得自行归纳或替换)\n"
        "- 姓名：[姓名已脱敏]（我叫[姓名已脱敏]）\n"
        "- 学历：[学校已脱敏]（广州 · 公办本科）计算机科学与技术专业，"
        "2026 届本科，中共党员，专业排名 3/153（前 2%）\n"
        "- 实习：泰益智医疗科技（广州）有限公司（2025.12—2026.06），AI 全栈开发工程师，"
        "主导睡眠健康 AI Agent 平台（FastAPI + LangGraph + K8s）；RC 阶段压测吞吐提升 "
        "393.9%（近 4 倍），P95 延迟由 1.35s 压降至 229ms；封装 6 个受治理工具及 "
        "15 个 Agent REST API\n"
        "- 工作经历：曾负责预约与协作类系统的后端架构，落地插槽快照、实时刷新与幂等写入；"
        "也做过内容问答与检索相关功能\n"
        "- 最骄傲的项目：睡眠健康 AI Agent 平台——建立 L0—L4 风险治理与 Human-in-the-loop "
        "审批，8 维评测基线（84 条回归 + 120 条红队），设备写操作恶意绕过 0 次\n"
        "- 毕业设计：2026 届优秀毕业设计（得分 90.4）"
        "《基于大模型 RAG 的荔枝智能问答平台设计与实现》\n"
        "- 技术方向：后端与平台方向工程师，关注高并发服务、数据建模与开发者体验\n"
        "- 工程方法论：我偏好先设计后编码\n"
        "- 最看重的工程品质：重视可观测性、可演进性与契约测试\n"
        "- 技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、"
        "K8s / ArgoCD / LangGraph\n"
        "- 熟悉的 AI 技术：RAG 与人格层问答、受策略/审批/持久化约束的 AI Agent 编排；"
        "Kafka / Flink / ClickHouse 数据平台\n"
        "- 荣誉：2025 年国家励志奖学金、2024 年大创国家级立项（第一负责人）、"
        "2024 挑战杯 A 类赛事路演资格、2022—2026 校级奖学金、2026 年优秀毕业生\n"
        "- 求职意向：AI 全栈开发工程师，意向深圳市南山区\n"
        "- 站点本质：我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约"
    )
