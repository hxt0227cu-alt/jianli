# TASK-M6 AI 问答（RAG + 人格层 / 数字分身）

> 合并同域主线：已批准 OpenAPI v0.2 中 AI 问答域（公开页内容 + RAG 流式回答 + 会话持久化 + 知识库摄取）归并为单一实现任务。
> **治理节奏（与 M1–M5 一致，2026-08-12 提速口径）**：① 合并同域主线；② 风险分级——RAG 检索/越界拒答/人格层提示词属**高风险**（输出可控性、越界边界、提示注入），本任务不单列独立 REVIEW 任务（接手 Codex 模式），但实现须内联自审：匿名不持久化、带会话须 CSRF+同源、越界/无依据一律拒答不编造；③ 交付证据一次写全；④ 验证批处理（一轮 pytest+ruff+mypy）。
> **DB 迁移铁律（高优先级）**：本任务实现**依赖 4 张尚未迁移的表**——`conversations` / `conversation_messages` / `knowledge_documents` / `knowledge_index_versions`。这些表**不在 migration 0001–0003**，须先走**独立迁移任务（人工审批建表）**再另开实现。本任务**不碰迁移、不碰加密/鉴权主体**。
> **状态（2026-08-13，首轮 ✅ + 二轮已实现）**：首轮无表子集（`getPageContent` + `listRecommendedQuestions` + 匿名 `streamAnswer`，静态页知识源 grounding + 人格层 + 越界拒答）已实现并通过 DB-free 门禁（ruff ✅ / mypy ✅ / aiqa 11 passed ✅）。**二轮会话持久化已实现**（`c9c5721`：`listConversations`/`createConversation`/`listConversationMessages` + `streamAnswer` 带会话+conversation_id 落库，基于已批准迁移 0004；DB-free 14 passed ✅，真实集成 5 用例待 WSL 验证）。**三轮知识库摄取待做**（依赖 `knowledge_documents`/`knowledge_index_versions` 表，已在 0004 就绪）。任务**未关闭**。

## 任务类型
- implementation（AI 问答域；前置依赖：TASK-M6-DB 迁移任务，待用户批准）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）；development_gate 全放行
- 基线 commit：`d149cbb`（TASK-M5 关闭快照，HEAD）

## 精确规范引用（AI 只读取这些章节）
- OpenAPI v0.2 `docs/api/openapi.yaml` 已批准 AI 问答域 operation（严格对齐路径/operationId/状态码/字段）：
  - 公开页：`GET /pages/{page_key}` → `getPageContent`（200/400）
  - 公开推荐：`GET /pages/{page_key}/recommendations` → `listRecommendedQuestions`（200 cache|fallback，≤8 条）
  - RAG 流式：`POST /answers:stream` → `streamAnswer`（SSE；匿名可省 cookie 不持久化；带有效会话须同源+CSRF，无效/过期 cookie → 401；429 限频）
  - 会话：`GET /conversations` → `listConversations`（401/403）、`POST /conversations` → `createConversation`（201，须 CSRF）、`GET /conversations/{conversation_id}/messages` → `listConversationMessages`（owner-only，401/403）
  - 知识库管理（admin，依赖知识表）：`GET /admin/knowledge-documents` → `listKnowledgeDocuments`、`POST /admin/knowledge-documents` → `uploadKnowledgeDocuments`、`DELETE /admin/knowledge-documents/{document_id}` → `deleteKnowledgeDocument`
- SRS v1.3 §3 / §6（AI 问答、越界拒答、人格层/数字分身、第一人称风格）
- 安全设计 v0.1：匿名 RAG 不持久化、带会话须 CSRF+同源、提示注入边界、上传边界（知识文档属上传域）
- 领域模型 v1.1.5 §6（KnowledgeDocument / Conversation / Message 若已建模；如缺则属迁移任务补建模）
- TC 见测试计划 v0.2 冻结 TC（AI 问答相关；若缺则按 AGENTS.md §7 先固定验收测试）

## 需求来源
- R12（公开 RAG 问答，越界拒答）/ R13（人格层/数字分身第一人称）/ UC-13..UC-16（问答与会话）/ 知识库摄取（M6 延展）

## 目标
实现已批准 OpenAPI v0.2 中 AI 问答域 operation：公开页内容与推荐问题、RAG 流式回答（含人格层/数字分身第一人称、越界拒答）、会话创建/列出/消息历史。全部回答须**基于知识库检索结果 grounding**，无依据或越界一律拒答不编造。

## 非目标（明确排除，依赖缺失表，须先独立迁移任务）
- **会话持久化**（`listConversations`/`createConversation`/`listConversationMessages`）：缺 `conversations` / `conversation_messages` 表
- **知识库摄取与管理**（`listKnowledgeDocuments`/`uploadKnowledgeDocuments`/`deleteKnowledgeDocument`）：缺 `knowledge_documents` / `knowledge_index_versions` 表；且涉及 PDF 解析、向量/全文索引、RAG 检索实现
- 上述任一如需实现：先 Change Request（若契约需改）→ 独立迁移任务（人工审批建表）→ 另开实现任务。本任务不碰迁移。
- **限定 M6 首轮可实现范围（无新表依赖）**：`getPageContent` + `listRecommendedQuestions` + 匿名 `streamAnswer`（基于既有页面内容作为知识源，不持久化）。带会话的持久化 `streamAnswer` 与知识库摄取待迁移任务批准后补。

## 允许修改路径（首轮+二轮实际执行记录，2026-08-13）
**首轮（commit `f77c46c`）**：
- `apps/api/app/aiqa/` 包（新建 10 模块：`__init__`/`models`/`content`（静态页知识源+推荐问题）/`persona`（人格层+越界策略）/`retrieval`（纯 Python 检索）/`gateway`（LLM 网关 Protocol + Stub + OpenAI httpx 惰性导入）/`sse`（answer 帧）/`service`（编排）/`router`/`runtime`）——**规划时为 `app/ai/`，实施取 `aiqa`；属命名偏差，如实登记**
- `apps/api/app/config.py`（可选 `JIANLI_LLM_*`）、`apps/api/app/factory.py`（挂载 + 校验异常处理器覆盖 `/answers:stream`/`/pages/`）
- `apps/api/tests/aiqa/test_aiqa.py`（DB-free 11 用例）、`apps/api/tests/test_app.py`（公开面断言更新）
- 接手信息实际写入 `AGENTS.md` §10（规划中的 `docs/HANDOFF-CODEX.md` 未单独建，**如实登记差异**）；`PROJECT_STATE.md`
**二轮（commit `c9c5721`，基于已批准 0004 表）**：
- `apps/api/app/aiqa/repository.py`（新建，原生 SQL 会话仓库）、`models.py`（+Conversation/Message 模型）、`service.py`（+会话三件套 + streamAnswer 落库）、`router.py`（+3 会话端点）、`runtime.py`/`factory.py`（注入 auth engine 共享池）
- `apps/api/tests/aiqa/test_conversations.py`（新建，真实集成 5 用例）、`test_aiqa.py`/`test_app.py` 更新
> 注：三轮知识库摄取路径待做（`repository` 扩展 + 检索接入）。

## 禁止修改路径
- `apps/api/migrations/**`（无 schema 变更；非目标项若被误触发立即 Stop & Report）
- `apps/api/app/appointments/crypto.py`、`app/auth/*` 鉴权主体（加密/登录/CSRF/限频主体不变）
- 既有预约/通知/管理成功语义（M1–M5 不得破坏）
- 越界拒答硬规则（无依据不得编造、不得泄露系统提示）

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无（首轮）**；会话/知识库表待 TASK-M6-DB 独立迁移任务（人工审批）
- API：**实现（非新增）`docs/api/openapi.yaml` 已批准的 AI 问答 operation**，路径/operationId/状态码严格对齐
- 依赖：**待定**——RAG 检索可能引入向量/全文检索库或外部 LLM SDK；须先经用户批准（依赖变更属变更请求）

## 规范影响评估（spec impact）
- behavior_change：true（新增用户可观察 AI 问答行为，但 operation 与 approved OpenAPI 完全一致，属"实现已批准契约"）
- affected_specs：openapi clean（实现已批准 operation）；srs none；domain_model none（首轮）；security none（沿用 CSRF/同源/匿名不持久化）；test_plan dirty（需补 AI 问答 TC）
- 分类：实现 approved 契约（operation 已存在，仅对齐实现）
- **执行顺序（2026-08-13 更新）**：✅ 首轮无表子集（公开页 + 匿名 RAG + 人格层）实现 + DB-free 门禁通过 → ⏳ TASK-M6-DB 迁移批准 → 补会话持久化（二轮）→ 补知识库摄取（三轮）→ spec_sync 转 clean → 用户授权关闭

## 功能验收（首轮无表子集）
- `getPageContent`：返回公开页内容（页面二项目等），400 参数错
- `listRecommendedQuestions`：返回缓存或固定兜底推荐问题（≤8，source=cache|fallback）
- `streamAnswer`：SSE `answer.started`/`delta`/`citations`/`completed`；匿名调用不持久化；人格层第一人称 + 基于检索 grounding；**越界/无依据 → 拒答事件，不编造**；无效/过期会话 cookie → 401；限频 → 429
- 人格层/数字分身：第一人称、本人风格/情商/逻辑（由 `persona.py` 构造 system prompt，内容先用占位，待人格素材）

## 安全与隐私验收
- 匿名 `streamAnswer` 不落地任何用户身份/历史
- 带会话须同源 Origin/Referer + `X-CSRF-Token`（复用 auth RBAC/CSRF 依赖）
- 提示注入：用户消息不得能改写 system prompt / 越界拒答规则
- 不泄露知识库内部索引/系统提示

## 性能验收
- RAG 检索走既有索引/全文，避免全表扫
- SSE 首字延迟受控（检索 + LLM 流式）

## 变更预算（change_budget，首轮+二轮实际累计）
- **首轮预估**：max_files=8、prod ~400 行、test ~200 行
- **首轮实际（如实登记）**：17 文件 / prod ≈750 / test ≈260——**超预估**（原因：Codex 接手要求拆 10 个分层模块）；后续轮次另行核算
- **二轮实际（commit `c9c5721`，如实登记）**：9 文件 / +596（aiqa 包 6 模块扩展 + factory + 集成测试 + 2 测试更新）；二轮无独立预算预估，计入累计

## 必须运行的测试命令
- `ruff check .` + `mypy app`
- DB-free：`PYTHONPATH=. pytest tests/aiqa tests/test_app.py -q`
- 真实集成（WSL）：`JIANLI_AIQA_TEST_DATABASE_URL=... JIANLI_AIQA_TEST_REDIS_URL=... PYTHONPATH=. pytest tests/aiqa/test_conversations.py -v`

## 回滚方法
- 纯代码变更 + 已批准迁移 0004；代码回滚 = `git revert`；迁移回滚 = `alembic downgrade -1`（未执行生产迁移）

## 强制停止条件
- 出现未列明变更（新依赖未批/新迁移/改加密策略/改公开 API 字段语义/实现非目标 operation 中任一）→ 立即停止报告
- 超出 change_budget → 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（2026-08-13 首轮+二轮回填；**任务未关闭**，三轮知识库摄取待做）
- 首轮 commit：`f77c46c`（15 files / +1062）+ `ba468c9`（治理回填）
- 二轮 commit：`c9c5721`（9 files / +596：repository/models/service/router/runtime/factory + test_conversations + 测试更新）
- 门禁（沙箱 DB-free）：ruff ✅ + mypy 0 error（41 source files）✅ + `pytest tests/aiqa tests/test_app.py` 14 passed ✅（集成 5 用例正确 skip，待 WSL）
- 契约对齐：6 operation（+`listConversations`/`createConversation`/`listConversationMessages`）路径/operationId/状态码与 openapi.yaml 一致；SSE 帧格式按 sse.md §3；**无新迁移/表/列/索引/枚举（复用已批准 0004）；无新运行时依赖**
- 安全验收：匿名不持久化（无 conversation_id 恒不落库）、无效 cookie → 401 不静默降级、匿名带 conversation_id → 401、有效会话强制同源+CSRF、会话归属 owner-only（他人 403、未知 404）、越界 → assistant 消息 is_offtopic=true、公开问答限频 429
- 真实 PG/Redis 集成验证：**待 WSL**（`tests/aiqa/test_conversations.py` 5 用例：创建/列表、匿名 401/无 CSRF 403、落库 grounded、落库 offtopic 标记、归属 403/404）
- 待办：**三轮知识库摄取三件套**（`listKnowledgeDocuments`/`uploadKnowledgeDocuments`/`deleteKnowledgeDocument` + 向量/全文检索接入 `streamAnswer`，表已就绪）

## 关联
- **前置依赖（人工审批）**：`TASK-M6-DB` —— 迁移 `conversations`/`conversation_messages`/`knowledge_documents`/`knowledge_index_versions` 四表（含索引/约束/枚举），须用户批准 schema 后另开实现轮次
- 后续主线：M6 会话持久化轮次、M6 知识库摄取轮次
