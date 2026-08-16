# TASK-M6-HARDENING-001 AI 问答域生产可用性加固（P0/P1 子集）

> 合并同域主线（加速期口径：TASK-M6-APPOINTMENTS 同类做法）。本任务承载此前风险盘点中判定的
> **该补** 生产可用性项：P0-1 网关重试、P0-2 多轮 memory 回填、P0-3 可观测性最小集、P1-2 token
> 统计。**P1-1 PDF/表格/图片结构感知解析明确延后**（见「非目标」与「未解决风险」）。

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5（取自 `docs/baseline.yml`）
- 基线 commit：a2ccb42

## 精确规范引用
- 领域模型 v1.1.5 §6.13（conversations / conversation_messages 持久化，本任务只是把已落库的
  历史消息回填进 prompt，不改变 schema）
- docs/api/sse.md §3（completed 帧 `usage` 字段已定义；本任务仅从 None 填成真实值）
- AGENTS.md §10.3（安全不变量：匿名不持久化、无效 cookie→401 等不变）
- TASK-KB-THRESHOLD-001 / TASK-AGENT-TOOLS-002（检索与双阶段管线不变，本任务不触及）

## 需求来源
- 风险盘点（用户 2026-08-16 指令「补这些」）：P0-1 / P0-2 / P0-3 / P1-2

## 目标
在不新增外部依赖、不改变任何公开 API/SSE 契约/数据库 schema/加密鉴权策略的前提下，补齐 AI
问答域的四项生产可用性短板：外部 LLM 偶发失败可重试、多轮对话能上下文回忆、关键事件带
trace_id 结构化日志、token 成本可见。

## 非目标（明确排除）
- **P1-1 PDF/表格/图片结构感知解析**：延后。dev 环境知识库为空（仅 `apps/web/public/resume.pdf`
  文本简历，pypdf 抽文本已够用）；结构感知需引入 pdfplumber/camelot/VLM 等新依赖，违反零依赖
  治理且需 Change Request 决策，故不在本任务范围。待用户确认实际知识库含表格/截图后再单独立项。
- 不新增 rerank / 意图识别 / query rewrite（非本批范围）。
- 不引入 Prometheus/Grafana/OpenTelemetry/tracing（仅把现有 JSON 日志补字段 + 结构化关键事件）。
- 不新增数据库表/字段/索引/迁移；不修改公开 API 契约字段；不改动加密/鉴权/权限策略。
- 不实现多 agent / function calling 写工具（仍遵守 PRD 决策#14）。

## 允许修改路径
- `apps/api/app/aiqa/gateway.py`（重试 + usage 解析 + build_gateway 透传 max_retries）
- `apps/api/app/aiqa/config*.py` 对应接入（llm_max_retries 配置项）
- `apps/api/app/aiqa/runtime.py`（接线 max_retries）
- `apps/api/app/aiqa/service.py`（memory 回填 + usage 透传 + 延迟测量 + 结构化日志）
- `apps/api/app/logging_config.py`（JsonFormatter 补可选字段）
- `apps/api/tests/aiqa/test_hardening.py`（新增测试）

## 禁止修改路径
- 迁移文件、领域模型、SRS、OpenAPI 契约、auth/appointments/notification 模块
- `persona.py` / `retrieval.py` / `bm25.py` / `chunking.py` / `content.py`（检索与人格层不变）
- 任何公开 operationId / SSE 事件名 / 契约字段的增删改

## 已批准的 DB / API / 依赖变更
- 无（无 schema 变更；无新增 pip/npm 依赖；重试与 usage 解析均为纯代码；max_retries 配置项
  属既有 `JIANLI_LLM_*` 家族扩展，不引入新依赖）

## 规范影响评估
- behavior_change：false（内存回填属于补全已批准的多轮持久化设计——对话历史已被存储但从未注入
  prompt，本任务把它接通；无契约/字段/API 变化。重试/日志/usage 均为内部或契约已有字段回填）
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none（completed.usage 字段已定义，仅从 None 填真实值）
  - security：none
  - test_plan：none
- reason：全部为内部健壮性/可观测性增强与已批准能力的接线补全，不改变用户可观察契约。

## 功能验收
- 网关重试：OpenAI 端点偶发 5xx / 网络错误时自动退避重试（默认 3 次 = 2 次重试），成功则正常流式；
  4xx 不重试直接报错；重试耗尽抛出 GatewayError → SSE error 帧（既有行为）。
- 多轮回填：登录且有 conversation_id 时，模型在 Phase1/Phase2 能看到最近 N 轮历史；匿名/无
  conversation_id 行为不变（不持久化、不回填）。
- 可观测性：answer 关键终态（completed/error/offtopic/greeting）以 JSON 日志输出，携带 trace_id
  与延迟（ms）；completed 帧 usage 填真实 token 数（Stub 仍为 null）。

## 安全与隐私验收
- 不输出任何 secret/key/全文知识库内容到日志（仅 trace_id/conversation_id/计数/延迟/标记）。
- 现有匿名 401、无效 cookie 401、限流 429、越界拒答等不变量全部不变。

## 性能验收
- 重试退避为确定性（base 0.3s，指数封顶 3s），不引入随机抖动（便于测试与可预测延迟）。
- 历史回填上限 6 条消息，避免上下文膨胀；无消息条数无上限不变量不受影响（已有 Question.max_length）。

## 变更预算
- max_files：8（gateway / config / runtime / service / logging_config / 测试 / TASK / PROJECT_STATE）
- expected_prod_lines：~160
- expected_test_lines：~180

## 必须运行的测试命令
- `pytest apps/api/tests/aiqa/test_hardening.py`（DB-free，新增）
- `pytest apps/api/tests/aiqa/test_aiqa.py`（DB-free，回归）
- `ruff check apps/api` / `mypy apps/api` / `pytest apps/api/tests/aiqa`（批处理）

## 回滚方法
- 全部为纯代码改动，无迁移；回滚 = `git revert` 本任务提交即可。

## 强制停止条件
- 不触发：无新依赖、无 schema 变更、无契约字段变更、无加密/鉴权策略变更、在预算内。
- 若实现中被迫新增依赖/迁移/契约变更，立即停止并报告。

## 交付证据（关闭前回填）
- commit / PR：beafbcf
- 修改文件清单：
  - `apps/api/app/aiqa/gateway.py`（重试循环 + `_RetryableError` + `_backoff` + `stream_options.include_usage` + usage 解析）
  - `apps/api/app/aiqa/service.py`（多轮 memory 回填 `_load_history` + usage 透传 `_add_usage` + 延迟测量 + 结构化日志 `_log_error`/`_log_offtopic`/`answer_completed`/`answer_greeting`）
  - `apps/api/app/aiqa/runtime.py`（接线 `max_retries=settings.llm_max_retries`）
  - `apps/api/app/config.py`（新增 `llm_max_retries` 字段 + `JIANLI_LLM_MAX_RETRIES` 映射）
  - `apps/api/app/logging_config.py`（`JsonFormatter` 补可选字段 trace_id/conversation_id/latency_ms/grounded/offtopic/model/prompt_tokens/completion_tokens）
  - `apps/api/tests/aiqa/test_hardening.py`（新增：网关重试 3 例 + `_RetryableError` 子类 + memory 回填 3 例 + JsonFormatter 2 例）
- 测试命令及结果：
  - `pytest apps/api/tests/aiqa/test_hardening.py apps/api/tests/aiqa/test_aiqa.py -q` → **22 passed**
  - `pytest apps/api/tests/aiqa apps/api/tests/test_app.py apps/api/tests/test_config.py -q` → **31 passed, 17 skipped**（skipped 均为需 PG/Redis 的真实集成测试，正确跳过）
- lint / typecheck：`ruff check` 全通过；`mypy`（gateway/service/runtime/config/logging_config）success，no issues
- DB 迁移验证：无（纯代码，无 schema 变更）
- 验收证据：
  - P0-1 重试：`test_gateway_retries_on_500_then_succeeds`（500→200，恰 1 次重试）、`test_gateway_does_not_retry_4xx`（4xx 不重试，calls==1）、`test_gateway_retry_exhausted_raises`（max_retries=1 耗尽抛 GatewayError）
  - P0-2 回填：`test_memory_backfill_injects_history_and_surfaces_usage`（历史注入且不含当前问句）、`test_memory_backfill_is_bounded`（上限 6 条，最旧注入 prior[4]）、`test_anonymous_stream_has_no_history`（匿名仅 1 条）
  - P0-3 可观测：`test_json_formatter_includes_optional_fields` / `test_json_formatter_omits_absent_fields`
  - P1-2 token：`answer.completed` 帧 `usage.total_tokens == 4`（真实计数，非 None）
- 变更预算实际值：prod 文件 5 + 测试 1 = 6（≤ max_files 8）；prod 增量 ~226 行（含测试 ~180 行），在预算内
- 未解决风险：P1-1 PDF 结构解析延后，待知识库内容确认后单独立项
- 是否偏离 TASK：否
- 规范影响结论：none（completed.usage 字段已定义，仅从 None 填真实值；memory 回填为已批准多轮持久化设计的接线补全）
- spec_sync：clean
- verified_commit：beafbcf
- 关闭门禁：①②③④ 全满足方可关闭
