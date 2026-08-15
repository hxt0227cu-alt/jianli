# TASK-AGENT-TOOLS-001 Agent 工具化：search_knowledge 只读工具 + 决策链 SSE 可见

> **状态**：Open（2026-08-15 建；用户确认"要做 Agent 工具化"）
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
- [ ] `gateway.py`：`LLMGateway.answer` 增加 `tools` 入参（OpenAI 兼容 tools 格式）；`OpenAIGateway` 解析流式 `tool_calls` 增量（拼接 function name+arguments JSON）；`StubGateway` 模拟"调用 search_knowledge（query=原问题）"保持 DB-free 确定性
- [ ] `service.py`：`stream_answer` 两阶段——① 第一轮带 tools 调 LLM；② 若返回 `search_knowledge` 调用 → 执行现有 `_knowledge_candidates(query)`（含阈值）→ 回填 tool 结果 → 第二轮生成；无工具调用 → 直接生成（越界走现有 offtopic 逻辑）
- [ ] `sse.py`：`tool_calls_frame(seq, calls, trace_id)`
- [ ] `models.py`/契约文档：`docs/api/sse.md` §3 更新
- [ ] 前端 `main.tsx`：解析 `answer.tool_calls` 帧 → 展示工具调用链
- [ ] 测试：DB-free 断言 tool_calls 帧存在；评测 REJECT/LITERAL 在真工具决策下重验（WSL）

## 4. 安全不变量（不得放宽）
- 工具白名单：**仅** `search_knowledge`（只读）；预约/写入/管理端点**绝不注册**为模型工具（PRD 决策#14）
- 工具结果不回传全文到前端帧（只 doc·chunk·score），引用溯源仍走 citations
- 匿名/会话边界、越界拒答、限频全部不变

## 5. 验收
- [ ] ruff ✅ / mypy ✅ / DB-free ✅（沙箱）
- [ ] WSL（DeepSeek + BGE-M3）：浏览器问简历问题 → 前端看到"已检索知识库（query=…）→ 命中 N 片段"决策链；越界问题仍拒答；评测 REJECT 10/10 保持
- [ ] 交付证据回填

## 6. 面试价值
"把 RAG 问答升级为**受控 Agent**：`search_knowledge` 注册为白名单只读工具，
模型通过 function calling 自主决策检索（query 由模型生成），决策链（工具名/query/命中片段）
通过 SSE `answer.tool_calls` 帧**可观测**；预约/写入类工具绝不注册（只读不越权）。"
