# TASK-AGENT-TOOLS-002 接通模型自主决策：service 两阶段 function calling

> **状态**：Open（2026-08-15 建；用户选定"接通真实模型自主决策（推荐）"）
> **依赖**：TASK-AGENT-TOOLS-001 阶段 1（gateway tools 能力、`answer.tool_calls` 帧、契约、前端渲染已交付并 WSL 验证）；DeepSeek V4 Flash function calling
> **承接**：TASK-AGENT-TOOLS-001 阶段 2 未接通部分——`service.py` 两阶段

## 1. 背景（面试工程：把"决策链可见"升级为"模型自主决策"）
001 阶段 1 后，前端绿色 tool-chain 条展示的 `search_knowledge` 调用是**系统硬编码**（query=原问题），模型无决策权。
本任务：`stream_answer` 第一轮带 `tools` 调真实模型（`tool_choice=auto`），**模型自主决定是否调用 `search_knowledge`、自主生成检索词 `query`**；service 执行工具（复用现有 `_knowledge_candidates` 混合检索 + 阈值）→ 回填 → 第二轮生成。面试讲法升级为："模型通过 function calling 自主决策检索词，白名单只读工具由系统执行，决策链 SSE 可观测；预约/写入类工具绝不注册。"

## 2. 安全不变量（不得放宽，与 001 相同）
- 工具白名单：仅 `search_knowledge`（只读）；预约/写入/管理端点绝不注册为模型工具（PRD 决策#14）
- **无资料永不编造**：工具执行无命中（模型调了工具但 hits=0）或模型不调工具且系统兜底检索无结果 → 一律走现有 offtopic 拒答（`OFFTOPIC_REPLY`、`completed.offtopic=true`），模型自由生成绝不外溢
- 工具结果帧不回传全文（仅 doc·fragment 摘要）；匿名/会话边界、越界拒答、限频不变

## 3. 实现清单
- [x] `service.py`：`_SEARCH_TOOLS` 常量（OpenAI 兼容 tools 格式，description 引导"需要事实依据时调用"）；`stream_answer` 两阶段：
  1. greeting 前置判定（不变）后，第一轮 `gateway.answer(messages1, tools=_SEARCH_TOOLS)`（`tool_choice=auto`，由 `OpenAIGateway` 下发），流式收集：`tool_call`（模型自主决策）或忽略 delta（模型自主判断无需检索）
  2. 模型调 `search_knowledge` → 解析 `arguments.query`（JSONDecodeError 兜底用原问题）→ `_knowledge_candidates(query)` → 空则 `retrieve(query, page_key, project_key)` 兜底 → 有命中：`tool_calls_frame`（模型 query + hits）+ 第二轮带【已知资料】生成（grounded=true）；无命中：`tool_calls_frame`（hits=[]）+ offtopic 拒答
  3. 模型不调工具 → 系统兜底检索（query=原问题）→ 有命中：`tool_calls_frame`（query=原问题）+ 带资料第二轮生成（保证 grounded 与引用一致，评测 LITERAL/SEMANTIC 双路径稳定）；无命中：offtopic 拒答（REJECT 稳定）
- [x] 测试 `tests/aiqa/test_aiqa.py`：新增 `test_stream_answer_tool_calls_frame`——DB-free 断言 `answer.tool_calls` 帧恰好一次、结构（name/query/hits，无 storage_key/text）；grounded 路径 hits 非空、offtopic 路径 hits=[]
- [x] 测试 `tests/aiqa/test_agent_tools.py`（新）：4 用例，用 FakeGateway 模拟真实 OpenAI 网关——① 模型生成 query 真正驱动检索（`calls[0].query == tool_query`，citations 全 jianli）；② 模型不调工具 → 系统兜底（query=原问题）仍 grounded；③ 模型调工具无命中 → hits=[] + offtopic 拒答（OFFTOPIC_REPLY 文案）
- [x] 契约 `docs/api/sse.md` §3：`answer.tool_calls` 语义补记（`query` 由模型自主生成、`hits` 可为空列表；文字同步，不改字段）

## 4. 行为对照（回归边界）
- greeting / off-topic / 匿名 401 / 校验 422 / 会话持久化：全部不变（`test_aiqa.py` 12 passed 覆盖）
- grounded/citations 语义不变（有资料才 grounded；citations 只含 doc·fragment）
- Stub 模式（DB-free）：Stub 收到 tools → 必返 `tool_call(query=原问题)` → 走第 2 步 → 行为与 001 现状一致（DB-free 16 passed 无回归）
- 真实模型：多一次"第一轮决策"调用（无命中时可能两轮），属预期成本

## 5. 验收
- [x] ruff ✅ / mypy ✅（45 files）/ DB-free ✅（沙箱：`test_aiqa.py` 12 passed + `test_agent_tools.py` 4 passed = 16 passed）
- [ ] WSL（DeepSeek + BGE-M3）：评测重跑保持 LITERAL 8/8 + REJECT 10/10（真模型自主决策下）；浏览器新会话提问 → 绿色 tool-chain 条可见，`query` 为模型生成检索词
- [ ] 交付证据回填（WSL 验证结果）+ 用户显式授权关闭 001 + 002
