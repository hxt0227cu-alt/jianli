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
_UPDATED_AT = datetime(2026, 9, 4, 0, 0, tzinfo=UTC)


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
    """Construct the in-memory page registry (content refreshed 2026-09 per new resume)."""

    resume_sections: list[dict[str, object]] = [
        {
            "heading": "简介",
            "body": (
                "我是一名 AI 应用开发工程师，关注业务落地的 AI Agent 工程、RAG 与云边端系统。"
                "这个站点是我本人的数字分身，用来回答关于我经历的问题并承接面试预约。"
            ),
        },
        {
            "heading": "教育背景",
            "body": (
                "公办本科计算机科学与技术专业，2026 届本科，专业排名 3/153（前 2%）。"
            ),
        },
        {
            "heading": "工作经历",
            "body": (
                "在泰益智医疗科技（2026.01—2026.08）任 AI 应用开发工程师，负责睡眠健康 AI "
                "Agent 平台（Agent Runtime、模型与工具治理、数据链路、Harness 治理）与 MCP "
                "智能数据分析引擎；在吉利控股（2025.10—2025.12）任 AI 应用开发实习生，负责"
                "极氪智能座舱助手；独立开发荔枝农技 AI Agent 协同平台（优秀毕设）与本项目 "
                "jianli（AI Agent 问答与面试预约系统）。偏好先设计后编码，重视可观测与可演进。"
            ),
        },
        {
            "heading": "技术栈",
            "body": (
                "Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React；"
                "LangGraph / Temporal、MCP、Kafka / Flink / ClickHouse；熟悉 RAG 与人格层问答、"
                "受约束的 AI Agent 编排。"
            ),
        },
    ]
    resume_chunks = _chunk(
        "简历",
        [
            "我是一名 AI 应用开发工程师，22 岁，现居深圳南山，可立即到岗；公办本科计算机"
            "科学与技术专业 2026 届毕业生，专业排名 3/153（前 2%）。",
            "我在泰益智医疗科技（广州）有限公司任 AI 应用开发工程师（2026.01—2026.08），"
            "参与睡眠健康 AI Agent 平台：基于 LangGraph + Temporal 构建统一 Agent Runtime，"
            "落地 5 类业务 Agent 与 Planner-Executor-Validator 协作，依托 PostgreSQL 实现长任务"
            "断点恢复；工具调用准确率 92.0%、非法调用率 4.1%；MQTT→Kafka→ClickHouse 链路"
            "故障恢复中位数约 13 秒；三层评测体系 80+ 回归用例通过率超 99%。这些指标来自内部"
            "NDA 验证，可追问口径，不公开原始证据。",
            "同一段工作期间，我参与 MCP 智能数据分析引擎（电商查数）：LangGraph 意图分类"
            "工作流 + MCP-Server 封装，分析效率提升约 60%、人工参与减少 50%+；NL2SQL + "
            "NL2Python 双 MCP-Server 与 Chroma 向量化，NL2SQL 幻觉率 5% 以下；Redis Bitmap "
            "分片（1000 分片 125 字节）+ Redisson + MinIO 断点续传，响应时间降低约 40%。",
            "我在浙江吉利控股集团任 AI 应用开发实习生（2025.10—2025.12），参与极氪智能座舱"
            "助手：LangChain + ReAct 四类 Agent 与 Skill 封装，10 轮短记忆 + 长期偏好；父子"
            "切块 + BM25 + BGE-M3 RRF + BGE-Reranker，Ragas Faithfulness 0.91、Answer "
            "Relevancy 0.88；5000 条数据 Qwen3-14B LoRA + DPO，意图识别 90.2%（+8%）、安全"
            "偏好命中 92.5%；复杂联动成功率 91%、平均响应 2 秒内。",
            "我的毕业设计是荔枝农技 AI 协同平台 Litchi Copilot（2026 届优秀毕设，"
            "2025.06—2026.05）：Planner-Guard-Executor-Synthesizer 编排器、5 类工具、4 步规划、"
            "7 类运行状态，HITL（预览→暂停审批→确认→落库），禁止 Shell-SQL-URL，快照 + "
            "幂等键 + 500 条内存降级 + SSE；RAG 采用 480+120 切块、1024 维哈希向量 Milvus + "
            "词法混合、Neo4j 关系，降级问答平均 159.88ms；60 条评测集（30 RAG + 20 Agent + 10 "
            "安全）、Prometheus、5 类 CI、k6。",
            "我在校主持国家级大创项目慧眼识蚁——红火蚁智能追踪与靶向灭治装备"
            "（2024.05—2025.05）：下位机控制/上位机视觉/云端分析三级架构；FreeRTOS 信号量"
            "互斥锁队列、MPU6500 DMP 四元数、PID+PWM 闭环调速、看门狗 72h、RPLIDAR S2 栅格"
            "地图、W25Q64JV Flash、EC800M 4G + MQTT 阿里云 IoT、树莓派 4B + YOLOv5s。",
            "技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、"
            "LangGraph / Temporal、MCP、Kafka / Flink / ClickHouse；熟悉 RAG 与人格层问答、"
            "受约束的 AI Agent 编排（工具白名单 + RBAC + 预算熔断 + HITL 审批）。",
            "我偏好先设计后编码，重视可观测性、可演进性与契约测试。",
            "我适合 AI 应用开发、后端与平台工程岗位，尤其适合重视工程质量、技术深度、协作"
            "和可交接性的团队；选择公司时看重完整工程环境、成长空间和技术成长路径，长期向"
            "架构师发展。",
            "我最有成就感的一段工程经历，是建立一套可复现、可交接的确定性验证闭环：80+ 条"
            "工程回归用例通过率超 99%，三轮 Kafka 重平衡事件零丢失。我的核心贡献是把评测、"
            "故障注入、数据校验和结果留痕串成统一证据链，让结果能够被复跑、被核验，也能交给"
            "下一位工程师继续维护。",
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
        "heading": "睡眠健康 AI Agent 平台（sleep，泰益智）",
        "body": (
            "泰益智（2026.01—2026.08）参与的团队核心项目：LangGraph + Temporal 统一 Agent "
            "Runtime，5 类业务 Agent，Planner-Executor-Validator；工具白名单 + HITL + 超时熔断；"
            "pgvector 租户隔离与分层记忆；工具调用准确率 92.0%、非法调用率 4.1%、故障恢复中位数"
            "约 13 秒、80+ 回归用例通过率超 99%。指标来自内部 NDA 验证，口径与限制均可追问。"
        ),
    }
    projects_mcp: dict[str, object] = {
        "heading": "MCP 智能数据分析引擎（mcp，泰益智）",
        "body": (
            "泰益智期间参与的电商查数项目：LangGraph 意图分类工作流 + MCP-Server 封装，"
            "NL2SQL / NL2Python 双引擎 + Chroma 向量化，NL2SQL 幻觉率 5% 以下；Redis Bitmap "
            "分片 + Redisson + MinIO 断点续传，分析效率提升约 60%、人工参与减少 50%+、响应时间"
            "降低约 40%。指标来自内部 NDA 验证，口径与限制均可追问。"
        ),
    }
    projects_zeekr: dict[str, object] = {
        "heading": "极氪智能座舱助手（zeekr，吉利实习）",
        "body": (
            "吉利控股（2025.10—2025.12）实习项目：LangChain + ReAct 四类 Agent 与 Skill 封装，"
            "10 轮短记忆 + 长期偏好；BM25 + BGE-M3 RRF + BGE-Reranker，Ragas Faithfulness 0.91、"
            "Answer Relevancy 0.88；5000 条数据 Qwen3-14B LoRA + DPO，意图识别 90.2%（+8%）、"
            "安全偏好命中 92.5%、联动成功率 91%、平均响应 2 秒内。指标来自内部 NDA 验证，"
            "口径与限制均可追问。"
        ),
    }
    projects_litchi: dict[str, object] = {
        "heading": "荔枝农技 AI 协同平台（litchi，毕设）",
        "body": (
            "2026 届优秀毕设：荔枝农技 B2B2C 协同平台，一人独立完成 Spring Boot 后端、Vue3 "
            "前端、诊断服务、语料与评测。Planner-Guard-Executor-Synthesizer 受控编排器 + HITL "
            "审批 + Milvus/Neo4j 混合证据检索；完整 AI 环境已现场演示，平台化设施按实验模板"
            "标注边界。"
        ),
    }
    projects_anteye: dict[str, object] = {
        "heading": "慧眼识蚁——红火蚁智能追踪与靶向灭治装备（大创）",
        "body": (
            "国家级大创项目（2024.05—2025.05，主持）：下位机控制/上位机视觉/云端分析三级"
            "架构。FreeRTOS 实时调度、MPU6500 DMP + PID 闭环调速、看门狗 72h、RPLIDAR S2 栅格"
            "地图、EC800M 4G + MQTT 阿里云 IoT、树莓派 4B + YOLOv5s 蚁巢识别。"
        ),
    }
    projects_sections: list[dict[str, object]] = [
        projects_jianli,
        projects_sleep,
        projects_mcp,
        projects_zeekr,
        projects_litchi,
        projects_anteye,
    ]
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
                    "改写失真丢证据。BGE-M3 向量 top10 必须先过 0.47；拒答判定是 0.47 阈值 + "
                    "BM25 CJK 停用词过滤（的/了/是等功能字不参与重叠计数）双层证据门，没有向量"
                    "候选时不会仅凭 BM25 中文单字重叠硬答。通过后与 BM25 top10 做 RRF(k=60) "
                    "融合 top12，可选 Cross-Encoder 再取 top6，并保持页面/项目域隔离。回答以 "
                    "SSE 返回引用；无依据明确拒答。BGE-M3 纯向量 avg-rank 1.3，本地哈希 "
                    "fallback 为 1.8。回答边界有个踩过的坑：问候语最初用子串包含，'hi' 会被 "
                    "'litchi'、'this' 等词误判成打招呼，后来改为整词匹配——'hi' 必须独立成词"
                    "才视为问候，含 'hi' 子串的工程问题照常走检索问答。"
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
                    "跨实例熔断 6。真实 RAG 门禁上传语料并走 BGE-M3、pgvector、命中/拒答/隐私；"
                    "越界集 10/10 拒答（拒答率 100%，从早期 0% 提升）在真实 embedding + 0.47 "
                    "阈值下验收。GitHub workflow 定义 backend→RAG→Web 三个串行 job，但现有证据"
                    "是本地等价门禁通过，没有远端 Actions run，不能说云端流水线已跑绿；79/79 也"
                    "不等于生产准确率。"
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
            "sleep",
            [
                (
                    "Sleep 是泰益智团队开发的非接触式睡眠健康 AI Agent 平台（2026.01—2026.08，"
                    "AI 应用开发工程师）。我主要负责 Agent 运行时编排、模型与工具治理、实时数据"
                    "链路与 Harness 工程治理。以下指标来自内部 NDA 验证，可追问口径，不公开原始"
                    "证据。"
                ),
                (
                    "Sleep Agent Runtime：基于 LangGraph + Temporal 构建统一 Agent Runtime，落地 "
                    "5 类业务 Agent，采用 Planner-Executor-Validator 多智能体协作，依托 PostgreSQL "
                    "实现长任务断点恢复；落地工具白名单、HITL 人工审批与超时熔断，集成 "
                    "Prometheus+Grafana 全链路监控，保障过程可控、可观测、可审计。"
                ),
                (
                    "Sleep 模型与知识治理：构建 OpenAI 兼容模型网关，支持结构化输出、限流降级与"
                    "熔断及 Token 成本统计，对接 SSO/OIDC 落地细粒度 RBAC；基于 pgvector 实现"
                    "租户级知识隔离与分层记忆；经 QLoRA 微调与 DPO 对齐，工具调用准确率提升至 "
                    "92.0%，非法调用率降至 4.1%。（口径：内部 NDA 验证。）"
                ),
                (
                    "Sleep 数据链路：搭建 MQTT→Kafka→ClickHouse 端到端遥测链路，实现多源设备"
                    "数据实时接入、幂等去重与时序存储；通过消息重试、显式 Offset 提交与死信队列"
                    "保障可靠性，故障恢复中位数约 13 秒。（口径：内部 NDA 验证，本地双进程/单 "
                    "Kafka/单 ClickHouse 环境。）"
                ),
                (
                    "Sleep Harness 治理：建立单元测试、场景回归、语义校验三层 Agent 评测体系，"
                    "覆盖功能、异常与安全场景，80+ 工程回归用例通过率超 99%；基于 Harness 搭建 "
                    "CI/CD 发布治理流水线，集成代码扫描、依赖校验、容器镜像检测与 Agent 自动化"
                    "评测门禁。（口径：内部 NDA 验证。）"
                ),
                (
                    "Sleep 边界与演进：历史阿里云基础设施与数据库迁移跑通过，但应用曾因启动与"
                    "扩展能力问题失败，候选未重新部署，因此不表述为生产上线或 staging 成功；"
                    "下一版聚焦事务 Outbox、服务身份、可信设备归属、持久执行、请求幂等与中断"
                    "演练。"
                ),
            ],
        ),
        *_chunk(
            "mcp",
            [
                (
                    "MCP 智能数据分析引擎是泰益智期间参与的电商查数项目：面向电商运营查数、"
                    "统计、预测及可视化任务，业务人员用自然语言完成意图分流、数据查询、统计预测、"
                    "结果解释及可视化输出，整体分析效率提升约 60%，人工参与减少 50% 以上。"
                    "（口径：内部 NDA 验证。）"
                ),
                (
                    "MCP 编排：基于 LangGraph 构建意图分类—SQL/Python 生成—SQL 校验—任务执行—"
                    "结果解释的状态驱动工作流，根据数据查询、统计分析、预测分析及可视化意图动态"
                    "路由；通过 MCP-Server 标准化封装并调度 SQL、Python 分析能力。"
                ),
                (
                    "MCP 双引擎与可靠性：NL2SQL 与 NL2Python 双 MCP-Server，将业务词典、表结构、"
                    "字段说明及 Few-shot 样例向量化存入 Chroma，通过表字段白名单、结构化输出校验"
                    "及错误反馈重试，将 NL2SQL 幻觉率控制在 5% 以下。"
                ),
                (
                    "MCP 性能：使用 Redis Bitmap 维护大文件分片状态，1000 个分片仅占 125 字节，"
                    "结合 Redisson 与 MinIO 实现并行上传、断点续传及分片合并；引入 Redis 缓存和"
                    "异步任务执行，将平均响应时间降低约 40%。（口径：内部 NDA 验证。）"
                ),
            ],
        ),
        *_chunk(
            "zeekr",
            [
                (
                    "极氪智能座舱助手是吉利控股（2025.10—2025.12）实习项目：面向复杂指令理解、"
                    "精准工具调用、多轮记忆与安全低延迟交互的车机助手。技术栈：Python、LangChain、"
                    "Qwen3-14B、RAG、Skill、ReAct、LoRA、Ragas、BGE-Reranker。（口径：内部 NDA "
                    "验证。）"
                ),
                (
                    "zeekr Agent 与记忆：基于 LangChain 与 ReAct 构建意图路由及音乐、空调、座椅、"
                    "问答四类专用 Agent，将播放控制、温度/风量调节、座椅加热/通风/按摩等能力封装"
                    "为 Skill；设计最近 10 轮短期记忆与长期偏好记忆，沉淀空调预设温度、座椅位置"
                    "及常听歌单，通过滑动窗口压缩与关键信息抽取提升多轮交互一致性。"
                ),
                (
                    "zeekr 车载 RAG：面向车辆功能、语音指令及驾驶模式等产品手册，采用父子切块"
                    "策略，构建 BM25 与 BGE-M3 的 RRF 混合检索链路，并通过 BGE-Reranker 精排；"
                    "Ragas 评测中 Faithfulness 0.91、Answer Relevancy 0.88。"
                ),
                (
                    "zeekr 微调与安全对齐：构建 5000 条座舱控制指令数据，基于 Qwen3-14B 完成 "
                    "LoRA 微调；针对座椅通风误识别为座椅加热等 Bad Case 引入 DPO 对齐，意图识别"
                    "准确率达到 90.2%，较基线提升约 8%；行车安全与合规偏好命中率达到 92.5%，"
                    "降低过度座椅按摩、空调温度过低等不安全操作风险。"
                ),
                (
                    "zeekr 端到端评测：建立模型、RAG 与 Agent 分层评测体系，持续监控意图路由、"
                    "工具选择、参数提取、任务完成及执行时延；复杂联动场景引导成功率达到 91%，"
                    "系统平均响应时长控制在 2 秒以内。（口径：内部 NDA 验证。）"
                ),
            ],
        ),
        *_chunk(
            "litchi",
            [
                (
                    "litchi 荔枝农技 AI 协同平台是我的 2026 届优秀毕设（2025.06—2026.05）：面向"
                    "农技服务公司、合作社及连锁农资机构的 B2B2C 平台，围绕荔枝种植场景，将病害"
                    "识别、RAG 知识问答、AI Agent 辅助决策、技术员审核、门店履约及效果反馈串联成"
                    "完整业务闭环。我独立完成 Spring Boot 3.2 后端、Vue3 前端、Python 诊断服务、"
                    "知识语料与评测。"
                ),
                (
                    "litchi 受控 Agent：设计 Planner-Guard-Executor-Synthesizer 受约束编排器，接入"
                    "果园上下文、知识检索、知识图谱、方案推荐、待审批方案 5 类工具；支持最多 4 步"
                    "规划、RBAC 权限过滤、未知/重复工具拦截、参数校验及全过程轨迹记录，覆盖创建、"
                    "规划、执行、等待审批、完成、失败、取消 7 类运行状态。写工具先进入 "
                    "waiting_approval；当前同一技术员仍可发起并确认，不宣称双人复核。"
                ),
                (
                    "litchi HITL 与降级：针对农技方案写入构建 Human-in-the-loop 机制（生成预览→"
                    "暂停审批→技术员确认→正式落库），从工具协议层禁止 Shell/SQL/URL 及动态代码"
                    "执行；实现运行快照、幂等键、MySQL 持久化、500 条内存降级及 SSE 状态接口，"
                    "通过超时、冷却与 degraded 状态保障异常时可解释响应。"
                ),
                (
                    "litchi RAG：支持 txt/md/csv/json/docx/pdf，按 480 字符 Chunk + 120 Overlap "
                    "切块；1024 维哈希向量（Milvus COSINE）+ 词法召回混合检索，结合标题/来源/"
                    "关键词去重规则重排，融合 Neo4j 品种/病虫害/药剂/栽培关系查询；外部模型不可用"
                    "时 20 次降级问答平均响应 159.88ms。哈希向量是 CPU 本地演示方案，并非语义 "
                    "embedding。"
                ),
                (
                    "litchi 评测与工程化：建设 60 条固定评测集（30 RAG + 20 Agent + 10 安全），"
                    "覆盖召回、工具选择、越权与拒答；补充运行次数/耗时/调用次数等 Prometheus 指标，"
                    "搭建 5 类 CI 任务，k6 压测识别异步线程池与快照持久化优化方向。历史并发边界："
                    "50 并发/50 请求全成功（平均约 6.9s、P95 约 11.2s），高并发稳定性未达目标，"
                    "需继续优化。"
                ),
                (
                    "litchi 诊断与图像实验：从 27,594 张原始图中取五类 300 训练/80 验证，最佳 "
                    "Top-1 93.75%、末轮 91.25%；80 张验证集偏小，只能证明五分类实验链路，不能"
                    "外推真实果园。识别准确率 ≥95% 是申报书目标指标，不表述为已经实测达到。"
                ),
                (
                    "litchi 下一版：Redis Stream/Last-Event-ID、租户 RLS、专用执行器、事务 Outbox、"
                    "职责分离审批、全链 deadline 与 Token/成本预算均为下一版方案，尚未落地。"
                ),
            ],
        ),
        *_chunk(
            "anteye",
            [
                (
                    "慧眼识蚁——红火蚁智能追踪与靶向灭治装备是我主持的国家级大创项目"
                    "（2024.05—2025.05）：作为本科生代表与机械与自动化院研究生合作研发下位机"
                    "实时控制、上位机视觉识别、云端数据分析三级架构的自主巡检机器人。"
                ),
                (
                    "anteye 硬件架构：参与下位机方案设计，采用核心板+底板分层结构，完成器件"
                    "选型、原理图绘制，预留主控拓展接口实现模块化复用；完成板卡焊接及示波器/"
                    "万用表电路功能调试。"
                ),
                (
                    "anteye 实时系统与运动控制：移植 FreeRTOS，通过信号量、互斥锁、消息队列实现"
                    "传感器采集、电机控制、姿态解算与避障任务的并发调度；基于 MPU6500 DMP 解算"
                    "四元数，结合增量式编码器反馈与 PID 算法输出 PWM 占空比，实现直流减速电机"
                    "闭环调速；配置独立看门狗，系统稳定运行 72 小时。"
                ),
                (
                    "anteye 感知与通信：驱动 RPLIDAR S2 激光雷达构建局部栅格地图，实现自主运动"
                    "与动态避障；通过 SPI 将陀螺仪与雷达数据存入 W25Q64JV Flash；基于 EC800M 4G "
                    "模块通过 UART 与 MCU 通信，采用 MQTT 协议对接阿里云 IoT 平台；配合树莓派 "
                    "4B 上位机完成 YOLOv5s 蚁巢识别模型联调。"
                ),
                (
                    "anteye 成果：项目获国家级大创立项；对应挑战杯科技发明制作 A 类赛事"
                    "路演资格。识别准确率 ≥95% 是申报书目标指标，不表述为已经实测达到；相关专利"
                    "归属课题依托单位。"
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
                "睡眠健康 AI Agent 平台做到了什么程度？",
                "荔枝农技 AI 协同平台（litchi）这个项目是做什么的？",
                "极氪智能座舱助手用到了哪些技术？",
                "你在项目里最得意的一个设计决策是什么？",
            ],
        ),
    }


PAGES = build_pages()


def build_resume_facts_card() -> str:
    """Hard, always-injected resume facts for the digital-twin voice.

    These are verbatim anchors distilled from the ``resume`` page chunks.
    They are injected into the *system* prompt (higher weight than the
    retrieved 【已知资料】 block) and pinned with a "use verbatim" constraint,
    so open-ended questions (methodology / what-you-value / other-directions)
    cannot be answered with generic paraphrases that drift from the source.

    MUST stay in sync with ``resume_chunks`` and ``docs/fact-consistency/fact-bank.md``.
    Identity rule (2026-09): the card carries NO real name / university / phone /
    personal email; NDA-bound metrics carry the 口径说明 note.
    """

    return (
        "【硬性事实卡·简历】(以下事实优先级最高，回答对应主题时必须逐字使用，"
        "不得自行归纳或替换)\n"
        "- 身份与教育：AI 应用开发工程师，22 岁，现居深圳南山，可立即到岗；"
        "公办本科计算机科学与技术专业 2026 届毕业生，专业排名 3/153（前 2%）\n"
        "- 工作经历①：泰益智医疗科技（广州）有限公司（2026.01—2026.08），AI 应用开发工程师；"
        "睡眠健康 AI Agent 平台（Agent Runtime、模型与工具治理、数据链路、Harness 治理）与 "
        "MCP 智能数据分析引擎（电商查数）\n"
        "- 工作经历②：浙江吉利控股集团（2025.10—2025.12），AI 应用开发实习生；"
        "极氪智能座舱助手\n"
        "- 关键指标（内部 NDA 验证，可追问口径、不公开原始证据）：工具调用准确率 92.0%、"
        "非法调用率 4.1%、故障恢复中位数约 13 秒、80+ 回归用例通过率超 99%、分析效率提升约 "
        "60%、人工参与减少 50%+、NL2SQL 幻觉率 5% 以下、响应时间降低约 40%、Ragas "
        "Faithfulness 0.91 / Answer Relevancy 0.88、意图识别 90.2%（+8%）、安全偏好命中 92.5%、"
        "联动成功率 91%、平均响应 2 秒内\n"
        "- 最骄傲的项目：睡眠健康 AI Agent 平台——用固定 DAG、工具白名单、租户上下文、"
        "Human-in-the-loop 和预算约束把安全边界放在模型之外\n"
        "- 毕业设计：2026 届优秀毕设 Litchi Copilot（荔枝农技 AI 协同平台）\n"
        "- 在校项目：国家级大创慧眼识蚁——红火蚁智能追踪与靶向灭治装备\n"
        "- 技术方向：AI 应用开发工程师，关注业务落地的 AI Agent 工程、RAG 与云边端系统\n"
        "- 工程方法论：我偏好先设计后编码\n"
        "- 最看重的工程品质：重视可观测性、可演进性与契约测试\n"
        "- 方向补充①：我曾负责预约与协作类系统的后端架构，落地过插槽快照、实时刷新与幂等写入\n"
        "- 方向补充②：我也独立做过内容问答与检索相关的功能\n"
        "- 技术栈：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、"
        "LangGraph / Temporal、MCP、Kafka / Flink / ClickHouse\n"
        "- 熟悉的 AI 技术：RAG 与人格层问答、受策略/审批/持久化约束的 AI Agent 编排\n"
        "- 荣誉：2025 年国家励志奖学金、2024 年大创国家级立项（第一负责人）、"
        "2024 挑战杯 A 类赛事路演资格、2022—2026 校级奖学金、2026 年优秀毕业生\n"
        "- 求职意向：AI 应用开发工程师，意向深圳市南山区\n"
        "- 站点本质：我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约"
    )
