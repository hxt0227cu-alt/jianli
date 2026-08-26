# TASK-ADMIN-QA-OBSERVABILITY-001 管理端问答客观可观测性

## 任务类型
- implementation
- migration
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.6
- 基线 commit：`b45dbfd`

## 精确规范引用（AI 只读取这些章节）
- `docs/design/domain-model.md §6.13`
- `docs/api/openapi.yaml` operationId `adminListConversations`
- `docs/api/openapi.yaml` operationId `adminListConversationMessages`
- `docs/api/openapi.yaml` operationId `getAIQAStats`
- `docs/api/openapi.yaml` schema `AdminMessage` / `AIQAStats`
- `TASK-CR-ADMIN-QA-OBSERVABILITY-001`

## 需求来源
- 用户于 2026-08-26 显式批准的管理端问答可观测性范围

## 目标
为 assistant 消息持久化三个客观观测事实，并在 owner 管理端展示引用数、响应耗时和是否基于资料。

## 非目标（明确排除）
- 不实现或保留规则硬编码 `quality_score`。
- 不新增外部依赖、公开问答 API、Agent 工具或鉴权策略。
- 不回填无法由历史记录客观恢复的旧消息观测值。

## 允许修改路径
- `apps/api/migrations/versions/0009_aiqa_observations.py`
- `apps/api/app/aiqa/repository.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/app/admin/router.py`
- `apps/api/tests/migrations/test_aiqa_observations.py`
- `apps/api/tests/migrations/test_aiqa_schema.py`
- `apps/api/tests/admin/test_admin_qa.py`
- `apps/api/tests/aiqa/`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tasks/TASK-ADMIN-QA-OBSERVABILITY-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- 认证、预约、通知、知识库摄取实现
- 0001–0008 历史迁移
- 依赖清单与锁文件
- approved 规范工件（本任务只实现已批准契约）

## 已批准的 DB / API / 依赖变更
- DB：新增可逆迁移 0009；`conversation_messages` 增 nullable `grounded boolean`、`citations_count integer`、`latency_ms integer`，后两者增加非负 CHECK。
- API：实现已批准 OpenAPI 0.5 中 admin 消息响应的三个 nullable 字段，以及统计响应的 `observed_answers`、`grounded_messages`、`grounded_rate`、`avg_latency_ms`。
- 依赖：无。

## 规范影响评估（spec impact）
- behavior_change：true
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：用户可观察行为与 schema 变化已先由 `TASK-CR-ADMIN-QA-OBSERVABILITY-001` 批准并同步至领域模型 1.1.6 / OpenAPI 0.5，本任务只实现批准态。

## 功能验收
- 新 assistant 消息保存本次回答的 grounded、实际 citations 数和服务端总耗时；user 与历史消息允许 null。
- owner 可在消息详情查看三个事实；统计仅以 `grounded IS NOT NULL` 为覆盖分母，历史 null 不污染比例。
- 正确拒答不被转换成主观质量分数；仓库生产代码与响应契约不存在 `quality_score`。

## 安全与隐私验收
- 三个 admin operation 继续仅 `owner_admin` 可访问；interviewer 返回 403。
- 不新增消息正文或身份数据暴露面。

## 性能验收
- admin 统计保持单次请求完成，不引入逐消息 N+1 查询。
- latency 使用单调时钟并以非负整数毫秒落库。

## 变更预算（change_budget）
- max_files：11
- expected_prod_lines：220
- expected_test_lines：220

## 必须运行的测试命令
- `pytest tests/migrations/test_aiqa_observations.py -v`
- `pytest tests/admin/test_admin_qa.py -v`
- `pytest tests/aiqa -q`
- `ruff check .`
- `mypy app`
- `npm run typecheck && npm run build`
- 对隔离 PostgreSQL 执行 Alembic `upgrade head -> downgrade 0008 -> upgrade head`

## 回滚方法
- 执行 `alembic downgrade 0008` 删除三个 nullable 字段及其 CHECK；回退对应应用提交。

## 强制停止条件
- 遵循 `AGENTS.md §2`；出现未列明 DB/API/依赖/安全变化、冻结测试失败或超过预算时立即停止报告。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`6b4df92`
- 修改文件清单：0009 迁移、AIQA repository/service、admin router、三组后端测试、Web 管理端、任务单（10 文件）
- 测试命令及结果：迁移套件 7 passed；admin 真栈 1 passed；AIQA 会话真栈 5 passed；AIQA DB-free 59 passed / 23 env-skipped；前端 typecheck/build passed
- lint / typecheck：本任务 8 个 Python 文件 `ruff` passed；`mypy app` 46 source files / 0 error；全仓 `ruff check .` 被既有任务外 `scripts/seed_kb.py`、`test_persona_style.py`、`test_rag_eval.py` 57 条问题阻塞
- DB 迁移验证：隔离 `jianli_tc_aiqa_001_db` 完成 upgrade head → downgrade 0008 → upgrade head；nullable 与两个非负 CHECK 均验证通过
- 验收证据：owner 三接口 200 且返回 grounded=true / citations_count=2 / latency_ms=1350；interviewer 三接口均 403；RAG 与拒答真栈分别落库 true/>0/非负耗时及 false/0/非负耗时
- 变更预算实际值：10/11 文件；生产新增 122 行、测试新增 157 行（任务治理 116 行不计生产/测试）；未超预算
- 未解决风险：仓库全量 ruff 的 57 条既有任务外问题需独立授权任务处理；本任务功能、迁移、权限、类型与前端门禁均通过
- 是否偏离 TASK：否
- 规范影响结论：updated（上游 CR 已批准）
- spec_sync：clean
- verified_commit：`6b4df92`
- 关闭门禁：Implemented / 验收通过；因全仓 ruff 任务外阻塞暂不标 Closed

## 关联
- Change Request：`TASK-CR-ADMIN-QA-OBSERVABILITY-001`（Approved / Closed，`7b44781`）
- 测试任务：本任务内实现测试；不修改既有冻结断言
