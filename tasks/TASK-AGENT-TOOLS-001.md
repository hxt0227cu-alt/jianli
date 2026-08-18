# TASK-AGENT-TOOLS-001 Agent 工具化：search_knowledge 只读工具 + 决策链 SSE 可见

> **状态**：**Closed（2026-08-18 用户显式授权关闭 001+002）**——阶段 1 交付已完成并 WSL 验证（绿色 tool-chain 条可见）；**阶段 2（模型自主决策两阶段）由 TASK-AGENT-TOOLS-002 承接并完成**（LITERAL 8/8 + REJECT 10/10 真模型自主决策全绿），两任务一并关闭。
> **依赖**：RAG 全部收官（混合检索/评测/阈值 closed）；DeepSeek V4 Flash 支持 OpenAI 兼容 tools（function calling）

## 1. 背景（面试工程：从 RAG 问答 → 受控 Agent）
当前 `stream_answer` 检索是**代码写死**的（自动混合检索），模型无决策权——面试可讲"RAG"，但讲不了"Agent"。
本任务：检索/页面查询注册为**白名单只读工具**，模型**自主决策调用**，决策链 SSE 可见。

## 2. SSE 契约变更（Change Request，用户"要做"即预批准；如实登记）
- **新增帧** `answer.tool_calls`：决策链可见——`tools`（工具名/入参 query）+ `results`（命中 doc·chunk 摘要，**不返回 storage_key/原文全文**，仅名称+序号+相似度）+ `trace_id`
- **§3 禁止条款修订**：保留"模型不得触发**预约/写入**工具调用"（PRD 决策#14 不变）；**新增允许**：模型可调用 `search_knowledge`（只读检索）工具，由系统执行、结果回填后继续生成
- 帧顺序：`answer.started` → （可选 `answer.tool_calls`）→ `answer.delta`* → `answer.citations` → `answer.completed`
- 前端展示：`answer.tool_calls` → "🤖 已检索知识库（query=…）→ 命中 N 个片段"

## 3. 实现清单

**阶段 1（本任务，2026-08-15 已交付，commit `4cf986c`）——决策链可观测**
- [x] `gateway.py`：`LLMGateway.answer` 增加 `tools` 入参（OpenAI 兼容 tools 格式）；`OpenAIGateway` 解析流式 `tool_calls` 增量（拼接 function name+arguments JSON）；`StubGateway` 模拟"调用 search_knowledge（query=原问题）"保持 DB-free 确定性
- [x] `sse.py`：`tool_calls_frame(seq, calls, trace_id)`（`calls` 含 `name`/`query`/`hits`，`hits` 仅 doc·fragment 摘要，无 storage_key/原文全文）
- [x] `models.py`/契约文档：`docs/api/sse.md` §3 更新（`answer.tool_calls` 帧 + 工具白名单边界条款）
- [x] 前端 `main.tsx`：解析 `answer.tool_calls` 帧 → 展示工具调用链（`.tool-chain` 绿色条）
- [x] 前端 `styles.css`：`.tool-chain` 样式

**阶段 2（未在本任务接通，由 TASK-AGENT-TOOLS-002 承接）——模型自主决策**
- [ ] `service.py`：`stream_answer` 两阶段——① 第一轮带 `tools` 调 LLM；② 若返回 `search_knowledge` 调用 → 解析模型生成的 `query` → 执行现有 `_knowledge_candidates(query)`（含阈值）→ 回填 tool 结果 → 第二轮生成；模型不调工具 → 系统兜底检索（query=原问题），无命中仍走现有 offtopic 拒答（安全不变量不放松）
- [ ] 测试：DB-free 断言 `answer.tool_calls` 帧存在；评测 REJECT/LITERAL 在真工具决策下重验（WSL）

> 当前 `service.py` 的 `tool_calls_frame` 由系统在 candidates 非空时**硬编码**发送（name=search_knowledge、query=原问题），模型并无决策权；前端展示的绿色条即此硬编码帧。

## 4. 安全不变量（不得放宽）
- 工具白名单：**仅** `search_knowledge`（只读）；预约/写入/管理端点**绝不注册**为模型工具（PRD 决策#14）
- 工具结果不回传全文到前端帧（只 doc·chunk·score），引用溯源仍走 citations
- 匿名/会话边界、越界拒答、限频全部不变

## 5. 验收

**阶段 1（已完成，2026-08-15 用户 WSL 验证全绿）**
- [x] ruff ✅ / mypy ✅ / DB-free ✅（沙箱；评测 5 passed，LITERAL 8/8 + REJECT 10/10 无回归）
- [x] WSL（DeepSeek + BGE-M3）：评测重跑 5 passed（`== RAG LITERAL HIT = 8/8 (100%)`、`== RAG REJECT= 10/10 (100%)`）；前端 `typecheck` / `test`（1 passed）/ `build` 全绿
- [x] WSL 浏览器：回答上方出现绿色 tool-chain 条「🤖 已检索知识库（query=…）→ 命中 N 个片段」
- [x] 交付证据回填（本文件；commit 见 TASK-AGENT-TOOLS-002 收口一并提交）

**阶段 2（TASK-AGENT-TOOLS-002，2026-08-18 完成并一并关闭）**
- [x] ruff ✅ / mypy ✅ / DB-free ✅（沙箱：test_aiqa 13 + test_agent_tools 5 = 18 passed）
- [x] WSL（DeepSeek + BGE-M3）：评测 REJECT/LITERAL 在**真模型自主决策**下重验保持 8/8、10/10（`ca81e7b` 后 LITERAL 8/8 + REJECT 10/10 + 5 passed）；浏览器新会话提问 → 绿色 tool-chain 条内 `query` 为模型生成的检索词（用户 2026-08-18 授权关闭时确认）
- [x] 用户显式授权关闭 001 + 002（2026-08-18）

## 6. 面试价值
"把 RAG 问答升级为**受控 Agent**：`search_knowledge` 注册为白名单只读工具，
模型通过 function calling 自主决策检索（query 由模型生成），决策链（工具名/query/命中片段）
通过 SSE `answer.tool_calls` 帧**可观测**；预约/写入类工具绝不注册（只读不越权）。"
