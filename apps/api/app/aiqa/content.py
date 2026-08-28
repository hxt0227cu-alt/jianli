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
                "在泰益智医疗科技参与团队开发的睡眠健康 AI Agent 平台，主要负责云端后端、"
                "Agent Runtime 与 RAG；有界异步改造使 RC 任务接纳吞吐 +393.9%、"
                "P95 1347.73ms→228.85ms；"
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
            "我在泰益智医疗科技（广州）有限公司实习（2025.12—2026.06），岗位 AI 全栈开发工程师。"
            "这是团队开发的睡眠健康 AI Agent 平台；我主要负责云端后端、Agent Runtime 与 RAG，"
            "也参与遥测链路、多租户治理和联调排障。将同步任务改为有界异步接纳后，同一 RC 口径下"
            "接纳吞吐提升 393.9%，P95 由 1347.73ms 降至 228.85ms；这不是 LLM 推理耗时。",
            "我参与建立模型外的安全边界：固定 LangGraph DAG、工具白名单、租户上下文、HITL 与"
            "预算约束。确定性工程集 84/84，但健康合规子项为 71.43%，公开测试中的设备 ACK 为模拟；"
            "我与同事共同完成 120 条红队用例，96 条通过（80%），危险写工具调用为 0，"
            "因此不会把结果包装成生产安全 100%。",
            "我的毕业设计是《基于大模型 RAG 的荔枝智能问答平台设计与实现》"
            "（2026 届优秀毕业设计，得分 90.4），独立开发荔枝农技 AI Agent 协同平台"
            "（Spring Boot 3.2 + Vue3 + TypeScript，22 个业务页面）；受控 Agent 通过工具白名单、"
            "角色过滤、4 步预算和人工审批约束写操作，RAG 组合 Milvus 文档证据与 Neo4j 关系数据。"
            "Milvus、Neo4j、Ollama 曾同时实际运行并在答辩现场演示；数据平台、可观测性与 Helm "
            "是我实现的实验模板，不表述为生产部署。",
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
        "heading": "AI 面试协作站（jianli）",
        "body": (
            "面向真实上线的 AI 面试协作站：把有依据的项目问答、受控预约 Agent、并发与隐私"
            "保护、异步通知、Agent Lab、版本化评测和可观测性串成一条可验证产品链。核心不是"
            "聊天页面，而是让 Agent 有据可答、有权才做、失败可追踪。"
        ),
    }
    projects_sleep: dict[str, object] = {
        "heading": "睡眠分析（sleep202603_an）",
        "body": (
            "团队开发的睡眠健康 AI Agent 平台；我主要负责云端后端、Agent Runtime 与 RAG。"
            "最有价值的不是模型包装，而是有界异步接纳、模型外安全治理和流式数据故障恢复："
            "RC 接纳吞吐 +393.9%、P95 1347.73ms→228.85ms，口径与限制均可追问。"
        ),
    }
    projects_litchi: dict[str, object] = {
        "heading": "荔枝问答平台（litchi，毕设）",
        "body": (
            "2026 届优秀毕业设计（90.4 分）：基于大模型 RAG 的荔枝智能问答平台，"
            "一人独立完成 Spring Boot 后端、Vue3 前端、诊断服务、语料与评测。核心价值是把 "
            "Milvus + Neo4j 证据检索、本地 Ollama、工具白名单、角色过滤、步骤预算和人工审批"
            "接成可控业务闭环；完整 AI 环境已现场演示，平台化设施按实验模板标注边界。"
        ),
    }
    projects_sections: list[dict[str, object]] = [projects_jianli, projects_sleep, projects_litchi]
    projects_chunks = [
        *_chunk(
            "jianli",
            [
                (
                    "Jianli 是我独立开发并准备正式上线的 AI 面试协作站：把简历与项目 RAG 问答、"
                    "登录注册、会话、动态时段、预约管理、邮件与飞书通知串成产品链。技术栈是 "
                    "FastAPI、SQLAlchemy/Alembic 0010、PG16 + pgvector、Redis7、React19、"
                    "DeepSeek V4 Flash 与 BGE-M3。"
                ),
                (
                    "Jianli 检索采用向量 top10 + BM25 top10，经 RRF 融合最多 12 个候选，再由可选 "
                    "Cross-Encoder 取 top6；0.47 阈值和 CJK 门槛使越界集 10/10 拒答。BGE-M3 "
                    "纯向量 avg-rank 1.3，对照本地哈希 1.8。Agent 有五个"
                    "白名单工具：知识检索，以及在 RBAC 下创建、查询、取消、改期预约；"
                    "MAX_STEPS=4，写操作复用 BookingService。"
                ),
                (
                    "Jianli Agent Lab 提供依据问答、多步只读预约、安全越权攻击、无依据拒答四个"
                    "真实挑战，点击后调用右侧 SSE 问答。answer.trace 展示策略、路由、检索/工具、"
                    "生成与结果的脱敏时间线，只含白名单字段，不含原文、Prompt、知识内容、"
                    "工具参数/完整结果或预约 PII，也不是模型思维链。"
                ),
                (
                    "Jianli 评测中心是项目页公开证据、无需登录，读取版本化报告；当前 79/79："
                    "Agent/Trace 22、事实一致性 38、"
                    "Web 1、Reranker 协议 4、缓存与 Provider 韧性 8、多副本熔断 6。GitHub Actions "
                    "已有 backend→RAG→Web 串行硬门禁，本地等价流程通过；尚未授权 push，"
                    "没有远端 Actions run，不能说云端 CI 已实际运行。"
                ),
                (
                    "Jianli 可观测闭环用 OpenTelemetry 记录 "
                    "HTTP/AIQA/tool/rerank/cache/breaker 阶段，"
                    "Prometheus 私网抓取低基数指标，Grafana 当前 10 个面板；Nginx 对公网 metrics "
                    "返回 404。未配置 OTLP 时 no-op，采集失败不影响业务；禁止原文、PII、密钥和"
                    "高基数 ID。配置与测试已验证，完整容器栈首次部署 smoke 仍待执行。"
                ),
                (
                    "Jianli 的 Qwen3-Reranker-8B 只重排已授权候选，失败回退 RRF；5 题真实 provider "
                    "组件对照 MRR 0.3333→1.0000、Hit@1 0/5→5/5。它证明了这组候选的排序改善，"
                    "但样本很小，不能外推为端到端生产质量；79/79 同样不是生产准确率，"
                    "重排也不能扩大召回或绕过拒答。"
                ),
                (
                    "Jianli 预约用 3 分钟预览令牌且不预占，创建时复核连续 Slot，并以行锁和数据库"
                    "唯一约束防超卖；AES-256-GCM 保护敏感字段，Outbox 异步投递邮件/飞书。匿名"
                    "grounded 回答可进同域语义缓存，LLM/Reranker 使用 Redis Lua 共享熔断；"
                    "一次检索回归 8/8→6/8 的根因是 litchi 中 hi 被问候判断误匹配，改整词后恢复。"
                    "正式域名部署、远端 CI 和完整观测栈 smoke 仍属于上线验收。"
                ),
            ],
        ),
        *_chunk(
            "sleep202603_an",
            [
                (
                    "Sleep 是团队开发的非接触式睡眠监测与受控 Agent 平台。我主要负责云端后端、"
                    "Agent Runtime 与 RAG，也参与遥测链路、多租户治理和联调；固件主要由同事负责，"
                    "我做云侧验证。项目使用过真实 ESP32/雷达硬件日志，但未完成生产上线。"
                ),
                (
                    "Sleep Agent 使用固定 route→policy→finalize DAG，不是开放式 ReAct。"
                    "同步执行改成 "
                    "202 异步接纳、有界队列与背压后，RC 接纳吞吐 87.78→433.53 次/秒（+393.9%），"
                    "P95 1347.73→228.85ms；这些是接纳性能，不是 LLM 推理速度。"
                ),
                (
                    "Sleep RAG 基于 PostgreSQL + pgvector，以租户上下文限制检索；模型外再用固定图、"
                    "工具白名单、HITL 和预算约束写操作。当前没有足够证据宣称 Hybrid/BM25/RRF、"
                    "rerank、claim 级引用或正式 Recall/MRR，RAG 是证据层而非性能主卖点。"
                ),
                (
                    "Sleep 流式故障：Worker 重平衡曾出现 6291 行但仅 6240 唯一事件，多出的"
                    "51 条是不应出现的重复写入，根因是 "
                    "ClickHouse Array(UUID) 查重静默返回空集。改为 String 数组并在 SQL 转 UUID 后，"
                    "3 轮均 6240/6240、lag=0，300 次重放全抑制，恢复中位数 12.605s；"
                    "仅代表本地双进程、单 Kafka、单 ClickHouse 验证。"
                ),
                (
                    "Sleep 证据：确定性工程集共七类（不是六类）、84/84，"
                    "但健康合规子项 71.43%，"
                    "公开 Harness 的设备 ACK "
                    "为模拟；120 条红队由我和同事共同设计、执行、分析，96 条通过（80%），危险写"
                    "工具调用为 0。失败说明正则难覆盖语义变体，不能宣称生产安全 100%。"
                ),
                (
                    "Sleep 历史 ACK/RDS staging 由我实际操作排障，基础设施和迁移曾在阿里云跑通，"
                    "但应用启动失败。内部未提交 RC 做过 command_id、请求指纹、数据库唯一约束和"
                    "真实设备 ACK；受 NDA 约束不展示源码/日志/截图，也不当作公开仓库可复现证据。"
                ),
            ],
        ),
        *_chunk(
            "litchi",
            [
                (
                    "litchi 荔枝问答平台是我的 2026 届优秀毕业设计（90.4 分）：《基于大模型 RAG 的"
                    "荔枝智能问答平台设计与实现》。我一人独立完成 Spring Boot 3.2 后端、Vue3 "
                    "前端、Python 诊断服务、知识语料与评测，共 22 个业务页面。Milvus、Neo4j、"
                    "Ollama 曾同时实际运行并在答辩现场演示；数据平台、可观测性和 Helm "
                    "是实验模板。"
                ),
                (
                    "litchi 受控 Agent：Planner 生成最多 4 步计划，内嵌 Guard 过滤未知/重复工具并按"
                    "角色收窄白名单，Executor 顺序执行，Synthesizer 只基于工具证据作答；写工具先"
                    "进入 waiting_approval。当前同一技术员仍可发起并确认，不宣称双人复核。"
                ),
                (
                    "litchi RAG：支持 txt/md/csv/json/docx/pdf，按 480/120 切块；1024 维确定性哈希"
                    "向量用于 CPU 本地演示，并非语义 embedding。ChatService 合并 Milvus 文档候选"
                    "与 Neo4j 图谱关系，再交给本地 Ollama qwen2.5:0.5b 生成有依据的回答。"
                ),
                (
                    "litchi 的证据边界：历史 50 并发本地测试全部成功，但后续 100 并发、200 请求"
                    "多轮成功率仅约 50.5%/21%/19%，环境条件不同，不能强推因果，只能确认高并发"
                    "稳定性未达标。Redis Stream、租户级 RLS、专用 Agent 执行器、事务 Outbox 与"
                    "Token/成本预算均是下一版计划，尚未落地。"
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
        "- 实习：泰益智医疗科技（广州）有限公司（2025.12—2026.06），AI 全栈开发工程师；"
        "在团队开发的睡眠健康 AI Agent 平台中主要负责云端后端、Agent Runtime 与 RAG；"
        "有界异步接纳使 RC 吞吐 87.78→433.53 次/秒（+393.9%）、P95 "
        "1347.73→228.85ms，该指标不是 LLM 推理耗时\n"
        "- 工作经历：曾负责预约与协作类系统的后端架构，落地插槽快照、实时刷新与幂等写入；"
        "也做过内容问答与检索相关功能\n"
        "- 最骄傲的项目：睡眠健康 AI Agent 平台——用固定 DAG、工具白名单、租户上下文、"
        "Human-in-the-loop 和预算约束把安全边界放在模型之外；84 条确定性工程集通过，"
        "120 条协作红队通过 96 条（80%），危险写工具调用 0 次，但不宣称生产安全 100%\n"
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
