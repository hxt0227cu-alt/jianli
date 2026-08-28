# 简历事实一致率 · 题库（FQ-01 … FQ-61）

> **事实源（ground truth）**：线上优先使用 `test_rag_eval.py` 的 canonical corpus；个人域由
> `profile.md`、`credentials.md`、`behavior-stories.md` 承载，项目域使用各项目分层文档。
> `content.py` 页面 chunks 是同源静态兜底。题库期望必须同时与 corpus 和静态兜底一致，
> 不允许用旧文档名或旧统计维持表面通过。
>
> **检索域（scope）**：每题标注 `page_key` / `project_key`，与 `measure_fact_consistency.py`
> 一一对应。检索按 page 隔离，域标错会误拒（详见脚本说明）。
>
> **对齐意图**：26 题对应北极星「简历事实一致率 ≥ 94%」（SLO 目标，非已测值），
> 设计上并行于需求 R1–R26 的覆盖意图，但本题库以 content.py chunk 为唯一事实锚点，
> 不反向依赖 PRD 文本。
>
> **判定口径**：见 `rubric.md`。一致率 = ✅数 ÷ 题库总数（现 38）；SLO ≥94% 下需 ✅ ≥ 36（即最多 2 题 ❌/🚫）。

---

## A 组 · 简历域（page_key=`resume`，不传 project_key）

### FQ-01 · 你主要是什么技术方向的工程师？
- **期望事实**：后端与平台方向工程师。
- **溯源**：R0「我是一名后端与平台方向的工程师」。
- **判定要点**：答"后端 / 平台 / 后端与平台"均算 ✅；答成"前端""算法"等冲突为 ❌。

### FQ-02 · 你平时重点关注哪些技术领域？
- **期望事实**：高并发服务、数据建模、开发者体验。
- **溯源**：R0「关注高并发服务、数据建模与开发者体验」。
- **判定要点**：包含上述三项核心词或合理复述即 ✅；只答其一不冲突（⚠️ 视宽松口径）；答成无关领域 ❌。

### FQ-03 · 你做过哪些类型的系统后端架构？
- **期望事实**：预约与协作类系统。
- **溯源**：R6「曾负责预约与协作类系统的后端架构」（content.py resume_chunks 新增可检索块，TASK-AIQA-FACTCOVERAGE-013）。
- **判定要点**：点出"预约 / 协作类系统"即 ✅；完全未提 ❌。

### FQ-04 · 你在预约系统里落地过哪些关键设计？
- **期望事实**：插槽快照、实时刷新、幂等写入。
- **溯源**：R6「落地过插槽快照、实时刷新与幂等写入」。
- **判定要点**：三项至少命中两项 ✅；一项或零项 ⚠️/❌（视是否引入错误事实）。

### FQ-05 · 你的工程方法论是什么？
- **期望事实**：先设计后编码。
- **溯源**：R2「我偏好先设计后编码」。
- **判定要点**：明确"先设计后编码" ✅；答"边写边改"等冲突 ❌。

### FQ-06 · 你做工程时特别看重什么？
- **期望事实**：可观测性、可演进性、契约测试。
- **溯源**：R2「重视可观测性、可演进性与契约测试」。
- **判定要点**：三项中命中主体（可观测 / 可演进 / 契约测试）即 ✅；答成"越快越好"等冲突 ❌。

### FQ-07 · 你的主要技术栈有哪些？
- **期望事实**：Python / FastAPI、PostgreSQL、Redis、TypeScript、React。
- **溯源**：R3「Python / FastAPI、PostgreSQL、Redis、TypeScript、React」。
- **判定要点**：命中 Python/FastAPI + Postgres + Redis + TS + React 主体 ✅；明显错列（如声称 Java/Go 为主栈）❌。

### FQ-08 · 你熟悉哪些 AI 问答相关技术？
- **期望事实**：RAG 与人格层问答。
- **溯源**：R3「熟悉 RAG 与人格层问答」（content.py resume_chunks R3，TASK-AIQA-FACTCOVERAGE-013）。
- **判定要点**：点出 RAG + 人格层 ✅；只说 RAG 未提人格层 ⚠️；说成"自研大模型"等无依据 ❌。

### FQ-09 · 除了后端架构，你还做过什么方向的功能？
- **期望事实**：内容问答与检索相关功能。
- **溯源**：R6「也做过内容问答与检索相关功能」。
- **判定要点**：点出"内容问答 / 检索"即 ✅；完全未提 ❌。

### FQ-10 · 你做的这个站点本质是用来做什么的？
- **期望事实**：本人的数字分身，回答关于"我经历"的问题并承接面试预约。
- **溯源**：R5（TASK-AIQA-GROUNDING-001 新增 resume chunk）「我做的这个站点是我本人的数字分身，用来回答关于我经历的问题，并承接面试预约。」（原仅存于 `resume_sections`，不进检索；现已补入 chunk 使可检索）。
- **判定要点**：命中"数字分身 + 回答经历问题 + 承接面试预约" ✅；只答其一不冲突 ⚠️。

---

## B 组 · jianli 项目域（page_key=`projects`，project_key=`jianli`）

### FQ-11 · jianli 这个项目是做什么的？
- **期望事实**：面向正式上线的 AI 面试协作站；把简历/项目 RAG 问答、登录注册、会话、动态时段、预约管理、邮件与飞书通知做成一条可验证产品链。
- **溯源**：CORPUS `jianli-overview.md`。
- **判定要点**：点出"个人 AI 问答网站 + 三件套产品链" ✅；只答"问答网站"不冲突 ⚠️；答成"别人的产品"❌。

### FQ-12 · jianli 处理越界或无依据问题的原则是什么？
- **期望事实**：真实性优先，越界或无依据问题一律拒答，绝不编造经历。
- **溯源**：J0「核心约束是面试场景真实性优先——越界或无依据的问题一律拒答，绝不编造经历。」
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
- **溯源**：CORPUS `jianli-agent-rag.md` / `jianli-reranker.md`。
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
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"拒答率 100%（REJECT 10/10）" ✅；说"拒答率 0%"❌（那是修复前的基线）。

### FQ-19 · jianli 的 Agent 能调用哪些工具？
- **期望事实**：五个白名单工具：`search_knowledge`、`request_interview_booking`、`list_my_appointments`、`cancel_appointment`、`reschedule_appointment`；面试官只管理本人，owner_admin 才能管理他人，写操作复用 BookingService，MAX_STEPS=4。
- **溯源**：CORPUS `jianli-agent-rag.md` / `docs/baseline.yml agent_tools`。
- **判定要点**：命中五工具 + 本人/管理员 RBAC + BookingService 复用 ✅；说 Agent 可直接写数据库、导出他人信息或调用白名单外工具 ❌。

### FQ-20 · jianli 的 Agent 是怎么决定要不要检索的？
- **期望事实**：模型通过 function calling（`tool_choice=auto`）自主决策是否检索并生成检索词。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"function calling / tool_choice=auto 模型自主决策" ✅；说成"硬编码固定检索词"❌（那是演进前的旧方案）。

### FQ-21 · jianli 用什么来量化检索质量？
- **期望事实**：`tests/aiqa/test_rag_eval.py` 将 canonical corpus 真实上传、分块、embedding 入库，再通过混合检索与 `streamAnswer` 验证命中、拒答、隐私和误拒，不是只测一个 mock scorer。
- **溯源**：CORPUS `jianli-evaluation-ci.md` + `tests/aiqa/test_rag_eval.py`。
- **判定要点**：命中"test_rag_eval.py + 真实语料全链路" ✅；说"没有评测"❌。

### FQ-22 · jianli 的检索评测达到了什么水平？
- **期望事实**：当前版本化报告中 RAG 事实一致性 38/38；越界集 10/10 拒答。整体报告为 79/79，但样本规模有限，不能等同生产质量。
- **溯源**：CORPUS `jianli-evaluation-ci.md` / `apps/web/evals/latest.json`。
- **判定要点**：命中 38/38 + 10/10 + 有限样本边界 ✅；把整体 79/79 说成 79 条全是 RAG 问题或生产准确率 100% ❌。

### FQ-23 · jianli 的预约业务闭环有哪些关键保障？
- **期望事实**：Slot 快照与并发锁、3 分钟预览不预占、原子创建、字段级 AES-256-GCM 加密、Outbox 通知、审计日志、SSE 恢复契约。
- **溯源**：CORPUS `jianli-reliability.md`。
- **判定要点**：命中 4 项以上关键保障 ✅；只答"有加密"⚠️；说成"无加密明文存储"❌。

### FQ-24 · jianli 的集成测试情况如何？
- **期望事实**：当前公开版本化证据合计 79/79，覆盖 Agent/Trace 22、RAG 事实 38、Web 1、Reranker 协议 4、缓存/Provider 韧性 8、多副本熔断 6；GitHub 三作业已完成本地等价门禁，但远端 run 尚待授权 push。
- **溯源**：CORPUS `jianli-evaluation-ci.md` / `apps/web/evals/latest.json`。
- **判定要点**：命中 79/79 的分组含义 + 远端未跑边界 ✅；说远端 GitHub Actions 已绿或把它说成 79 条端到端生产测试 ❌。

### FQ-25 · jianli 的 embedding 经历过什么演进？
- **期望事实**：从本地哈希（无语义）换成 BGE-M3。
- **溯源**：CORPUS `jianli-agent-rag.md`。
- **判定要点**：命中"本地哈希 → BGE-M3，哈希无语义" ✅；说反方向 ❌。

### FQ-26 · jianli 开发中有过什么值得记录的坑？
- **期望事实**：Agent 模型自主决策上线后评测一度 8/8→6/8，根因是 greeting 判定里 'hi' 子串误匹配 'litchi'，改整词匹配修复。
- **溯源**：CORPUS `jianli-reliability.md`。
- **判定要点**：命中"greeting 'hi'⊂'litchi' 子串误匹配、改整词匹配" ✅；说成"没有任何坑"❌（与诚实记录相悖）。

### FQ-51 · 模型生成的检索词偏离原问题时，Jianli 怎么避免丢证据？
- **期望事实**：服务端同时检索模型生成词与用户原问题，按文档和片段去重合并；不会先截断模型词结果后把原问题证据挤掉。
- **溯源**：CORPUS `jianli-agent-rag.md` / `AnswerService._search_candidates`。
- **判定要点**：命中“双路检索 + 去重合并 + 保留原问题 fallback” ✅；说完全信任模型改写或只查一次 ❌。

### FQ-52 · 为什么 BM25 有中文重叠时仍可能拒答？
- **期望事实**：知识库路径先要求至少一个 BGE-M3 向量候选达到 0.47；若向量证据门未通过，BM25 的中文单字重叠不能单独触发 grounded 回答，以降低偶然重叠误答。
- **溯源**：CORPUS `jianli-agent-rag.md` / `AnswerService._knowledge_candidates`。
- **判定要点**：命中“向量证据门先行、BM25 不能单独兜底硬答” ✅；说只要 BM25 命中就回答 ❌。

### FQ-53 · Jianli 的 Agent 为什么不能靠 Prompt 保证不越权？
- **期望事实**：模型只负责提出 function call；服务端限制五个工具、MAX_STEPS=4、登录态和本人 RBAC，未知工具拒绝，预约写操作复用 BookingService。管理员管理他人走独立管理端边界，不接受模型自报角色。
- **溯源**：CORPUS `jianli-agent-lab.md` / `AnswerService._run_agent_tool`。
- **判定要点**：命中“模型计划非可信 + 代码白名单/RBAC/业务服务” ✅；说 Prompt 或模型角色声明可以授权 ❌。

### FQ-54 · answer.trace 是不是模型思维链？
- **期望事实**：不是。它是服务端生成的脱敏执行事实，只含单调 step、固定 phase/status、白名单工具、耗时和短标签，不含 Prompt、用户/知识原文、参数、完整结果或预约 PII。
- **溯源**：CORPUS `jianli-agent-lab.md`。
- **判定要点**：命中“结构化运行轨迹，不是 chain-of-thought”及隐私边界 ✅；宣称公开模型完整推理过程 ❌。

### FQ-55 · 两个请求同时抢同一预约时段，Jianli 如何处理？
- **期望事实**：确认预约时在同一数据库事务中锁公司和三个连续 30 分钟 Slot，复核状态后写预约、占 Slot、Outbox 与审计；Slot 竞争由行锁和事务内状态复核处理。活动用户/公司部分唯一索引独立约束重复业务预约，不应解释成“行锁失效兜底”。冲突转成业务错误，真实测试含十轮双事务抢 Slot。
- **溯源**：CORPUS `jianli-reliability.md` / `BookingService.create` / `test_two_transactions_race_for_slots_ten_rounds`。
- **判定要点**：命中“行锁 + 同事务 + 唯一索引 + 并发测试” ✅；只说前端按钮防重复或 Redis 锁 ❌。

### FQ-56 · Jianli 的 Outbox 能保证邮件和飞书 exactly-once 吗？
- **期望事实**：不能这样宣称。Worker 以 `FOR UPDATE SKIP LOCKED` 抢占事件并按失败窗口重试，delivery 唯一键防重复尝试行，整体是 at-least-once；外部发送与数据库状态不是一个原子事务，仍需容忍提供方侧重复。
- **溯源**：CORPUS `jianli-reliability.md` / `notifications/worker.py`。
- **判定要点**：命中“at-least-once + 尝试行幂等边界 + 外部副作用非 exactly-once” ✅；说有 Outbox 就绝不重复 ❌。

### FQ-57 · Jianli 的语义缓存如何避免跨域旧答案？
- **期望事实**：只缓存匿名、无会话、无工具轨迹的 grounded 回答；namespace 由 page/project 生成，阈值 0.94、TTL 600 秒、最多 100 条，不存问题明文；知识上传或删除会失效全部登记 namespace，异常时旁路而非影响问答。
- **溯源**：CORPUS `jianli-reliability.md` / `semantic_cache.py` / `AnswerService._invalidate_semantic_cache`。
- **判定要点**：命中“资格限制 + 域隔离 + TTL/容量 + 知识变更失效” ✅；说登录会话或工具副作用也缓存 ❌。

### FQ-58 · 多个 API 实例如何共享 Provider 熔断状态？
- **期望事实**：LLM 与 Reranker 使用独立固定组件键，Redis Lua 原子维护 closed/open/half-open、失败计数和恢复窗口；恢复时跨实例只放一个探针。Redis 失联时退回各实例本地 breaker，不能再宣称跨实例一致。
- **溯源**：CORPUS `jianli-reliability.md` / `RedisCircuitBreaker` / `test_real_redis_cross_instance_atomic_probe`。
- **判定要点**：命中“Redis Lua 共享状态 + 单探针 + 断连本地降级边界” ✅；说内存 breaker 天生跨实例共享 ❌。

---

## C 组 · Litchi 毕设域（page_key=`projects`，project_key=`litchi`；TASK-AIQA-KB-EXPAND-014 新增）

### FQ-27 · litchi 毕设用了什么技术栈？
- **期望事实**：本人独立完成的 90.4 分毕设；Spring Boot 3.2 / Java 17 后端 + Vue3 / TypeScript 前端 + Python 诊断服务 + MySQL，AI 链路使用 Milvus、Neo4j、本地 Ollama；三者曾同时真实运行并在答辩现场演示。数据平台、可观测性和 Helm 是已实现的实验模板，不是生产部署。
- **溯源**：CORPUS `litchi-overview.md` / content.py litchi chunk / 用户事实确认。
- **判定要点**：命中“独立开发 + Spring Boot/Vue3 + Milvus/Neo4j/Ollama 现场演示 + 模板边界” ✅；说成 FastAPI/React 主栈或模板已生产化 ❌。

### FQ-28 · litchi 的四段受控 Agent 是怎么实现的？
- **期望事实**：Planner 用 LLM 生成 JSON 计划（硬上限 4 步、失败走 fallbackPlan）→ 内嵌 Guard 过滤未知/重复工具并按 AgentTool.supports(user) 做角色收窄 → Executor 顺序执行 → Synthesizer 仅依工具证据作答；pending_remedy_plan 先进入 waiting_approval 再确认落库。当前同一技术员可发起并确认，不是双人复核。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中四段 + 白名单/预算/RBAC/HITL + 单人确认边界 ✅；说成“纯聊天壳”“独立 Guard 服务”或“双人复核已落地”❌。

### FQ-29 · litchi 的 LLM 和向量是怎么选的？
- **期望事实**：本地 Ollama qwen2.5:0.5b（CPU 可跑，无 GPU 笔记本本地演示约束）+ Milvus 哈希向量 1024 维（SimpleEmbeddingService，非语义 embedding）。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中"本地 Ollama 0.5b + 哈希向量 + 无 GPU 约束" ✅；说成"云端大模型 + BGE-M3 语义向量"❌（那是泰益智/jianli）。

### FQ-30 · litchi 的并发压测结果如何？
- **期望事实**：历史 50 并发/50 请求本地测试全部成功（平均约 6.9s、P95 约 11.2s）；后续 100 并发/200 请求多轮成功率约 50.5%/21%/19%，其中一轮 P95 约 15.2s。环境和脚本条件不同，不能据此证明容量回归的单一因果，只能确认高并发稳定性未达标；旧 API 路径、PowerShell JSON、重复依赖探测等已排查，但唯一根因未被证明。
- **溯源**：CORPUS `litchi-evidence-retrospective.md`。
- **判定要点**：同时命中“50 并发历史成功 + 200 请求多轮失败 + 条件不同不能强推因果 + 未证明唯一根因” ✅；只说“50 并发 100% 所以生产可用”或把 19% 说成“200 并发”❌。

### FQ-39 · litchi 为什么不信任 Planner 直接调用工具？
- **期望事实**：Planner 只产出候选 JSON 计划；服务端 Guard 再按 availableTools、重复调用、角色 supports 和最大 4 步过滤，Executor 只执行过滤后的计划。模型输出是非可信输入，权限与预算必须由确定性代码执行。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：命中“模型计划非可信 + 服务端白名单/RBAC/步数二次校验” ✅；说“模型自己保证不越权”❌。

### FQ-40 · litchi 的 RAG 摄入和检索链路是什么？
- **期望事实**：多格式抽取→空白归一化→480/120 切块→双字符/分词 Java hash→1024 维 L2 归一化→Milvus/本地候选→标题/来源/关键词启发式重排→Neo4j 关系证据→Ollama 合成/模板降级。
- **溯源**：CORPUS `litchi-agent-rag.md`。
- **判定要点**：能说明哈希向量是 CPU 离线取舍而非语义 embedding ✅；宣称 BGE、BM25/RRF 或高级 reranker 已实现 ❌。

### FQ-41 · litchi 为什么有 outbox 表仍不是事务 Outbox？
- **期望事实**：Agent/业务状态与 outbox 通过不同保存调用或连接完成，不共享同一原子事务；状态成功而事件失败、或反向不一致的窗口仍存在。
- **溯源**：CORPUS `litchi-evidence-retrospective.md` / `litchi-evolution.md`。
- **判定要点**：命中“同事务原子写入缺失” ✅；仅以“存在 outbox 表”证明可靠投递 ❌。

### FQ-42 · litchi 的 SSE、取消和恢复做到什么程度？
- **期望事实**：后端提供状态 SSE，但前端主要轮询；事件在进程内，没有 Last-Event-ID 持久重放。cancel 只改状态，不能中断已发出的 LLM/数据库调用；执行 steps 也没有逐步持久化。
- **溯源**：CORPUS `litchi-agent-rag.md` / `litchi-evolution.md`。
- **判定要点**：主动说明“端点存在不等于前端闭环或断线恢复” ✅；宣称流式 Token 输出或多实例恢复已完成 ❌。

### FQ-43 · litchi 为什么只能称为部分协作闭环？
- **期望事实**：农户、门店、技术员相关的诊断、方案、审批、咨询和反馈模块都存在，但缺少贯穿它们的统一业务 ID、强状态流转和事务关联。
- **溯源**：CORPUS `litchi-overview.md`。
- **判定要点**：命中“模块存在 + 强关联缺失” ✅；宣称完整技术员审核—门店履约—效果反馈闭环 ❌。

### FQ-59 · litchi 为什么发现文档不命中后没有继续调向量阈值？
- **期望事实**：根因排查发现中文 PDF/DOCX 在文本入口已经为空或乱码；坏输入无法靠相似度参数补救。当前使用 PDFBox/Apache POI，只有有效文本产生分块，空分块标为未索引，扫描件由清洗脚本标记 `needs_ocr`。历史重复状态仍在，检索只是在结果层去重。
- **溯源**：CORPUS `litchi-agent-rag.md` / `DocumentService` / `clean_knowledge_docs.py`。
- **判定要点**：命中“先检查解析入口 + 空文本不索引 + OCR/历史重复边界” ✅；说调高 top-k 或降低阈值就能恢复空文档 ❌。

### FQ-60 · litchi 的 RAG 从 3/30 到 24/30 是模型提升了八倍吗？
- **期望事实**：不是。同一批 runner 结果对修复前错误 `evidenceIds` 只有 3/30，对修正权威文档编号后的标注为 24/30；主要变化是评测标签修复，剩余 6 条才是真实未命中。结果来自未提交工作区，证据等级低于干净提交。
- **溯源**：CORPUS `litchi-evidence-retrospective.md` / 评测结果与标注修复前备份的只读复算。
- **判定要点**：命中“同一结果、标签修正、仍有 6 条失败、工作区证据” ✅；宣称模型或检索算法突然提升八倍 ❌。

### FQ-61 · litchi 图像识别的 93.75% 能代表真实果园吗？
- **期望事实**：不能。原始 11 类 27,594 张图片只抽取五类均衡子集，300 张训练、80 张验证；续训最佳 Top-1 93.75%，末轮 91.25%，部署模型哈希等于 `best.pt`。小验证集波动明显，只证明实验链路。降级路径仍可能使用文件名提示或数据集原型，必须通过 `engine`/`demoMode` 明示；只有 `ultralytics-yolo` 且 `demoMode=false` 属真实模型推理。
- **溯源**：CORPUS `litchi-evidence-retrospective.md` / 训练 CSV、数据目录、模型哈希与诊断服务源码。
- **判定要点**：命中“300/80 + 最佳/末轮区别 + best checkpoint + demoMode 边界” ✅；表述为真实田间准确率 93.75% 或把 fallback 当模型结果 ❌。

## D 组 · sleep 泰益智域（page_key=`projects`，project_key=`sleep202603_an`；TASK-AIQA-KB-EXPAND-014 新增）

### FQ-31 · 泰益智的 84 例评测怎么分类？
- **期望事实**：源码实际是 11 个 case group——睡眠分析 20、知识问答 10、Prompt Injection 10、已审批控制 10、未审批控制 5、模拟超时 5、睡眠报告 5、改善计划 5、语音陪伴 5、算法优化 5、隐私拒绝 4，共 84/84；七类只是展示归并。该工程集不调用外部 LLM，公开 Harness 的设备 ACK 为模拟。未提交 RC 的健康合规为 25/35=71.43%。
- **溯源**：CORPUS `sleep-evidence-retrospective.md`。
- **判定要点**：命中“源码 11 groups + 可展示归并七类 + deterministic/模拟 ACK” ✅；说成“源码原生七类”或只报 100% 而省略口径 ❌。

### FQ-32 · 泰益智 51 条重复的根因是什么？
- **期望事实**：故障注入重平衡首轮被杀 Worker 的原 6 分区出 51 条重复，根因 ClickHouse `Array(UUID)` 参数查重返回空集却不报错，换 string→UUID 子查询修复；3 轮 × 6,240 事件验证（12 分区 lag 全 0、恢复 median 12.605s、300 次显式重放全抑制）。
- **溯源**：CORPUS `sleep-data-reliability.md`。
- **判定要点**：命中"Array(UUID) 返回空集不报错 → UUID 子查询" ✅；说"重复是网络问题"❌。

### FQ-33 · 泰益智同一套代码出了几个端？
- **期望事实**：三端——Taro 小程序（16 页，rpx 单位 / TARO_ENV 分支 / 统一 API 封装做跨端规避）+ Web（dist）+ Android（Capacitor 壳 appId=com.sleep202603.app，MainActivity 一行 extends BridgeActivity、零自定义原生代码）。
- **溯源**：CORPUS `sleep-overview.md`。
- **判定要点**：命中"三端 + Capacitor 壳零原生代码" ✅；说"写过 Java/Kotlin 业务代码"❌（诚实边界）。

### FQ-44 · Sleep 的 202 异步接纳优化到底优化了什么？
- **期望事实**：控制面创建 Run/Outbox 后投递 FastAPI；本地有界队列接纳并由 Worker 后台执行。1000 个合成请求、并发 100 下接纳吞吐 87.78→433.53/s，P95 1347.73→228.85ms；只测 HTTP 接纳，不含真实 LLM/RAG/工具或完成延迟。
- **溯源**：CORPUS `sleep-agent-runtime.md`。
- **判定要点**：命中“202=接纳、不是完成或推理提速” ✅；说“Agent 推理性能提升 393.9%”❌。

### FQ-45 · Sleep 为什么用固定 DAG，Temporal 又验证到了哪？
- **期望事实**：route→policy→finalize 固定 DAG 让工具集合、审批点和预算可预测；不是开放式 ReAct。Temporal 有 Workflow、信号和 Activity 实现，但测试使用 Fake Client，没有真实 Worker/Pod 中断恢复证据。
- **溯源**：CORPUS `sleep-agent-runtime.md`。
- **判定要点**：区分固定图实现与真实 Temporal 恢复 ✅；宣称 Temporal exactly-once 或故障恢复已验证 ❌。

### FQ-46 · Sleep 的设备控制安全边界有什么缺口？
- **期望事实**：固定计划、allowlist、参数校验和 HITL 已实现；但 device_control 的可信 allowed_device_ids 未由 NestJS 控制面强制注入，执行器缺省会回退到输入 device_id，内部 Agent API 也缺少独立服务认证。
- **溯源**：CORPUS `sleep-rag-governance.md`。
- **判定要点**：同时说明已实现守卫和可信边界缺口 ✅；用“危险写工具 0”掩盖设备归属风险 ❌。

### FQ-47 · Sleep 的 RAG 租户隔离能证明什么？
- **期望事实**：已实现 global+tenant 过滤、引用和无证据拒答，真实 PG 隔离测试为 2/2；但集成测试使用固定向量，且没有 BM25/RRF/reranker/阈值或正式 Recall/MRR，所以只能证明本地查询边界，不证明生产级语义质量。
- **溯源**：CORPUS `sleep-rag-governance.md`。
- **判定要点**：命中“2/2 本地隔离 + 固定向量/质量边界” ✅；外推为生产多租户安全或高级 Hybrid RAG ❌。

### FQ-48 · Sleep 的设备 command_id 为什么不等于请求幂等？
- **期望事实**：当前公开仓库每次 HTTP 请求生成新 command_id，重复请求仍可能产生两个命令；没有请求 fingerprint 核对，迟到 ACK 还可能把 timeout 改成 success。内部 RC 的指纹/唯一约束/真实 ACK 属 NDA 经历，不作为公开可复现实现。
- **溯源**：CORPUS `sleep-data-reliability.md`。
- **判定要点**：命中“命令 ID 唯一≠业务请求幂等 + 迟到 ACK 状态守卫缺失” ✅。

### FQ-49 · Sleep 的 120 条红队 80% 和危险写工具 0 如何同时理解？
- **期望事实**：120 条为未提交 RC，本人与同事协同设计、执行和分析；96/120 通过，24 条失败主要包括 17 条输入守卫漏检和 7 条运行边界问题。危险写工具 0 只说明固定工具/审批在这些模拟样本中守住，不代表输入防护或生产安全 100%。
- **溯源**：CORPUS `sleep-evidence-retrospective.md`。
- **判定要点**：能同时解释“写边界守住”和“总体仍有失败” ✅；把 0 次危险调用说成系统 100% 安全 ❌。

### FQ-50 · Sleep 上云和可观测性实际做到哪？
- **期望事实**：本人操作的历史阿里云基础设施和数据库迁移跑通过，但应用启动失败且候选未重部署。当前有指标/健康/脱敏 metadata trace 代码；Prometheus 实抓、告警恢复、跨服务 OTel Trace、Temporal 中断恢复和镜像回滚没有公开运行证据。
- **溯源**：CORPUS `sleep-evolution.md`。
- **判定要点**：命中“真实上云排障但应用失败 + 代码能力与运行证据分开” ✅；说 staging/生产上线成功 ❌。

## E 组 · 行为/动机/竞赛（interview-story，TASK-AIQA-KB-EXPAND-014 新增）

### FQ-34 · 你在泰益智是怎么带人的？
- **期望事实**：团队 1→3 人；教同事 Figma（UI/UX）与 MQTT（数据上报）；方式 = 1 对 1 实操演示 → 布置任务 + 验收 → 不停改版迭代；Figma 设计稿与小程序端能力冲突 → 列转换成本清单对齐、先还原核心页再迭代。
- **溯源**：CORPUS `behavior-stories.md`「行为故事、协作与职业动机」。
- **判定要点**：命中"1 对 1 实操→任务+验收→改版"或"先还原核心页" ✅；说"没带过人"❌。

### FQ-35 · 你工程上最大的教训是什么？
- **期望事实**：① 67/84 配置漂移——"失败记录是证据不是污点、评测自己暴露漂移比上线后被用户发现好"；② 静默错误——"错误不报 ≠ 没问题、零报错最危险、对每个探针结果做语义核验"；③ 并发压测时间边界止损。
- **溯源**：CORPUS `behavior-stories.md`「行为故事、协作与职业动机」。
- **判定要点**：命中任意一条核心教训 ✅；说"没什么教训"❌（与诚实记录相悖）。

### FQ-36 · 你的求职动机和职业规划是什么？
- **期望事实**：科班 + 2023 年起用 AI 工具编程 → 前后端项目 → 泰益智从 0 做项目、从架构角度思考工程 → AI 全栈方向；意向深圳南山（充满理想的城市 + AI 产业密集）；选公司看重更大平台；5 年目标一步步往架构师方向走；一句话自荐"文档/契约/评测/门禁都是交付物，让任何接手的人（同事或 AI）无缝上手"。
- **溯源**：CORPUS `behavior-stories.md`「行为故事、协作与职业动机」。
- **判定要点**：命中"2023 起 AI 编程 / 深圳南山 / 架构师 / 可交接"至少两项 ✅；说成"没有规划"❌。

### FQ-37 · 慧眼识蚁项目是做什么的？
- **期望事实**：红火蚁精准防控的"大数据 + 机器人"装备（挑战杯科技发明制作 A 类、团队 5 人我任第一作者）：① 蚁丘-蚁巢识别估算（CNN 多核卷积 + GANs 还原运动蚂蚁轮廓区分红火蚁与本地蚁 + 回归模型估蚁巢大小）；② 户外巡检 + 药剂投放机器人（多传感器融合 + GPS + 环境感知）；③ 大数据决策云平台（时间序列 + 稀疏门控 MoE 预测繁殖/迁徙趋势，输出重点巡检区域）。
- **溯源**：CORPUS `behavior-stories.md`「慧眼识蚁竞赛」。
- **判定要点**：命中"红火蚁 + 大数据/机器人 + CNN/GANs/MoE 任一项" ✅；说成"与蚂蚁无关"❌。

### FQ-38 · 慧眼识蚁做到了什么程度？
- **期望事实**：完成实物中试/原型、已落地实测；识别准确率 ≥95% 为申报书目标指标（非必达实测数字）；相关专利属学校（申报号 [专利号已脱敏]）；对应 2024 大创国家级立项（第一负责人）。
- **溯源**：CORPUS `behavior-stories.md`「慧眼识蚁竞赛」。
- **判定要点**：命中"实物中试/原型 + 已落地实测" ✅；把 ≥95% 说成"实测已达成"⚠️（如实标注为目标指标）；专利说成个人申报 ❌（属学校）。

---

## 备注
- **覆盖项**：个人教育、能力、证书、行为故事进入三篇 canonical profile 文档；B 组 Jianli 基础 FQ-11~26 + 源码级追问 FQ-51~58；C 组 litchi 基础 FQ-27~30 + 技术追问 FQ-39~43 + 开发故事补强 FQ-59~61；D 组 sleep 基础 FQ-31~33 + 技术追问 FQ-44~50；E 组行为/动机/竞赛 FQ-34~38。canonical 文档仍为 20 篇。
- **漂移风险**：若 `content.py` chunk 文本变更，本题库期望事实须同步修订，否则一致率失真。修订须走内容变更流程，不可静默改期望值凑分。
- **题库口径变更（2026-08-18）**：分母 26 → 38（FQ-27+ 扩展，rubric.md §3 同步）；SLO ≥94% 不变，38 题下需 ✅ ≥ 36。
