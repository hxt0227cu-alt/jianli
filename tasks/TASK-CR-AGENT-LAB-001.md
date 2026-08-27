# TASK-CR-AGENT-LAB-001 Agent Lab 与结构化 Trace（Change Request）

> **状态：Closed（2026-08-27，verified_commit=`127b030`）**
> 用户于 2026-08-27 授权以求职竞争力为目标连续推进，并明确要求主线聚焦代码、只保留必要审查。

## 任务类型
- change-request
- documentation
- design

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.7 / UI 1.0.1 / OpenAPI-SSE 0.8 / test-plan 0.6
- 基线 commit：`547ca4c`

## 精确规范引用
- `docs/requirements/SRS.md §3.1–§3.2`
- `docs/design/ui-wireframe.md U2`
- `docs/api/sse.md §3`
- `docs/test/test-plan.md §2.2`
- `docs/design/security.md §9`

## 需求来源
- 用户要求把唯一可公开体验的作品强化为具有 Agent 开发岗竞争力的真实演示。
- 现有系统已有 5 个白名单工具、RAG、拒答、RBAC 和 SSE，但页面只以一行摘要展示决策链。

## 目标
在现有页面 2 的 jianli 项目区域加入 4 个可直接运行的 Agent 挑战场景，并新增脱敏 `answer.trace` SSE 事件，使面试官可检查策略、检索/工具、生成与结果阶段。

## 非目标
- 不新增 Agent 工具、Prompt 权限、模型 provider、数据库或外部依赖。
- 不展示 Chain-of-Thought、系统 Prompt、完整工具参数/结果、知识库原文或预约 PII。
- 不新增第四个顶级页面；Agent Lab 是现有 U2 项目页增强。
- 不包含评测中心、CI、OpenTelemetry、Prometheus/Grafana、故障注入或 Reranker。

## 允许修改路径
- `tasks/TASK-CR-AGENT-LAB-001.md`
- `docs/requirements/SRS.md`
- `docs/design/ui-wireframe.md`
- `docs/api/sse.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/**`
- `docs/design/domain-model.md`
- `docs/design/security.md`
- `docs/api/openapi.yaml`
- 既有冻结 TC 断言

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：新增可选 SSE 事件 `answer.trace`，字段仅为 `step`、`phase`、`status`、`label`、可空 `duration_ms`、可空 `tool_name`、可空 `detail`、`trace_id`。
- API：`phase=policy|routing|retrieval|tool|generation|result`；`status=started|completed|blocked|failed`；同一回答 step 从 1 单调递增。
- 依赖：无。
- 版本：SRS 1.7→1.8、UI 1.0.1→1.0.2、OpenAPI-SSE 0.8→0.9、test-plan 0.6→0.7；PRD/use-cases/domain/architecture/security 不变。

## 规范影响评估
- behavior_change：true
- affected_specs：
  - srs：update
  - domain_model：none
  - openapi/SSE：update
  - security：none（既有最小权限边界不变）
  - test_plan：update（新增 TC-AI-010）
- reason：现有 U2 增加用户可见挑战入口与结构化执行轨迹，须先批准契约再实现。

## 功能验收
- U2/jianli 显示 4 个场景：依据问答、多步预约、安全攻击、无依据拒答。
- 点击场景把预置问题发送到右侧真实问答；登录要求和真实工具权限不绕过。
- 每次回答可展开结构化时间线，阶段按 step 单调排序；不把静态营销文案伪装成实时 Trace。
- 不支持 Trace 的历史消息仍正常渲染。

## 安全与隐私验收
- `label/detail` 只能由服务端固定模板生成，单字段≤160字符，不拼接用户原始输入、系统 Prompt、知识库原文或完整工具结果。
- `tool_name` 只能来自 baseline 白名单；预约 Trace 只显示 outcome 类型，不显示公司、邮箱、电话、会议号、appointment_id。
- 匿名/登录、CSRF、RBAC、限频与持久化规则不变。

## 性能验收
- Trace 为同一 SSE 连接内的小型事件，不新增网络调用或数据库写入。
- 每帧 JSON 载荷≤1KB；不改变现有首字 P95≤3s 门槛。

## 变更预算
- max_files：7
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 版本与 based_on 文本一致性断言。
- Trace 字段白名单/隐私约束人工核对。
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；无数据库或运行时状态。

## 强制停止条件
- 需要新增依赖、DB、工具、权限、Prompt 能力或修改既有冻结 TC 时停止并拆分。
- 超出 7 文件时拆任务。

## 交付证据
- commit / PR：`127b030`（批准规范快照）
- 修改文件清单：本任务单、SRS、UI 线框、SSE、测试计划、baseline、PROJECT_STATE；7/7 均在允许路径。
- 测试命令及结果：版本/based_on/TC-AI-010/`answer.trace` 文本一致性断言 → pass。
- lint / typecheck：纯规范任务，不适用；`git diff --check` → pass。
- DB 迁移验证：无
- 验收证据：SRS 1.8、UI 1.0.2、OpenAPI-SSE 0.9、test-plan 0.7 均 approved；73 个 TC，新增 TC-AI-010。
- 变更预算实际值：7/7 文件；生产代码 0 行；测试代码 0 行。
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`127b030`

## 关联
- 前置：`TASK-CR-AIQA-SSE-ALIGN-001`
- 下游：`TASK-AIQA-AGENT-LAB-001`
