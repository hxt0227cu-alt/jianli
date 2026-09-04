"""Canonical corpus (TASK-AIQA-KB-001): the single source of truth for the AIQA RAG.

Rules:
- Each document is a self-contained, first-person description. Facts (numbers,
  boundaries, ownership) may only be stated here if they are true and verifiable;
  the corpus is the only place the AI may draw resume facts from.
- Keep every doc addressable: the file name is used in tests and citations.
- 23 documents exactly; the hard count is enforced on import (fail fast if a doc
  is added or removed without updating this constant and the tests).
- Identity rule (2026-09): the public corpus must NOT contain the owner's real
  name, university, phone number or personal email. Metrics from internal
  NDA-bound projects carry the 口径说明 note (可追问、不公开原始证据) instead
  of granular internal-audit caveats.
"""

# ruff: noqa: E501
CANONICAL_CORPUS: dict[str, str] = {
    # ------------------------------------------------------------------ #
    # Profile / identity / credentials / behavior                        #
    # ------------------------------------------------------------------ #
    "profile.md": """# 个人档案｜教育、能力与求职方向
我是一名 AI 应用开发工程师，22 岁，现居深圳南山，可立即到岗。公办本科计算机科学与技术专业 2026 届毕业生，专业排名 3/153（前 2%）。聚焦业务落地的 AI Agent 工程，具备 Agent Runtime、MCP 工具协议、RAG 工程化及 AIoT 设备协同实践。熟练使用 Python、Java、TypeScript，掌握 LangGraph、Temporal，可独立完成状态编排、任务拆解、工具调用、长任务恢复、人工审批、评测与安全治理。拥有智能数据分析、睡眠 AIoT、智能座舱及嵌入式机器人项目经验，熟悉 MQTT、Kafka、Redis、PostgreSQL、FreeRTOS，具备云边端系统设计、性能优化与故障定位能力。严格遵循阿里巴巴代码规范，重视模块化设计、自动化测试、持续集成及可观测性建设。主持国家级大创项目，参与挑战杯 A 类路演，获国家励志奖学金、优秀毕业生等。
求职方向：AI 应用开发工程师，意向深圳南山；长期向架构师发展。
【口径说明】本简历涉及的量化指标（如工具调用准确率、非法调用率、恢复耗时、回归通过率、效率提升等）来自内部项目验证（受 NDA 约束），面试中可追问口径与细节，但不公开原始代码、日志、数据与内部文档。""",

    "credentials.md": """# 证书、荣誉与竞赛资格证明
持有 PingCAP TiDB 数据库专员 PCTA 认证证书和大学英语四级 CET4。获得 2025 年国家励志奖学金、2022—2026 学年校级奖学金、2026 年优秀毕业生；2024 年大学生创新创业训练计划国家级立项第一负责人，并获得挑战杯科技发明制作 A 类赛事路演资格。识别准确率 ≥95% 是红火蚁项目申报书目标指标，不表述为已经实测达到；相关专利归属课题依托单位。""",

    "behavior-stories.md": """# 行为故事、协作与职业动机
我偏好先设计后编码，重视可观测性、可演进性与契约测试；失败记录是证据而不是污点。实习中我用一对一演示、任务拆分和验收帮助同事上手新工具与消息链路；当设计与既有组件体系冲突时，我列出转换成本，与产品、设计先对齐核心页面再迭代。三个重要教训是：配置漂移要靠确定性评测暴露；ClickHouse 静默空结果说明零报错不等于正确；性能修复到时间边界仍未达标时应登记风险而不是修改口径。科班背景加上 2023 年起使用 AI 工具开发，让我逐步从实现功能转向思考架构、契约和交付，目标是 AI 应用开发并长期向架构师发展。
我最有成就感的一段工程经历，是建立了一套可复现、可交接的确定性验证闭环：80+ 条工程回归用例通过率超 99%，三轮 Kafka 重平衡事件零丢失。我的核心贡献是把评测、故障注入、数据校验和结果留痕串成统一证据链；这些结果不仅能演示，也能被复跑、被核验并交给下一位工程师继续维护。""",

    # ------------------------------------------------------------------ #
    # Litchi Copilot (毕业设计)                                          #
    # ------------------------------------------------------------------ #
    "litchi-overview.md": """# Litchi Copilot｜荔枝智能农技协同平台（优秀毕设）
这是我 2025.06—2026.05 独立完成的 2026 届毕业设计，获优秀毕设。面向农技服务公司、合作社及连锁农资机构的 B2B2C 智能农技平台，围绕荔枝种植场景，将病害识别、RAG 知识问答、AI Agent 辅助决策、技术员审核、门店履约及效果反馈串联成完整业务闭环。
技术栈：Java 17、Spring Boot 3.2、Vue 3、TypeScript、Python、Agent、Tool Calling、RAG、Ollama/vLLM/OpenAI-compatible API、Milvus、Neo4j、MySQL、Prometheus、Docker。
我独立完成后端、前端（21 个业务页面）、诊断服务、知识语料与评测；Milvus、Neo4j、本地 Ollama 完整环境实际跑通并在答辩现场演示。数据平台、可观测性与容器编排属于实验模板，不表述为生产部署。""",

    "litchi-agent-rag.md": """# Litchi 受控 Agent 与 RAG 调用链
设计 Planner–Guard–Executor–Synthesizer 受约束编排器，接入果园上下文、知识检索、知识图谱、方案推荐、待审批方案 5 类工具；支持最多 4 步任务规划、RBAC 权限过滤、未知/重复工具拦截、参数校验及全过程轨迹记录，覆盖创建、规划、执行、等待审批、完成、失败、取消 7 类运行状态。
针对农技方案写入构建 Human-in-the-loop 机制（生成预览→暂停审批→技术员确认→正式落库），从工具协议层禁止 Shell/SQL/URL 及动态代码执行；实现运行快照、幂等键、MySQL 持久化、500 条内存降级及 SSE 状态接口，通过超时、冷却与 degraded 状态保障异常时可解释响应。
RAG：构建支持 6 类文档格式的 RAG 链路，采用 480 字符 Chunk+120 Overlap 切块；实现 1024 维哈希向量（Milvus COSINE）+词法召回的混合检索，结合标题/来源/关键词去重规则重排，融合 Neo4j 品种/病虫害/药剂/栽培关系查询；外部模型不可用时 20 次降级问答平均响应 159.88ms。哈希向量是 CPU 本地演示方案，不是语义 embedding。""",

    "litchi-evidence-retrospective.md": """# Litchi 评测、可观测与工程化
建设 60 条固定评测集（30 RAG+20 Agent+10 安全），覆盖召回、工具选择、越权与拒答；补充运行次数/耗时/调用次数等 Prometheus 指标，搭建 5 类 CI 任务，k6 压测识别异步线程池与快照持久化优化方向。
历史并发边界：50 并发 50 请求全成功（平均约 6.9s、P95 约 11.2s）；后续 100 并发/200 请求多轮成功率约 50.5%/21%/19%，高并发稳定性未达目标，需继续优化。Agent 状态与 outbox 不在同一事务；前端主要轮询 SSE。
诊断链：原始 11 类 27,594 张图片抽取五类均衡子集（300 训练/80 验证），最佳 Top-1 93.75%、末轮 91.25%；80 张验证集偏小，只能证明五分类实验链路，不能外推真实果园。只有 ultralytics-yolo 且 demoMode=false 才算真实模型推理。""",

    "litchi-evolution.md": """# Litchi 当前边界与下一版演进（方案尚未落地）
当前 run、step、approval、业务写入与 outbox 未处于同一可恢复事务状态机；SSE 事件进程内、前端主要轮询；租户强隔离、专用执行器、事务 Outbox、职责分离审批、全链 deadline 与 Token/成本预算为下一版方案。先修评测可信度与恢复，再谈扩模型与工具。""",

    # ------------------------------------------------------------------ #
    # Sleep AIoT（泰益智，2026.01—2026.08）                              #
    # ------------------------------------------------------------------ #
    "sleep-overview.md": """# 睡眠健康 AI Agent 平台｜项目定位与职责（泰益智）
这是我 2026.01—2026.08 在泰益智医疗科技（广州）有限公司任 AI 应用开发工程师期间参与的核心项目：非接触式智能睡眠健康 Agent 平台。背景：传统睡眠设备存在遥测数据割裂、设备控制缺少权限与安全边界等问题。目标：构建具备可恢复 Agent Runtime、受控工具调用及云边端协同能力的睡眠健康平台，打通"数据采集—分析解读—改善建议—设备执行—效果评估"闭环。我主要负责 Agent 运行时编排、模型与工具治理、实时数据链路与 Harness 工程治理。
技术栈：Python、TypeScript/NestJS、LangGraph、Temporal、Qwen3、RAG/pgvector、PostgreSQL/TimescaleDB、Redis、MQTT/Kafka/Flink/ClickHouse、Taro/React、C/C++/ESP-IDF、Kubernetes。
【口径说明】以下指标来自内部项目验证（NDA 约束），可追问口径，不公开原始证据。""",

    "sleep-agent-runtime.md": """# Sleep Agent Runtime｜可恢复编排与受控工具
基于 LangGraph + Temporal 构建统一 Agent Runtime，落地 5 类业务 Agent；采用 Planner-Executor-Validator 多智能体协作模式，依托 PostgreSQL 实现长任务断点恢复；落地工具白名单、HITL 人工审批与超时熔断机制，集成 Prometheus+Grafana 全链路监控，保障过程可控、可观测、可审计。""",

    "sleep-rag-governance.md": """# Sleep 模型网关、RBAC 与知识隔离
构建 OpenAI 兼容模型网关，接入多基座模型并支持结构化输出、限流降级与熔断；实现多维度 Token 成本统计，对接 SSO/OIDC 体系落地细粒度 RBAC 权限控制；基于 pgvector 实现租户级知识隔离与分层记忆；经 QLoRA 微调与 DPO 对齐后，工具调用准确率提升至 92.0%，非法调用率降至 4.1%。（口径：内部 NDA 验证，可追问。）""",

    "sleep-data-reliability.md": """# Sleep 实时数据链路与可靠性
搭建 MQTT→Kafka→ClickHouse 端到端遥测链路，实现多源设备数据的实时接入、幂等去重与时序存储；通过消息重试、显式 Offset 提交与死信队列保障数据可靠性，故障恢复中位数约 13 秒。（口径：内部 NDA 验证，本地双进程/单 Kafka/单 ClickHouse 环境。）""",

    "sleep-evidence-retrospective.md": """# Sleep Harness 工程治理
建立单元测试、场景回归、语义校验三层 Agent 评测体系，覆盖功能、异常与安全场景，80+ 工程回归用例通过率超 99%；基于 Harness 搭建 CI/CD 发布治理流水线，集成代码扫描、依赖校验、容器镜像检测与 Agent 自动化评测门禁，实现变更可追溯、上线可审计，平衡迭代速度与发布稳定性。（口径：内部 NDA 验证。）""",

    "sleep-evolution.md": """# Sleep 边界与演进
历史阿里云基础设施与数据库迁移跑通过，但应用曾因启动与扩展能力问题失败，候选未重新部署，因此不表述为生产上线或 staging 成功。当前聚焦：事务 Outbox、服务身份、可信设备归属、持久执行、请求幂等与中断演练等下一版能力。数据面与完整生产观测仍在推进中。""",

    # ------------------------------------------------------------------ #
    # MCP 智能数据分析引擎（泰益智）                                     #
    # ------------------------------------------------------------------ #
    "mcp-analytics-engine.md": """# MCP 智能数据分析引擎（泰益智）
泰益智期间参与的另一核心项目：面向电商运营查数、统计、预测及可视化任务。背景：需跨 SQL、Python 多环节，存在分析链路长、业务响应慢问题。目标：业务人员通过自然语言完成意图分流、数据查询、统计预测、结果解释及可视化输出，整体分析效率提升约 60%，人工参与减少 50% 以上。
技术栈：Python、FastAPI、LangGraph、LangChain、MCP-Server、Qwen3-8B、PostgreSQL、Redis、Chroma、MinIO、NL2SQL、NL2Python。
1. Agent 编排与工具标准化：基于 LangGraph 构建"意图分类—SQL/Python 生成—SQL 校验—任务执行—结果解释"的状态驱动工作流，根据数据查询、统计分析、预测分析及可视化意图动态路由；通过 MCP-Server 标准化封装并调度 SQL、Python 分析能力。
2. 双引擎与可靠性治理：开发 NL2SQL 与 NL2Python 双 MCP-Server，分别覆盖业务查询聚合，以及数据清洗、统计建模、预测计算和图表生成；将业务词典、表结构、字段说明及 Few-shot 样例向量化存入 Chroma，通过表字段白名单、结构化输出校验及错误反馈重试机制，将 NL2SQL 幻觉率控制在 5% 以下。
3. 工程可靠性与性能优化：使用 Redis Bitmap 维护大文件分片状态，1000 个分片仅占 125 字节，结合 Redisson 与 MinIO 实现并行上传、断点续传及分片合并；引入 Redis 缓存和异步任务执行策略，将平均响应时间降低约 40%。（口径：内部 NDA 验证。）""",

    # ------------------------------------------------------------------ #
    # 极氪智能座舱助手（吉利控股，实习）                                 #
    # ------------------------------------------------------------------ #
    "zeekr-cockpit-assistant.md": """# 极氪汽车智能座舱助手（吉利控股，实习）
这是我 2025.10—2025.12 在浙江吉利控股集团有限公司任 AI 应用开发实习生期间参与的项目。背景：解决传统车机交互僵化、难以处理复杂指令与开放问答的问题。目标：构建基于 LLM 的多 Agent 智能座舱助手，统一编排音乐、空调、座椅控制及车辆手册问答能力，实现复杂指令理解、精准工具调用、多轮记忆与安全低延迟交互。
技术栈：Python、LangChain、Agent、RAG、Qwen3-14B、Skill、ReAct、LoRA、Badcase、Ragas、BGE-Reranker。
1. 座舱 Agent 与记忆编排：基于 LangChain 与 ReAct 构建意图路由及音乐、空调、座椅、问答四类专用 Agent，将播放控制、温度/风量调节、座椅加热/通风/按摩等能力封装为 Skill；设计最近 10 轮短期记忆与长期偏好记忆，沉淀空调预设温度、座椅位置及常听歌单，通过滑动窗口压缩与关键信息抽取提升多轮交互一致性。
2. 车载知识 RAG 优化：面向车辆功能、语音指令及驾驶模式等产品手册，采用父子切块策略，构建 BM25 与 BGE-M3 的 RRF 混合检索链路，并通过 BGE-Reranker 精排；Ragas 评测中 Faithfulness 0.91、Answer Relevancy 0.88。
3. 模型微调与安全对齐：构建 5000 条座舱控制指令数据，基于 Qwen3-14B 完成 LoRA 微调；针对"座椅通风误识别为座椅加热"等 Bad Case，引入 DPO 对齐降低工具误调用与参数遗漏，意图识别准确率达到 90.2%，较基线提升约 8%；行车安全与合规偏好命中率达到 92.5%，降低过度座椅按摩、空调温度过低等不安全操作风险。
4. 端到端轨迹评测：建立模型、RAG 与 Agent 分层评测体系，持续监控意图路由、工具选择、参数提取、任务完成及执行时延；复杂联动场景引导成功率达到 91%，系统平均响应时长控制在 2 秒以内，满足车载交互的低时延要求。（口径：内部 NDA 验证。）""",

    # ------------------------------------------------------------------ #
    # 慧眼识蚁（国家级大创）                                             #
    # ------------------------------------------------------------------ #
    "anteye-robot.md": """# 慧眼识蚁——红火蚁智能追踪与靶向灭治装备（国家级大创项目）
这是我 2024.05—2025.05 主持的国家级大学生创新创业训练计划项目，作为本科生代表与机械与自动化院研究生合作研发"下位机实时控制、上位机视觉识别、云端数据分析"三级架构的自主巡检机器人。
1. 硬件架构设计：参与下位机方案设计，采用"核心板+底板"分层结构，完成器件选型、原理图绘制，预留主控拓展接口实现模块化复用；完成板卡焊接及示波器/万用表电路功能调试。
2. 实时系统与运动控制：移植 FreeRTOS，通过信号量、互斥锁、消息队列实现传感器采集、电机控制、姿态解算与避障任务的并发调度；基于 MPU6500 DMP 解算四元数，结合增量式编码器反馈与 PID 算法输出 PWM 占空比，实现直流减速电机闭环调速；配置独立看门狗，系统稳定运行 72 小时。
3. 感知与建图：驱动 RPLIDAR S2 激光雷达构建局部栅格地图，实现自主运动与动态避障；通过 SPI 将陀螺仪与雷达数据存入 W25Q64JV Flash 芯片。
4. 云端通信与系统联调：基于 EC800M 4G 模块通过 UART 与 MCU 通信，采用 MQTT 协议对接阿里云 IoT 平台，实现多模态传感器数据上行上报与云端指令下行交互；配合树莓派 4B 上位机完成 YOLOv5s 蚁巢识别模型联调，实现端云协同的多模态数据同步。
项目获国家级大创立项；对应挑战杯科技发明制作 A 类赛事路演资格。识别准确率 ≥95% 是申报书目标指标，不表述为已经实测达到。""",

    # ------------------------------------------------------------------ #
    # jianli（站点自身，保留问答）                                       #
    # ------------------------------------------------------------------ #
    "jianli-overview.md": """# Jianli AI 面试协作站｜从聊天入口到可靠业务闭环\n这是我独立开发、准备挂正式域名上线的求职产品。浏览器通过 React 19 页面调用 FastAPI：公开问题走 SSE，登录用户可持久化本人会话；知识库先按 page/project 域检索，模型只有在有依据时生成并返回引用。预约链路把邮箱验证码登录、动态 Slot、预览确认、并发创建、本人管理、管理员看板、邮件与飞书同步连在一起。数据层使用 SQLAlchemy/Alembic 0010、PostgreSQL 16 + pgvector 和 Redis 7，模型链路为 DeepSeek V4 Flash、BGE-M3 与可选Qwen3-Reranker-8B。核心设计是把概率模型限制在确定性边界内：证据门决定能否回答，服务端白名单与 RBAC 决定能否操作，数据库事务和 Outbox 决定副作用如何落地。""",

    "jianli-agent-rag.md": """# Jianli 受控 Agent 与混合 RAG｜检索词失败也不丢证据\n模型以 function calling 自主选择 search_knowledge 并生成检索词，但模型输出不被直接信任：服务端同时检索模型词和用户原问题，按文档与片段去重合并，避免模型改写失真把原始证据裁掉。每一路先做 1024 维 BGE-M3 向量 top10；若没有达到 0.47 的向量候选，即使BM25 有中文单字重叠也拒绝据此硬答。通过证据门后，BM25 top10 与向量结果用 RRF(k=60)融合为最多 12 条，再由可选 Cross-Encoder 排到 top6，并保持 page/project 域隔离。本地哈希 embedding 只是确定性离线 fallback；对照中 BGE-M3 纯向量 avg-rank 1.3，哈希为 1.8。回答流遵守 started→trace/delta→citations→completed；无依据返回 offtopic，不会让模型凭常识补齐个人经历。""",

    "jianli-agent-lab.md": """# Jianli Agent Lab｜模型负责规划，代码负责授权\n避免智能体乱调用不能只靠 Prompt：Agent 最多循环 4 步，只注册 search_knowledge、创建预约、查询本人预约、取消本人预约、改期本人预约五个工具；未知工具确定性拒绝。预约工具必须登录，面试官只能操作本人记录，所有写操作复用 BookingService 的校验、事务和审计，模型不能直接写库；管理员管理他人的能力走独立管理端服务边界，不因模型声称自己是管理员而放权。每轮工具结果作为结构化证据交回模型生成自然语言，检索工具则进入 RAG 引用链。页面预置依据问答、多步只读预约、越权攻击、无依据拒答四类真实挑战，调用同一 SSE 接口而非展示预制答案。answer.trace 只公开单调 step、固定 phase/status、白名单工具名、耗时和短标签；不含 Prompt、用户/知识原文、工具参数、完整结果或预约 PII，因此是可审计执行事实，不是模型思维链。""",

    "jianli-evaluation-ci.md": """# Jianli 评测中心与 CI 门禁\n评测中心读取版本化 JSON 报告，公开样本数、生成时间、verified commit、套件结果与脱敏边界案例，而不是运行时临时拼一个满分。当前报告为 79/79：Agent/Trace 22、RAG 事实一致性 38、Web 交付 1、Cross-Encoder 协议 4、语义缓存与 Provider 韧性 8、多副本共享熔断 6；真实 RAG 测试会上传 canonical corpus、分块、BGE-M3 embedding 入 pgvector，再验证命中、拒答、隐私和误拒。Agent Quality Gate 定义 backend-agent→rag-integration→web-delivery 三个串行 job，后两段分别带真实 PG/Redis和前端测试/typecheck/build。当前只有本地等价门禁证据，尚无远端 Actions run；79/79 也只是这组冻结检查全过，不等于生产准确率或线上可用性，所以不能说云端流水线已经跑绿。""",

    "jianli-observability.md": """# Jianli OpenTelemetry + Prometheus/Grafana\n显式开启后，ASGI 中间件从请求头提取 Trace 上下文，覆盖完整流式响应时长，并只记录method、规范化 route、status。AIQA 另有回答结果/耗时/token、工具结果、重排、语义缓存和LLM/Reranker 熔断指标与 Span event；工具名和状态均为有界标签，未知工具折叠为固定值。Prometheus 通过私网 /internal/metrics 暴露，Nginx 对公网返回 404；配置 OTLP 时批量导出OpenTelemetry，未配置则不外发。Grafana Agent Overview 有 10 个面板。问题、回答、Prompt、知识原文、PII、密钥、高基数 ID 和异常正文不进入观测属性。代码与自动化测试已验证，完整 Collector/Prometheus/Grafana 容器栈 smoke 尚未完成。""",

    "jianli-reranker.md": """# Jianli Reranker 对照实验\nCross-Encoder 只接收已经通过域过滤和相关性门槛的 RRF top12，不能扩大召回、跨项目取证或绕过拒答；Qwen3-Reranker-8B 返回排序索引与分数后，服务端再次校验数量、类型、重复和越界索引，最终取 top6。每次检索最多外调一次且超时上限 5 秒；超时、429/5xx、协议畸形或熔断都会 fail-open，完整保留原 RRF 顺序，而不是让问答一起失败。真实 provider 的 5 题组件对照为 MRR 0.3333→1.0000、Hit@1 0/5→5/5；样本很小，只能证明组件排序改善，不能外推端到端生产质量；79/79 版本化检查同样不是生产准确率。""",

    "jianli-reliability.md": """# Jianli 可靠业务闭环｜不是只会聊天的 Demo\n预约预览令牌绑定登录人和规范化表单、有效 3 分钟且不占 Slot；确认时在一个事务中锁公司与三个连续 30 分钟 Slot，检查状态后写 appointment、更新 Slot、Outbox 和审计；并发冲突映射为业务错误。改期同样先锁记录和新 Slot，再释放旧 Slot。Slot 竞争靠行锁和事务内复核；活动用户/公司部分唯一索引独立约束重复业务预约，不是所谓‘行锁失效兜底’。敏感字段用带表/列/记录 AAD 的 AES-256-GCM，去重只存 HMAC 指纹。过期 active 状态的预约由幂等 CTE 自动完成并取消旧提醒。Worker 用 FOR UPDATE SKIP LOCKED 抢 Outbox，投递是 at-least-once；delivery 唯一键防重复尝试行，但不能宣称外部邮件/飞书 exactly-once。\n匿名、无会话且无工具轨迹的 grounded 回答才可进入按页面/项目隔离的语义缓存，阈值 0.94、TTL 600 秒、最多 100 条且不存问题明文；知识增删会整体失效。LLM 与 Reranker 用 Redis Lua共享 closed/open/half-open 状态和单恢复探针，Redis 失联退回本地 breaker。真实 PG/Redis测试覆盖十轮抢 Slot、改期竞争、自动过期和跨实例熔断；正式域名、远端 CI 与完整观测栈smoke 仍是上线验收项。""",
}

_EXPECTED_DOC_COUNT = 23
if len(CANONICAL_CORPUS) != _EXPECTED_DOC_COUNT:
    raise RuntimeError(
        f"CANONICAL_CORPUS must have exactly {_EXPECTED_DOC_COUNT} documents, "
        f"got {len(CANONICAL_CORPUS)}. Update the count and the tests together."
    )
