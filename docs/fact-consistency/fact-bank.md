# 简历事实一致率 · 题库（FQ-01 … FQ-64）

> **事实源（ground truth）**：线上优先使用 `test_rag_eval.py` 的 canonical corpus；个人域由
> `profile.md`、`credentials.md`、`behavior-stories.md` 承载，项目域使用各项目分层文档。
> `content.py` 页面 chunks 是同源静态兜底。题库期望必须同时与 corpus 和静态兜底一致，
> 不允许用旧文档名或旧统计维持表面通过。
>
> **2026-09 知识库刷新（TASK-KB-RESUME-REFRESH-001）**：随新简历整体刷新——身份（姓名/学校/
> 手机/邮箱）不进入公开问答；泰益智岗位与时间更新（2026.01—2026.08，AI 应用开发工程师），
> 新增吉利极氪、MCP 数据分析引擎、慧眼识蚁硬件细节；NDA 约束项目的量化指标一律带「口径说明」
> （内部验证、可追问、不公开原始证据），不再展开内部审计级细节。
>
> **检索域（scope）**：每题标注 `page_key` / `project_key`，与 `measure_fact_consistency.py`
> 一一对应。检索按 page 隔离，域标错会误拒（详见脚本说明）。
>
> **判定口径**：见 `rubric.md`。一致率 = ✅数 ÷ 题库总数（测量运行 38 题：FQ-01~38）；SLO ≥94%
> 下需 ✅ ≥ 36（即最多 2 题 ❌/🚫）。FQ-39+ 为「源码级追问」参考题库，不进测量运行。

---

## A 组 · 简历域（page_key=`resume`，不传 project_key）

### FQ-01 · 你主要是什么技术方向的工程师？
- **期望事实**：AI 应用开发工程师。
- **溯源**：R0「我是一名 AI 应用开发工程师，22 岁，现居深圳南山，可立即到岗」。
- **判定要点**：答"AI 应用开发 / AI 应用"均算 ✅；答"AI 全栈""后端与平台"为 ❌（旧口径，已随新简历更新）。

### FQ-02 · 你平时重点关注哪些技术领域？
- **期望事实**：业务落地的 AI Agent 工程、RAG 与云边端系统。
- **溯源**：R0「聚焦业务落地的 AI Agent 工程，具备 Agent Runtime、MCP 工具协议、RAG 工程化及 AIoT 设备协同实践」。
- **判定要点**：包含"AI Agent / RAG / 云边端"中两项以上核心词或合理复述即 ✅；只答旧"高并发/数据建模/开发者体验"且未提 Agent/RAG ⚠️（旧口径）。

### FQ-03 · 你做过哪些类型的系统后端架构？
- **期望事实**：预约与协作类系统。
- **溯源**：R10「曾负责预约与协作类系统的后端架构」（content.py resume_chunks）。
- **判定要点**：点出"预约 / 协作类系统"即 ✅；完全未提 ❌。

### FQ-04 · 你在预约系统里落地过哪些关键设计？
- **期望事实**：插槽快照、实时刷新、幂等写入。
- **溯源**：R10「落地过插槽快照、实时刷新与幂等写入」。
- **判定要点**：三项至少命中两项 ✅；一项或零项 ⚠️/❌（视是否引入错误事实）。

### FQ-05 · 你的工程方法论是什么？
- **期望事实**：先设计后编码。
- **溯源**：R7「我偏好先设计后编码」。
- **判定要点**：明确"先设计后编码" ✅；答"边写边改"等冲突 ❌。

### FQ-06 · 你做工程时特别看重什么？
- **期望事实**：可观测性、可演进性、契约测试。
- **溯源**：R7「重视可观测性、可演进性与契约测试」。
- **判定要点**：三项中命中主体（可观测 / 可演进 / 契约测试）即 ✅；答成"越快越好"等冲突 ❌。

### FQ-07 · 你的主要技术栈有哪些？
- **期望事实**：Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、LangGraph / Temporal、MCP、Kafka / Flink / ClickHouse。
- **溯源**：R6「Python / FastAPI、NestJS、PostgreSQL、Redis、TypeScript、React、LangGraph / Temporal、MCP、Kafka / Flink / ClickHouse」。
- **判定要点**：命中 Python/FastAPI + Postgres + Redis + TS/React 主体 ✅；明显错列（如声称以 Java/Go 为主栈）❌。

### FQ-08 · 你熟悉哪些 AI 问答相关技术？
- **期望事实**：RAG 与人格层问答、受约束的 AI Agent 编排。
- **溯源**：R6「熟悉 RAG 与人格层问答、受约束的 AI Agent 编排（工具白名单 + RBAC + 预算熔断 + HITL 审批）」。
- **判定要点**：点出 RAG + 人格层 / 受约束 Agent 编排 ✅；只说 RAG 未提人格层 ⚠️；说成"自研大模型"等无依据 ❌。

### FQ-09 · 除了后端架构，你还做过什么方向的功能？
- **期望事实**：内容问答与检索相关功能。
- **溯源**：R10「也做过内容问答与检索相关功能」。
- **判定要点**：点出"内容问答 / 检索"即 ✅；完全未提 ❌。

### FQ-10 · 你做的这个站点本质是用来做什么的？
- **期望事实**：本人的数字分身，回答关于"我经历"的问题并承接面试预约。
- **溯源**：R9「我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约」。
- **判定要点**：命中"数字分身 + 回答经历问题 + 承接面试预约" ✅；只答其一不冲突 ⚠️。

---

## B 组 · jianli 项目域（page_key=`projects`，project_key=`jianli`）

### FQ-11 · jianli 这个项目是做什么的？
- **期望事实**：面向正式上线的 AI 面试协作站；把简历/项目 RAG 问答、登录注册、会话、动态时段、预约管理、邮件与飞书通知做成一条可验证产品链。
- **溯源**：CORPUS `jianli-overview.md`。
- **判定要点**：点出"个人 AI 问答网站 + 三件套产品链" ✅；只答"问答网站"不冲突 ⚠️；答成"别人的产品"❌。

### FQ-12 · jianli 处理越界或无依据问题的原则是什么？
- **期望事实**：真实性优先，越界或无依据问题一律拒答，绝不编造经历。
- **溯源**：CORPUS `jianli-overview.md`「把概率模型限制在确定性边界内：证据门决定能否回答」。
- **判定要点**：命中"真实性优先 / 一律拒答 / 不编造" ✅；答成"会尽量编一个"❌。

### FQ-13 · jianli 的后端技术栈是什么？
- **期望事实**：FastAPI + SQLAlchemy + Alembic（迁移已到 0010）+ PostgreSQL 16 + pgvector + Redis 7；前端 React 19，LLM/embedding 为 DeepSeek V4 Flash + BGE-M3。
- **溯源**：CORPUS `jianli-overview.md`。
- **判定要点**：命中 FastAPI + Alembic 0010 + PG16/pgvector + Redis7 主体 ✅；说成 MySQL 或仍停在 0007 ❌。

### FQ-14 · jianli 用什么模型和 embedding？
- **期望事实**：LLM 用 DeepSeek V4 Flash（chat）；embedding 用硅基流动 BGE-M3（1024 维）。
- **溯源**：CORPUS `jianli-overview.md` / `jianli-agent-rag.md`。
- **判定要点**：命中 DeepSeek V4 Flash + BGE-M3(1024 维) ✅；说成 GPT/Claude 主模型 ❌。

### FQ-15 · jianli 的检索是怎么做的？
- **期望事实**：向量 top10 + BM25 top10 经 RRF 融合最多 12 个候选，可选 Cross-Encoder 重排后取 top6。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"向量 + BM25 + RRF top12 + 可选重排 top6" ✅；只说向量检索或把 Cross-Encoder 说成召回层 ❌。

### FQ-16 · jianli 把 embedding 换成 BGE-M3 后检索质量有什么变化？
- **期望事实**：纯向量层 avg-rank 从本地哈希的 1.8 降到 BGE-M3 的 1.3。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"1.3（BGE-M3）vs 1.8（本地哈希）且 BGE-M3 更优" ✅；数值颠倒或说反 ❌。

### FQ-17 · jianli 怎么判断一个问题该拒答？
- **期望事实**：双层门槛：① 知识库向量相关性阈值 0.47；② 静态检索加 CJK 停用词过滤（功能字不参与重叠计数）。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"0.47 阈值 + CJK 停用词双层" ✅；只说阈值 ⚠️；说成"完全不拒答"❌。

### FQ-18 · jianli 的拒答率现在是多少？
- **期望事实**：从 0% 提升到 100%（评测 REJECT 10/10）。
- **溯源**：CORPUS `jianli-agent-rag.md` / `test_rag_eval.py` REJECT_CASES。
- **判定要点**：命中"拒答率 100%（REJECT 10/10）" ✅；说"拒答率 0%"❌（那是修复前的基线）。

### FQ-19 · jianli 的 Agent 能调用哪些工具？
- **期望事实**：五个白名单工具：`search_knowledge`、`request_interview_booking`、`list_my_appointments`、`cancel_appointment`、`reschedule_appointment`；面试官只管理本人，owner_admin 才能管理他人，写操作复用 BookingService，MAX_STEPS=4。
- **溯源**：CORPUS `jianli-agent-rag.md` / `docs/baseline.yml agent_tools`。
- **判定要点**：命中五工具 + 本人/管理员 RBAC + BookingService 复用 ✅；说 Agent 可直接写数据库、导出他人信息或调用白名单外工具 ❌。

### FQ-20 · jianli 的 Agent 是怎么决定要不要检索的？
- **期望事实**：模型通过 function calling（`tool_choice=auto`）自主决策是否检索并生成检索词。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"function calling / tool_choice=auto 模型自主决策" ✅；说成"硬编码固定检索词"❌。

### FQ-21 · jianli 用什么来量化检索质量？
- **期望事实**：`tests/aiqa/test_rag_eval.py` 将 canonical corpus 真实上传、分块、embedding 入库，再通过混合检索与 `streamAnswer` 验证命中、拒答、隐私和误拒，不是只测一个 mock scorer。
- **溯源**：CORPUS `jianli-evaluation-ci.md` + `tests/aiqa/test_rag_eval.py`。
- **判定要点**：命中"test_rag_eval.py + 真实语料全链路" ✅；说"没有评测"❌。

### FQ-22 · jianli 的检索评测达到了什么水平？
- **期望事实**：当前版本化报告中 RAG 事实一致性 38/38；越界集 10/10 拒答。整体报告为 79/79，但样本规模有限，不能等同生产质量。
- **溯源**：CORPUS `jianli-evaluation-ci.md`。
- **判定要点**：命中 38/38 + 10/10 + 有限样本边界 ✅；把整体 79/79 说成 79 条全是 RAG 问题或生产准确率 100% ❌。

### FQ-23 · jianli 的预约业务闭环有哪些关键保障？
- **期望事实**：Slot 快照与并发锁、3 分钟预览不预占、原子创建、字段级 AES-256-GCM 加密、Outbox 通知、审计日志、SSE 恢复契约。
- **溯源**：CORPUS `jianli-reliability.md`。
- **判定要点**：命中 4 项以上关键保障 ✅；只答"有加密"⚠️；说成"无加密明文存储"❌。

### FQ-24 · jianli 的集成测试情况如何？
- **期望事实**：当前公开版本化证据合计 79/79，覆盖 Agent/Trace 22、RAG 事实 38、Web 1、Reranker 协议 4、缓存/Provider 韧性 8、多副本熔断 6；GitHub 三作业已完成本地等价门禁，但远端 run 尚待授权 push。
- **溯源**：CORPUS `jianli-evaluation-ci.md`。
- **判定要点**：命中 79/79 的分组含义 + 远端未跑边界 ✅；说远端 GitHub Actions 已绿或把它说成 79 条端到端生产测试 ❌。

### FQ-25 · jianli 的 embedding 经历过什么演进？
- **期望事实**：从本地哈希（无语义）换成 BGE-M3。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"本地哈希 → BGE-M3，哈希无语义" ✅；说反方向 ❌。

### FQ-26 · jianli 开发中有过什么值得记录的坑？
- **期望事实**：Agent 模型自主决策上线后评测一度 8/8→6/8，根因是 greeting 判定里 'hi' 子串误匹配 'litchi'，改整词匹配修复。
- **溯源**：CORPUS `jianli-reliability.md` / `persona.py` `_HI_RE`。
- **判定要点**：命中"greeting 'hi'⊂'litchi' 子串误匹配、改整词匹配" ✅；说成"没有任何坑"❌。

---

## C 组 · Litchi 毕设域（page_key=`projects`，project_key=`litchi`）

### FQ-27 · litchi 毕设用了什么技术栈？
- **期望事实**：本人独立完成的 2026 届优秀毕设（2025.06—2026.05），B2B2C 荔枝农技协同平台；Spring Boot 3.2 / Java 17 后端 + Vue3 / TypeScript 前端 + Python 诊断服务 + MySQL，AI 链路使用 Milvus、Neo4j、Ollama/vLLM/OpenAI-compatible API。数据平台、可观测性和容器编排属于实验模板，不表述为生产部署。
- **溯源**：CORPUS `litchi-overview.md` / content.py litchi chunk。
- **判定要点**：命中"独立开发 + 优秀毕设 + B2B2C + Spring Boot/Vue3 + Milvus/Neo4j + 模板边界" ✅；说成 FastAPI/React 主栈或模板已生产化 ❌。

### FQ-28 · litchi 的受控 Agent 是怎么实现的？
- **期望事实**：Planner–Guard–Executor–Synthesizer 受约束编排器，接入果园上下文、知识检索、知识图谱、方案推荐、待审批方案 5 类工具；最多 4 步规划、RBAC 权限过滤、未知/重复工具拦截、参数校验及轨迹记录，覆盖创建/规划/执行/等待审批/完成/失败/取消 7 类状态；写操作 HITL（生成预览→暂停审批→确认→落库）。当前同一技术员可发起并确认，不宣称双人复核。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中四段编排 + 5 工具 + 4 步 + 7 状态 + HITL + 单人确认边界 ✅；说成"纯聊天壳"或"双人复核已落地"❌。

### FQ-29 · litchi 的 LLM 和向量是怎么选的？
- **期望事实**：LLM 走 Ollama/vLLM/OpenAI-compatible API（本地可演示）；RAG 用 1024 维哈希向量（Milvus COSINE）+ 词法召回混合检索，哈希向量是 CPU 本地演示方案，不是语义 embedding。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中"哈希向量 + 词法混合 + 非语义 embedding" ✅；说成"云端大模型 + BGE-M3 语义向量"❌（那是泰益智/jianli）。

### FQ-30 · litchi 的并发压测结果如何？
- **期望事实**：历史 50 并发/50 请求本地测试全部成功（平均约 6.9s、P95 约 11.2s）；后续 100 并发/200 请求多轮成功率约 50.5%/21%/19%，高并发稳定性未达目标，需继续优化。
- **溯源**：CORPUS `litchi-evidence-retrospective.md`。
- **判定要点**：同时命中"50 并发历史成功 + 高并发未达标" ✅；只说"50 并发 100% 所以生产可用"或把 19% 说成"200 并发"❌。

---

## D 组 · Sleep 泰益智域（page_key=`projects`，project_key=`sleep`；TASK-KB-RESUME-REFRESH-001 重写）

### FQ-31 · 泰益智睡眠 AI Agent 平台怎么做的？
- **期望事实**：2026.01—2026.08 在泰益智任 AI 应用开发工程师参与的核心项目。基于 LangGraph + Temporal 构建统一 Agent Runtime，落地 5 类业务 Agent 与 Planner-Executor-Validator 多智能体协作，依托 PostgreSQL 实现长任务断点恢复；落地工具白名单、HITL 人工审批与超时熔断，集成 Prometheus+Grafana 全链路监控。（口径：内部 NDA 验证，可追问、不公开原始证据。）
- **溯源**：CORPUS `sleep-overview.md` / `sleep-agent-runtime.md` / content.py sleep chunk。
- **判定要点**：命中"LangGraph+Temporal 统一 Runtime + 5 类 Agent + Planner-Executor-Validator + PostgreSQL 断点恢复 + 白名单/HITL/熔断" ✅；说成"模型自己保证安全"或"没有运行时"❌。

### FQ-32 · 泰益智睡眠平台的核心指标如何？
- **期望事实**：构建 OpenAI 兼容模型网关（结构化输出、限流降级、熔断、Token 成本统计），对接 SSO/OIDC 落地细粒度 RBAC；基于 pgvector 实现租户级知识隔离与分层记忆；经 QLoRA 微调与 DPO 对齐后工具调用准确率提升至 92.0%，非法调用率降至 4.1%；三层 Agent 评测体系 80+ 工程回归用例通过率超 99%。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `sleep-rag-governance.md` / `sleep-evidence-retrospective.md`。
- **判定要点**：命中"92.0% / 4.1% / 99%"+ NDA 口径说明 ✅；说成旧口径"吞吐 +393.9%/P95 228ms/84 例/120 红队"❌（旧口径已废弃）。

### FQ-33 · 泰益智睡眠平台的数据链路怎么做？
- **期望事实**：搭建 MQTT→Kafka→ClickHouse 端到端遥测链路，实现多源设备数据实时接入、幂等去重与时序存储；通过消息重试、显式 Offset 提交与死信队列保障数据可靠性，故障恢复中位数约 13 秒。（口径：内部 NDA 验证，本地双进程/单 Kafka/单 ClickHouse 环境。）
- **溯源**：CORPUS `sleep-data-reliability.md`。
- **判定要点**：命中"MQTT→Kafka→ClickHouse + 幂等去重 + 13 秒 + NDA 口径" ✅；说成"完全不用消息队列"或旧"51 条重复/6,240 事件/12.6s"❌。

---

## E 组 · 行为/动机/竞赛（page_key=`resume`；慧眼识蚁题 page_key=`projects`）

### FQ-34 · 你在泰益智是怎么带人的？
- **期望事实**：方式 = 1 对 1 实操演示 → 布置任务 + 验收 → 不停改版迭代；实习中帮同事上手新工具与消息链路；设计与既有组件体系冲突时先列转换成本清单对齐、先还原核心页再迭代。
- **溯源**：CORPUS `behavior-stories.md`。
- **判定要点**：命中"1 对 1 实操→任务+验收→改版"或"先还原核心页" ✅；说"没带过人"❌。

### FQ-35 · 你工程上最大的教训是什么？
- **期望事实**：① 配置漂移要靠确定性评测暴露；② 静默错误——"错误不报 ≠ 没问题、对每个探针结果做语义核验"（ClickHouse 静默空结果）；③ 性能修复到时间边界仍未达标时应登记风险而不是修改口径。
- **溯源**：CORPUS `behavior-stories.md`。
- **判定要点**：命中任意一条核心教训 ✅；说"没什么教训"❌。

### FQ-36 · 你的求职动机和职业规划是什么？
- **期望事实**：科班 + 2023 年起用 AI 工具编程 → 泰益智从 0 做项目、从架构角度思考工程 → AI 应用开发工程师方向；意向深圳南山（AI 产业密集）；选公司看重更大平台；5 年目标一步步往架构师方向走；把文档/契约/评测/门禁都当作交付物，让接手的人无缝上手。
- **溯源**：CORPUS `behavior-stories.md` / `profile.md`。
- **判定要点**：命中"2023 起 AI 编程 / AI 应用开发 / 深圳南山 / 架构师 / 可交接"至少两项 ✅；说成"没有规划"❌；说成"AI 全栈"⚠️（旧口径）。

### FQ-37 · 慧眼识蚁项目是做什么的？
- **期望事实**：国家级大创项目（2024.05—2025.05，主持），与机械与自动化院研究生合作研发"下位机实时控制、上位机视觉识别、云端数据分析"三级架构的自主巡检机器人：下位机 FreeRTOS 实时调度（信号量/互斥锁/消息队列）、MPU6500 DMP 四元数 + PID 闭环调速、RPLIDAR S2 栅格地图、EC800M 4G + MQTT 阿里云 IoT、树莓派 4B + YOLOv5s 蚁巢识别。
- **溯源**：CORPUS `anteye-robot.md`。
- **判定要点**：命中"红火蚁 + 三级架构 + FreeRTOS/MPU6500/PID/RPLIDAR/EC800M/YOLOv5s 任一项" ✅；说成"与蚂蚁无关"❌。

### FQ-38 · 慧眼识蚁做到了什么程度？
- **期望事实**：国家级大创立项（第一负责人）；对应挑战杯科技发明制作 A 类赛事路演资格；识别准确率 ≥95% 为申报书目标指标（非必达实测数字）；相关知识产权归属课题依托单位。
- **溯源**：CORPUS `anteye-robot.md` / `credentials.md`。
- **判定要点**：命中"大创立项 + 挑战杯 A 类 + ≥95% 目标口径" ✅；把 ≥95% 说成"实测已达成"⚠️；披露申报号或学校 ❌（身份隐藏原则）。

---

## 扩展 · 源码级追问（不进 38 题测量运行）

### C 组延伸 · litchi（FQ-39~43、59~61）

### FQ-39 · litchi 为什么不信任 Planner 直接调用工具？
- **期望事实**：Planner 只产出候选计划；服务端 Guard 再按 RBAC、未知/重复工具、参数校验和最多 4 步过滤，Executor 只执行过滤后的计划。模型输出是非可信输入，权限与预算必须由确定性代码执行。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中"模型计划非可信 + 服务端二次校验" ✅；说"模型自己保证不越权"❌。

### FQ-40 · litchi 的 RAG 摄入和检索链路是什么？
- **期望事实**：6 类文档格式 → 480 字符 Chunk + 120 Overlap 切块 → 1024 维哈希向量（Milvus COSINE）+ 词法召回混合检索 → 标题/来源/关键词去重重排 → Neo4j 关系查询；外部模型不可用时 20 次降级问答平均响应 159.88ms。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：能说明哈希向量是 CPU 离线取舍而非语义 embedding ✅；宣称 BGE/BM25-RRF 或高级 reranker 已实现 ❌。

### FQ-41 · litchi 为什么有持久化仍不是事务 Outbox？
- **期望事实**：当前 run、step、approval、业务写入与 outbox 未处于同一可恢复事务状态机，状态以内存为主并可写 MySQL JSON 快照，执行中的 steps 不逐步持久化；SSE 事件进程内、前端主要轮询。
- **溯源**：CORPUS `litchi-evolution.md`。
- **判定要点**：命中"同事务原子写入缺失" ✅；仅以"有快照表"证明可靠投递 ❌。

### FQ-42 · litchi 的 SSE、取消和恢复做到什么程度？
- **期望事实**：后端提供状态 SSE，但事件在进程内、前端主要轮询，没有 Last-Event-ID 持久重放；cancel 只改状态，不能中断已发出的依赖调用；执行 steps 不逐步持久化。
- **溯源**：CORPUS `litchi-evolution.md` / `litchi-agent-rag.md`。
- **判定要点**：主动说明"端点存在不等于断线恢复" ✅；宣称流式 Token 输出或多实例恢复已完成 ❌。

### FQ-43 · litchi 的评测集结构是什么？
- **期望事实**：60 条固定评测集 = 30 RAG + 20 Agent + 10 安全，覆盖召回、工具选择、越权与拒答；补充 Prometheus 指标（运行次数/耗时/调用次数），搭建 5 类 CI 任务，k6 压测识别异步线程池与快照持久化优化方向。
- **溯源**：CORPUS `litchi-evidence-retrospective.md` / `litchi-agent-rag.md`。
- **判定要点**：命中"60 条 = 30 RAG + 20 Agent + 10 安全 + Prometheus + 5 类 CI + k6" ✅；说成"没有评测"❌。

### FQ-59 · litchi 的 RAG 降级如何做？
- **期望事实**：外部模型不可用时走确定性降级，20 次降级问答平均响应 159.88ms；降级路径仍可能参考文件名提示或数据集原型，但会用 engine/demoMode 明示，只有 ultralytics-yolo 且 demoMode=false 才算真实模型推理。
- **溯源**：CORPUS `litchi-agent-rag.md` / `litchi-evidence-retrospective.md`。
- **判定要点**：命中"降级可解释 + engine/demoMode 边界" ✅；把降级结果混称为模型真实能力 ❌。

### FQ-61 · litchi 图像识别的 93.75% 能代表真实果园吗？
- **期望事实**：不能。原始 11 类 27,594 张图片只抽取五类均衡子集，300 张训练、80 张验证；最佳 Top-1 93.75%、末轮 91.25%。小验证集波动明显，只证明五分类实验链路，不能外推真实果园；≥95% 是申报目标指标。
- **溯源**：CORPUS `litchi-evidence-retrospective.md`。
- **判定要点**：命中"300/80 + 最佳/末轮区别 + 小验证集边界" ✅；表述为真实田间准确率 93.75% ❌。

### D 组延伸 · Sleep / MCP（FQ-44~50、62）

### FQ-44 · Sleep 的 Agent Runtime 有什么设计？
- **期望事实**：LangGraph + Temporal 统一 Agent Runtime，5 类业务 Agent，Planner-Executor-Validator 多智能体协作，依托 PostgreSQL 长任务断点恢复；工具白名单、HITL 审批与超时熔断，Prometheus+Grafana 全链路监控。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `sleep-agent-runtime.md`。
- **判定要点**：命中"统一 Runtime + 5 类 Agent + Planner-Executor-Validator + 断点恢复 + 白名单/HITL/熔断" ✅；说成"没有运行时"或"生产级 Temporal 中断已证"❌。

### FQ-45 · Sleep 的模型与工具治理怎么做？
- **期望事实**：OpenAI 兼容模型网关（多基座、结构化输出、限流降级、熔断、Token 成本统计），SSO/OIDC + 细粒度 RBAC，pgvector 租户级知识隔离与分层记忆；QLoRA + DPO 对齐后工具调用准确率 92.0%、非法调用率 4.1%。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `sleep-rag-governance.md`。
- **判定要点**：命中"网关 + RBAC + 租户隔离 + 92.0%/4.1%" ✅；说"未做权限控制"❌。

### FQ-46 · Sleep 的数据链路可靠性怎么保障？
- **期望事实**：MQTT→Kafka→ClickHouse 端到端遥测链路，多源设备实时接入、幂等去重与时序存储；消息重试、显式 Offset 提交与死信队列，故障恢复中位数约 13 秒。（口径：内部 NDA 验证，本地双进程/单 Kafka/单 ClickHouse。）
- **溯源**：CORPUS `sleep-data-reliability.md`。
- **判定要点**：命中"MQTT→Kafka→ClickHouse + 幂等去重 + 13 秒 + 本地边界" ✅；说成"生产 HA 已证"❌。

### FQ-47 · Sleep 的 Harness 评测怎么做的？
- **期望事实**：单元测试、场景回归、语义校验三层 Agent 评测体系，覆盖功能、异常与安全场景，80+ 工程回归用例通过率超 99%；基于 Harness 搭建 CI/CD 发布治理流水线，集成代码扫描、依赖校验、容器镜像检测与 Agent 自动化评测门禁。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `sleep-evidence-retrospective.md`。
- **判定要点**：命中"三层评测 + 80+ 回归 >99% + CI/CD 门禁 + NDA 口径" ✅；说成旧"84 例/11 groups/120 红队"❌。

### FQ-48 · Sleep 的边界与演进是什么？
- **期望事实**：历史阿里云基础设施与数据库迁移跑通过，但应用曾因启动与扩展能力问题失败，候选未重新部署，因此不表述为生产上线或 staging 成功；下一版聚焦事务 Outbox、服务身份、可信设备归属、持久执行、请求幂等与中断演练。
- **溯源**：CORPUS `sleep-evolution.md`。
- **判定要点**：命中"不表述生产上线 + 下一版方案清单" ✅；说"staging/生产上线成功"❌。

### FQ-49 · MCP 智能数据分析引擎是做什么的？
- **期望事实**：泰益智期间参与的电商查数项目（面向电商运营查数、统计、预测及可视化），基于 LangGraph 构建"意图分类—SQL/Python 生成—SQL 校验—任务执行—结果解释"状态驱动工作流，通过 MCP-Server 标准化封装并调度 SQL、Python 分析能力；整体分析效率提升约 60%，人工参与减少 50% 以上。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `mcp-analytics-engine.md`。
- **判定要点**：命中"MCP-Server + LangGraph 意图分类 + NL2SQL/NL2Python + 60%/50% + NDA 口径" ✅；说成"纯模板项目"❌。

### FQ-50 · MCP 怎么控制 NL2SQL 幻觉？
- **期望事实**：NL2SQL 与 NL2Python 双 MCP-Server；业务词典、表结构、字段说明及 Few-shot 样例向量化存入 Chroma；表字段白名单、结构化输出校验及错误反馈重试机制，将 NL2SQL 幻觉率控制在 5% 以下；Redis Bitmap 维护大文件分片状态（1000 分片 125 字节）+ Redisson + MinIO 断点续传，平均响应时间降低约 40%。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `mcp-analytics-engine.md`。
- **判定要点**：命中"双引擎 + Chroma 向量化 + 白名单/校验/重试 + 幻觉率 <5% + 125 字节/40%" ✅；说成"不做校验"❌。

### FQ-62 · 极氪智能座舱助手是做什么的？
- **期望事实**：吉利控股（2025.10—2025.12，AI 应用开发实习生）项目：基于 LangChain 与 ReAct 构建意图路由及音乐、空调、座椅、问答四类专用 Agent，将播放控制、温度/风量调节、座椅加热/通风/按摩等封装为 Skill；10 轮短期记忆 + 长期偏好记忆。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `zeekr-cockpit-assistant.md`。
- **判定要点**：命中"极氪座舱 + 四类 Agent + Skill 封装 + 10 轮短记忆/长期偏好 + NDA 口径" ✅；说成"纯问答壳"❌。

### FQ-63 · 极氪项目的 RAG 与微调做了什么？
- **期望事实**：车载知识 RAG 用父子切块 + BM25 与 BGE-M3 RRF 混合检索 + BGE-Reranker 精排，Ragas Faithfulness 0.91、Answer Relevancy 0.88；5000 条座舱指令数据基于 Qwen3-14B LoRA 微调 + DPO 对齐，意图识别 90.2%（+8%）、行车安全与合规偏好命中 92.5%；复杂联动引导成功率 91%、平均响应 2 秒内。（口径：内部 NDA 验证。）
- **溯源**：CORPUS `zeekr-cockpit-assistant.md`。
- **判定要点**：命中"父子切块 + RRF + Reranker + 0.91/0.88 + 90.2%/92.5%/91% + NDA 口径" ✅；数值说反或缺失 NDA 口径 ⚠️。

### FQ-64 · 慧眼识蚁的硬件细节是什么？
- **期望事实**：下位机"核心板+底板"分层结构、器件选型与原理图绘制、板卡焊接与示波器/万用表调试；FreeRTOS 信号量/互斥锁/消息队列并发调度；MPU6500 DMP 四元数 + 增量式编码器反馈 + PID 输出 PWM 闭环调速；看门狗 72h；RPLIDAR S2 栅格地图；SPI 存 W25Q64JV Flash；EC800M 4G + MQTT 阿里云 IoT；树莓派 4B + YOLOv5s 蚁巢识别。
- **溯源**：CORPUS `anteye-robot.md`。
- **判定要点**：命中"核心板+底板 / FreeRTOS / MPU6500+PID / RPLIDAR / EC800M+MQTT / YOLOv5s"任二项 ✅；编造未提硬件 ❌。

---

## 备注
- **覆盖项**：个人教育、能力、证书、行为故事进入 canonical profile 文档；B 组 Jianli FQ-11~26 + 追问 FQ-51~58；C 组 litchi FQ-27~30 + 追问 FQ-39~43、59~61；D 组 sleep FQ-31~33 + 追问 FQ-44~48；MCP FQ-49~50；zeekr FQ-62~63；慧眼识蚁 FQ-37~38、FQ-64。canonical 文档共 23 篇。
- **身份规则（2026-09）**：公开语料与问答输出不出现真实姓名、学校、手机号、个人邮箱与可反查学校的专利申报号；公司名与项目名保留。
- **口径规则（2026-09）**：NDA 约束项目的量化指标带「口径说明」（内部验证、可追问、不公开原始证据），不再展开内部审计级细节；旧口径指标（吞吐 +393.9%、P95 1347.73→228.85ms、84/84、120 红队 96/120、90.4 分等）已随新简历废弃。
- **漂移风险**：若 `content.py` chunk 文本变更，本题库期望事实须同步修订，否则一致率失真。修订须走内容变更流程，不可静默改期望值凑分。
- **题库口径变更（2026-09-04）**：测量运行保持 38 题（FQ-01~38），SLO ≥94% 不变，38 题下需 ✅ ≥ 36；新增源码级追问 FQ-62~64。
