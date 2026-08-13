# TASK-M6 AI 问答（RAG + 人格层 / 数字分身）

> 合并同域主线：已批准 OpenAPI v0.2 中 AI 问答域（公开页内容 + RAG 流式回答 + 会话持久化 + 知识库摄取）归并为单一实现任务。
> **治理节奏（与 M1–M5 一致，2026-08-12 提速口径）**：① 合并同域主线；② 风险分级——RAG 检索/越界拒答/人格层提示词属**高风险**（输出可控性、越界边界、提示注入），本任务不单列独立 REVIEW 任务（接手 Codex 模式），但实现须内联自审：匿名不持久化、带会话须 CSRF+同源、越界/无依据一律拒答不编造；③ 交付证据一次写全；④ 验证批处理（一轮 pytest+ruff+mypy）。
> **DB 迁移铁律（高优先级）**：本任务实现**依赖 4 张尚未迁移的表**——`conversations` / `conversation_messages` / `knowledge_documents` / `knowledge_index_versions`。这些表**不在 migration 0001–0003**，须先走**独立迁移任务（人工审批建表）**再另开实现。本任务**不碰迁移、不碰加密/鉴权主体**。

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

## 允许修改路径（首轮：无新表依赖子集）
- `apps/api/app/ai/` 包（新建：router / service / models / runtime；RAG 检索 + 人格层提示词 + SSE 流式拼装）
- `apps/api/app/ai/persona.py`（新建：人格层/数字分身第一人称 system prompt 构造，越界拒答指令）
- `apps/api/app/public/router.py`（扩展或新建：`getPageContent` / `listRecommendedQuestions`，基于既有 pages 内容）
- `apps/api/app/factory.py`（挂载 ai + public router）
- `apps/api/tests/ai/test_answer_stream.py`（新建，真实 PG/Redis 或 DB-free，依实现定）
- `PROJECT_STATE.md`（仅当前任务段）
> 注：会话/知识库相关路径在 TASK-M6-DB 批准后于本任务后续轮次追加。

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
- **执行顺序**：TASK-M6-DB 迁移批准 → 实现首轮无表子集（公开页+匿名 RAG+人格层）→ 真实测试通过 → 补会话持久化 → 补知识库摄取 → spec_sync 转 clean → 关闭

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

## 变更预算（change_budget，首轮）
- max_files：8（ai 包 4 + public 扩展 1 + factory 1 + tests 1 + 本任务单 + PROJECT_STATE）
- expected_prod_lines：~400（RAG+人格层+SSE）
- expected_test_lines：~200

## 必须运行的测试命令
- `pytest apps/api/tests/ai/test_answer_stream.py`
- `ruff check .` + `mypy`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件
- 出现未列明变更（新依赖未批/新迁移/改加密策略/改公开 API 字段语义/实现非目标 operation 中任一）→ 立即停止报告
- 超出 change_budget → 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- *待实现后回填（首轮无表子集实现 + 真实测试通过后）*

## 关联
- **前置依赖（人工审批）**：`TASK-M6-DB` —— 迁移 `conversations`/`conversation_messages`/`knowledge_documents`/`knowledge_index_versions` 四表（含索引/约束/枚举），须用户批准 schema 后另开实现轮次
- 后续主线：M6 会话持久化轮次、M6 知识库摄取轮次
