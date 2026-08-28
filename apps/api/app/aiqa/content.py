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
                    "Jianli 是我独立开发并准备正式上线的 AI 面试协作站。React 19 调用 FastAPI，"
                    "把简历与项目 RAG、邮箱验证码登录、本人会话、动态 Slot、预约管理、管理员看板、"
                    "邮件和飞书同步串成产品链；数据层是 SQLAlchemy/Alembic 0010、PG16 + pgvector"
                    "与 Redis7，模型链路使用 DeepSeek V4 Flash、BGE-M3 和可选 Qwen3-Reranker-8B。"
                    "证据门、服务端 RBAC、数据库事务分别约束回答、工具和副作用。"
                ),
                (
                    "模型可自主生成检索词，但服务端同时检索模型词和用户原问题并去重合并，避免"
                    "改写失真丢证据。BGE-M3 向量 top10 必须先过 0.47；没有向量候选时不会仅凭"
                    "BM25 中文单字重叠硬答。通过后与 BM25 top10 做 RRF(k=60) 融合 top12，可选"
                    "Cross-Encoder 再取 top6，并保持页面/项目域隔离。回答以 SSE 返回引用；无依据"
                    "明确拒答。BGE-M3 纯向量 avg-rank 1.3，本地哈希 fallback 为 1.8。"
                ),
                (
                    "避免智能体乱调用不能只靠 Prompt：Jianli Agent 最多循环 4 步，只注册检索、"
                    "创建预约、查询/取消/改期本人预约五个"
                    "工具；未知工具拒绝，预约工具必须登录且复用 BookingService，模型不能直写"
                    "数据库，"
                    "管理员管理他人走独立管理端边界。Agent Lab 的四类挑战调用同一 SSE 真链路。"
                    "answer.trace 只公开单调步骤、固定阶段/状态、白名单工具、耗时和短标签，不含"
                    "Prompt、原文、参数、完整结果或 PII；它是执行事实，不是模型思维链。"
                ),
                (
                    "Jianli 评测中心读取带时间和 verified commit 的版本化报告；当前 79/79 分为"
                    "Agent/Trace 22、RAG 事实 38、Web 1、Reranker 协议 4、缓存/Provider 韧性 8、"
                    "跨实例熔断 6。真实 RAG 门禁上传语料并走 BGE-M3、pgvector、命中/拒答/隐私。"
                    "GitHub workflow 定义 backend→RAG→Web 三个串行 job，但现有证据是本地等价"
                    "门禁通过，没有远端 Actions run，不能说云端流水线已跑绿；79/79 也不等于"
                    "生产准确率。"
                ),
                (
                    "Jianli 显式启用 OpenTelemetry 后覆盖完整 HTTP 流式响应，并观测 AIQA 结果/耗时/"
                    "token、工具、重排、缓存和熔断；标签只用规范化 route 与有界状态。Prometheus "
                    "私网 /internal/metrics 对公网 404，Grafana 有 10 个面板。问题、回答、Prompt、"
                    "知识原文、PII、密钥、高基数 ID 和异常正文不进属性。代码和测试已验证，完整"
                    "Collector/Prometheus/Grafana 容器栈 smoke 尚未完成。"
                ),
                (
                    "Qwen3-Reranker-8B 只重排已经通过域过滤和证据门的 RRF top12；服务端校验返回"
                    "数量、类型、重复和越界索引后取 top6。超时 5 秒、429/5xx、畸形协议或熔断都"
                    "完整回退 RRF 原顺序。5 题真实 provider 组件对照 MRR 0.3333→1.0000、Hit@1 "
                    "0/5→5/5，只能证明这组候选排序改善，不能外推生产质量，也不能绕过拒答。"
                ),
                (
                    "预约预览令牌绑定用户和表单、3 分钟有效且不占 Slot；确认时同一事务锁公司和"
                    "三个连续 30 分钟 Slot，写预约、更新 Slot、Outbox 与审计。Slot 竞争靠行锁和"
                    "事务复核；活动用户/公司部分唯一索引独立约束重复预约，不是行锁失效兜底。"
                    "字段以带 AAD 的 AES-256-GCM 加密，去重存 HMAC 指纹；过期预约自动完成。"
                    "Outbox Worker 用 SKIP LOCKED，属于 at-least-once 而非外部 exactly-once。匿名无"
                    "会话的 grounded 回答才进 0.94/600 秒语义缓存，知识变更失效；LLM/Reranker 用"
                    "Redis Lua 共享熔断和单恢复探针。正式域名与完整观测 smoke 仍待验收。"
                ),
            ],
        ),
        *_chunk(
            "sleep202603_an",
            [
                (
                    "Sleep 是团队开发的非接触式睡眠监测与受控 Agent 平台。我主要负责云端后端、"
                    "Agent Runtime 与 RAG，也参与遥测链路、多租户治理、云环境和联调；固件主要由"
                    "同事负责，我做云侧验证。项目使用过真实 ESP32/雷达日志；NDA 材料不公开，"
                    "历史 staging 应用启动失败，不能称为生产上线。"
                ),
                (
                    "Sleep 控制面鉴权并解析可信 tenant 后创建 AgentRun 与 Outbox，再投递 FastAPI。"
                    "本地有界队列默认容量 1000、10 个 Worker，HTTP 202 只代表接纳。并发 100、"
                    "1000 个合成请求下接纳吞吐 87.78→433.53 次/秒，P95 1347.73→228.85ms；"
                    "不含真实 LLM/RAG/工具或跨 Pod，不能说推理提速。Run 与 Outbox 也非同一事务。"
                ),
                (
                    "Sleep 任务编排使用 LangGraph route→policy→finalize 固定 DAG，不是 ReAct。"
                    "local "
                    "coordinator "
                    "负责进程内队列与 SQLite 恢复；Temporal 有 Workflow/信号/Activity 代码，但测试"
                    "使用 Fake Client，不能宣称真实中断恢复；PostgreSQL Store 只存快照，没有 CAS。"
                    "五个预算字段中部分在执行后检查，也没有货币成本预算。"
                ),
                (
                    "Sleep 六个工具由 Agent 类型固定规划，再经 policy allowlist、参数与设备校验；"
                    "device_control 未审批会暂停，但当前不是职责分离审批。控制面没有为该类型注入"
                    "可信设备白名单，执行器缺省又回退到输入 device_id；内部 Agent 端点也没有独立"
                    "服务身份，所以不能宣称设备归属和服务认证已经闭环。"
                ),
                (
                    "Sleep RAG 实现摄入、分块、Embedding、pgvector 余弦检索、global+tenant 过滤、"
                    "引用和无证据拒答；真实 PG 有 2/2 隔离测试，另有 8/8 确定性契约，但测试向量"
                    "固定。没有 BM25/RRF、reranker、阈值或正式 Recall/MRR；固定工具能防改工具类型，"
                    "不能证明未知 Prompt Injection 与输出 DLP 已解决。"
                ),
                (
                    "Sleep 流式故障：Worker 重平衡曾出现 6291 行但仅 6240 唯一事件，多出的"
                    "51 条是不应出现的重复写入，根因是 "
                    "ClickHouse Array(UUID) 查重静默返回空集。改为 String 数组并在 SQL 转 UUID 后，"
                    "3 轮均 6240/6240、lag=0，300 次重放全抑制，恢复中位数 12.605s；"
                    "仅代表本地双进程、单 Kafka、单 ClickHouse 验证。"
                ),
                (
                    "Sleep 后端 MQTT command/ACK 和固件源码存在，真实硬件联调由本人确认；但公开 "
                    "Agent Harness 的 ACK 是模拟。当前仓库每次 HTTP 请求生成新 command_id，没有"
                    "请求 fingerprint 幂等闭环，迟到 ACK 可能改写 timeout。内部 RC 的指纹、唯一约束"
                    "和真实 ACK 属于 NDA 经历，不冒充公开仓库可复现实现。"
                ),
                (
                    "Sleep HEAD 的 84 条确定性用例实际由 11 个 case group 组成并全部通过；七类只是"
                    "展示归并。它固定 Provider/特征/语料且模拟设备 ACK，只验证状态和工具序列。"
                    "未提交"
                    "RC 的健康合规为 25/35；120 条红队由我和同事协同设计执行，96/120，危险写工具"
                    "调用为 0，但 17 条输入守卫漏检，不能称为生产安全率。"
                ),
                (
                    "Sleep 历史阿里云基础设施和迁移跑通过，但应用启动失败，候选未重新部署。当前有"
                    "健康、指标和脱敏 metadata Trace View；Prometheus 实抓、告警恢复、跨服务 "
                    "Trace、"
                    "Temporal 中断恢复和镜像回滚尚无证据。下一版优先做事务 Outbox、服务身份、可信"
                    "设备归属、持久执行、请求幂等和 queued/running/waiting_approval 中断演练。"
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
                    "litchi 把农户、门店、技术员的诊断线索、证据、方案、确认、咨询和反馈放在同一"
                    "产品中，但相邻模块之间缺少统一业务 ID 和强状态关联，因此只能称为部分协作闭环，"
                    "不能宣传完整履约闭环。"
                ),
                (
                    "litchi 受控 Agent：Planner 生成最多 4 步计划，内嵌 Guard 过滤未知/重复工具并按"
                    "角色收窄白名单，Executor 顺序执行，Synthesizer 只基于工具证据作答；写工具先"
                    "进入 waiting_approval。当前同一技术员仍可发起并确认，不宣称双人复核。异步"
                    "执行使用公共线程池，cancel 不能中断已经发出的依赖调用。"
                ),
                (
                    "litchi RAG：支持 txt/md/csv/json/docx/pdf，按 480/120 切块；1024 维确定性哈希"
                    "向量由双字符/分词 Java hash 后 L2 归一化，用于 CPU 本地演示，并非语义 "
                    "embedding。"
                    "查询合并 Milvus 与本地候选，做标题/来源/关键词启发式重排，再用 Neo4j 补关系"
                    "证据并交给 Ollama；不能宣称 BM25/RRF、高级 reranker 或特定 HNSW/IVF 调优。"
                ),
                (
                    "litchi 评测：测试源码已提交；38/38 和 119 轮巡检来自未提交本地报告。60 条数据"
                    "与结构校验已提交，但真实 runner 为 Agent 20/20、RAG 24/30、安全 0/10，gate "
                    "失败；角色/租户、citation、P95 和成本统计都有口径缺陷，因此结果用于暴露盲区。"
                ),
                (
                    "litchi 并发边界：历史 50 并发/50 请求全成功，平均约 6.9s、P95 约 11.2s；"
                    "后续 100 并发/200 请求多轮成功率约 50.5%/21%/19%，一轮 P95 约 15.2s。条件"
                    "没有严格冻结，不能证明唯一根因，只能确认高并发稳定性未达标。"
                ),
                (
                    "litchi 当前 Agent 状态与 outbox 不在同一事务；后端有 SSE 状态端点，前端主要"
                    "轮询；诊断链有真实模型、数据集演示和后端 fallback，仓库无可复现准确率报告。"
                    "Redis Stream/Last-Event-ID、租户 RLS、专用执行器、事务 Outbox、职责分离审批、"
                    "全链 deadline 与 Token/成本预算都是下一版方案，尚未落地。"
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
