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
_UPDATED_AT = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)


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
            "body": "计算机科学与技术本科，主修分布式系统、数据库与软件工程。",
        },
        {
            "heading": "工作经历",
            "body": (
                "曾负责预约与协作类系统的后端架构，落地过插槽快照、实时刷新与幂等写入；"
                "也做过内容问答与检索相关功能。偏好先设计后编码，重视可观测与可演进。"
            ),
        },
        {
            "heading": "技术栈",
            "body": (
                "Python / FastAPI、PostgreSQL、Redis、TypeScript、React；熟悉 RAG 与人格层问答。"
            ),
        },
    ]
    resume_chunks = _chunk(
        "简历",
        [
            "我叫[姓名已脱敏]，[学校已脱敏]（广州 · 公办本科）计算机科学与技术专业"
            "（国家一流专业建设点）2026 届本科毕业生，中共党员，专业排名 3/153，GPA 3.38/4.0。",
            "我在泰益智医疗科技（广州）有限公司实习 7 个月，岗位 AI 全栈开发工程师 / "
            "技术负责人，主导智能睡眠监测台灯（Sleep AIoT）从 IoT 原型升级为以 LLM "
            "Agent 为核心的 AI Native 平台；落地 5 微服务 + 9 层 AI 能力矩阵，"
            "84 例工程评测 100% 通过、审批绕过率 0%。",
            "我的毕业设计是《基于大模型 RAG 的荔枝智能问答平台设计与实现》"
            "（2026 届优秀毕业设计，得分 90.4）。",
            "技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React；"
            "熟悉 RAG 与人格层问答、受约束的 AI Agent 编排，用过 Kafka / Flink / ClickHouse 数据平台。",
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
            "(pgvector) + Redis + React + DeepSeek + BGE-M3。"
        ),
    }
    projects_sleep: dict[str, object] = {
        "heading": "睡眠分析（sleep202603_an）",
        "body": "一个睡眠数据可视化与分析原型，负责数据采集管道与前端看板。",
    }
    projects_litchi: dict[str, object] = {
        "heading": "荔枝问答平台（litchi，毕设）",
        "body": (
            "2026 届优秀毕业设计（90.4 分）：基于大模型 RAG 的荔枝智能问答平台，"
            "一人独立完成 8 个模块（Spring Boot 3.2 后端 / Vue3 前端 / YOLOv8 诊断 / "
            "数据平台 / 可观测 / Helm 部署 / 评测 / 语料）；四段受控 Agent + Milvus/Neo4j "
            "双路检索 + 本地 Ollama 小模型，60 条评测集门禁。"
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
                    "up→down→up 可逆）+ PostgreSQL 16 + pgvector + Redis 7 + React 19/Vite 8 "
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
                    "防次优改写丢证据；预约/写入/管理端点绝不注册为模型工具。"
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
                "sleep202603_an 是睡眠数据可视化与分析原型，负责采集管道与前端看板。",
            ],
        ),
        *_chunk(
            "litchi",
            [
                (
                    "litchi 荔枝问答平台是我的 2026 届优秀毕业设计（90.4 分）：《基于大模型 RAG 的"
                    "荔枝智能问答平台设计与实现》，一人独立完成 8 个模块（Spring Boot 3.2 后端 / "
                    "Vue3 前端 / YOLOv8 诊断服务 / 数据平台 / 可观测 / Helm 部署 / 评测 / 语料）。"
                ),
                (
                    "litchi 技术要点：Planner/Guard/Executor/Synthesizer 四段受控 Agent"
                    "（AgentService.java 实现），Milvus 哈希向量 + Neo4j 图谱双路检索，本地 Ollama "
                    "qwen2.5:0.5b（无 GPU 笔记本可演示）；诚实局限：并发压测 200 并发仅 19% 达标、"
                    "混合检索 BM25+RRF 未完成、数据平台为可部署模板未生产验证。"
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
                "你最擅长的技术方向是什么？",
                "你做过哪些高并发相关的系统？",
                "你为什么强调先设计后编码？",
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
                "sleep202603_an 解决了什么问题？",
                "荔枝问答平台（litchi）这个项目是做什么的？",
                "你在项目里最得意的一个设计决策是什么？",
            ],
        ),
    }


PAGES = build_pages()


def build_resume_facts_card() -> str:
    """Hard, always-injected resume facts for the digital-twin voice.

    These are verbatim anchors distilled from the ``resume`` page chunks
    (R0–R4 + the R5 digital-twin chunk added by TASK-AIQA-GROUNDING-001 + the
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
        "- 学历：[学校已脱敏]（广州 · 公办本科）计算机科学与技术专业"
        "（国家一流专业建设点），2026 届本科，中共党员，专业排名 3/153，GPA 3.38/4.0\n"
        "- 实习：泰益智医疗科技（广州）有限公司，7 个月，AI 全栈开发工程师 / 技术负责人，"
        "主导智能睡眠监测台灯（Sleep AIoT）从 IoT 原型升级为以 LLM Agent 为核心的 AI Native 平台\n"
        "- 工作经历：曾负责预约与协作类系统的后端架构，落地插槽快照、实时刷新与幂等写入；"
        "也做过内容问答与检索相关功能\n"
        "- 最骄傲的项目：AI 睡眠健康 Agent 平台——84 例工程评测 100% 通过、工具选择准确率 100%、"
        "审批绕过率 0%、10 例 Prompt 注入 0 越权写、4 例隐私测试 0 泄露\n"
        "- 毕业设计：2026 届优秀毕业设计（得分 90.4）《基于大模型 RAG 的荔枝智能问答平台设计与实现》\n"
        "- 技术方向：后端与平台方向工程师，关注高并发服务、数据建模与开发者体验\n"
        "- 工程方法论：我偏好先设计后编码\n"
        "- 最看重的工程品质：重视可观测性、可演进性与契约测试\n"
        "- 技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React\n"
        "- 熟悉的 AI 技术：RAG 与人格层问答、受策略/审批/持久化约束的 AI Agent 编排；"
        "Kafka / Flink / ClickHouse 数据平台\n"
        "- 求职意向：AI 全栈开发工程师，意向深圳市南山区\n"
        "- 站点本质：我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约"
    )
