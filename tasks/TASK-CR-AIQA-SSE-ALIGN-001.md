# TASK-CR-AIQA-SSE-ALIGN-001 AIQA 白名单工具与 SSE 契约校正（Change Request）

> **状态：Closed（2026-08-27，verified_commit=`a087f2c`）**
> 用户于 2026-08-27 明确授权本目标链全部必要规范与实现工作；本任务只校正既有批准行为的规范漂移，不新增产品能力。

## 任务类型
- change-request
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.7 / OpenAPI 0.7
- 基线 commit：`68c13c02c39bc15e59e011b4a9bb023615019e4f`

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md §2.4`
- `docs/design/security.md §9`
- `docs/api/sse.md §3`
- `docs/baseline.yml` `agent_tools` / `mvp_hard_rules[0]`
- `TASK-CR-AIQA-BOOKING-001`
- `TASK-AIQA-AGENT-CRUD-001`

## 需求来源
- 仓库审计发现已批准规范与现有实现冲突：SRS/安全设计允许 5 个白名单工具，baseline/SSE 仍保留早期只读工具与单一创建工具口径。
- 用户 2026-08-27 明确授权先消除冲突，再继续 Agent Lab 目标链。

## 冲突事实

| 真相源 | 当前口径 | 结论 |
|---|---|---|
| SRS 1.7 §2.4（行为 SSOT） | `search_knowledge` + 创建/查询/取消/改期预约，多轮最多 4 步 | 已批准行为 |
| Security §9 | 同上；所有预约工具复用 `BookingService` 与 RBAC | 已批准安全边界 |
| 当前源码/测试 | 已实现 5 工具、多轮循环与结构化预约 outcome | 实现事实 |
| baseline `agent_tools` | 仅登记 `search_knowledge`、`request_interview_booking` | 漂移 |
| baseline `mvp_hard_rules[0]` | 声称其余预约仅经确定性 UI/API | 漂移 |
| SSE §3 | 声称预约/写入/管理类工具绝不注册 | 漂移 |

## 目标
使 baseline 与 SSE 契约对齐已经批准的 SRS 1.7、安全设计和当前实现，恢复单一一致口径。

## 非目标（明确排除）
- 不新增、删除或改名任何 Agent 工具。
- 不改变 Prompt、工具参数、RBAC、鉴权、加密或预约领域校验。
- 不改生产代码、测试断言、数据库、OpenAPI HTTP operation 或前端。
- 不实现 Agent Lab、OpenTelemetry、Prometheus/Grafana、CI 或 Reranker。

## 允许修改路径
- `tasks/TASK-CR-AIQA-SSE-ALIGN-001.md`
- `docs/baseline.yml`
- `docs/api/sse.md`
- `docs/test/test-plan.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/**`
- `docs/requirements/SRS.md`
- `docs/design/security.md`
- `docs/api/openapi.yaml`
- `docs/design/domain-model.md`
- 既有冻结测试

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：校正 `docs/api/sse.md §3` 的既有白名单工具文字，补记源码已存在的 `answer.booking` 事件与分支帧顺序；不新增事件、字段、状态码或 HTTP operation。
- 依赖：无。
- 治理：OpenAPI-SSE 0.7 → 0.8；在 baseline `agent_tools` 补登记 `list_my_appointments`、`cancel_appointment`、`reschedule_appointment`，并校正 `mvp_hard_rules[0]` 为 5 工具现状；test-plan 0.5 → 0.6，仅执行 OpenAPI-SSE 0.8 impact review 与 `based_on` 同步，冻结 TC 不变。

## 规范影响评估
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi/SSE：update（纠正低优先级契约漂移）
  - security：none
  - test_plan：none
- reason：不改变运行行为；仅使低优先级工件与 SRS、安全设计及实现事实一致。

## 功能验收
- baseline `agent_tools` 精确登记 5 个现有工具及既有 RBAC guard。
- SSE §3 不再禁止已批准预约工具；如实区分检索分支的 `answer.tool_calls` 与预约写分支的 `answer.booking`，不提前宣称尚未实现的完整多步 Trace。
- SSE 事件名、字段和总体帧顺序不变。
- test-plan 明确 OpenAPI-SSE 0.8 不新增验收行为，72 个冻结 TC 不变。

## 安全与隐私验收
- `answer.tool_calls` 仅暴露工具名、脱敏输入摘要和命中文档片段标识；不暴露原文全文、`storage_key`、密钥或预约 PII。
- 面试官仅本人、owner_admin 管理他人的既有 RBAC 不变。

## 性能验收
- 纯规范校正，无运行时性能变化。

## 变更预算（change_budget）
- max_files：5
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- PowerShell 文本一致性断言：baseline/SSE 同时包含 5 个工具且不再包含旧禁止句。
- YAML 解析：`python -c "import yaml; yaml.safe_load(open('docs/baseline.yml', encoding='utf-8'))"`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；无数据库或运行时状态需要回滚。

## 强制停止条件
- 发现需要改变工具集合、参数、RBAC、Prompt、公开事件字段、数据库或依赖时立即停止并另建 Change Request。
- 超出 5 文件时拆任务。

## 交付证据
- commit / PR：`a087f2c`（规范校正快照）
- 修改文件清单：`docs/baseline.yml`、`docs/api/sse.md`、`docs/test/test-plan.md`、`PROJECT_STATE.md`、本任务单；均在允许路径内。
- 测试命令及结果：5 工具文本一致性断言 → pass；WSL Python `yaml.safe_load(docs/baseline.yml)` → exit 0。
- lint / typecheck：纯文档任务，不适用；`git diff --check` → pass。
- DB 迁移验证：无
- 验收证据：baseline 精确登记 5 工具；SSE 记录 `answer.tool_calls`/`answer.booking` 实际分支且旧禁止句已移除；test-plan based_on=OpenAPI-SSE 0.8。
- 变更预算实际值：5/5 文件；生产代码 0 行；测试代码 0 行；规范/治理净增 143 行。
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated（行为不变，契约校正）
- spec_sync：clean
- verified_commit：`a087f2c`

## 关联
- 上游批准：`TASK-CR-AIQA-BOOKING-001`、`TASK-AIQA-AGENT-CRUD-001`
- 下游：`TASK-CR-AGENT-LAB-001`
