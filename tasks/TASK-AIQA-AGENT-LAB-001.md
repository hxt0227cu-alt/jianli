# TASK-AIQA-AGENT-LAB-001 Agent Lab 与结构化 Trace 实现

> **状态：Closed（2026-08-27）**

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.8 / UI 1.0.2 / OpenAPI-SSE 0.9 / test-plan 0.7
- 基线 commit：`0f6c6ff`

## 精确规范引用
- `docs/requirements/SRS.md §3.1–§3.2`
- `docs/design/ui-wireframe.md U2`
- `docs/api/sse.md §3` `answer.trace`
- `docs/test/test-plan.md TC-AI-010`
- `TASK-CR-AGENT-LAB-001`

## 需求来源
- 已批准 `TASK-CR-AGENT-LAB-001`。

## 目标
实现 4 个真实 Agent 挑战场景、服务端脱敏结构化 Trace 和前端可展开时间线。

## 非目标
- 不新增工具、Prompt 权限、鉴权、DB、依赖或顶级页面。
- 不实现评测中心、CI、OTel、Prometheus/Grafana、故障注入或 Reranker。
- 不持久化 Trace，不展示 Chain-of-Thought 或敏感数据。

## 允许修改路径
- `tasks/TASK-AIQA-AGENT-LAB-001.md`
- `apps/api/app/aiqa/sse.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/tests/aiqa/test_agent_lab.py`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `PROJECT_STATE.md`

## 禁止修改路径
- 规范工件（本任务只实现已批准契约）
- `apps/api/app/appointments/**`、`apps/api/app/auth/**`
- migrations、依赖清单、Prompt/persona、知识库语料
- 既有冻结测试断言

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：实现 OpenAPI-SSE 0.9 已批准的可选 `answer.trace` 事件及精确字段/枚举。
- 依赖：无。

## 规范影响评估
- behavior_change：true
- affected_specs：SRS/UI/OpenAPI-SSE/test-plan 均已由 `TASK-CR-AGENT-LAB-001` 更新批准；domain/security none。
- reason：本任务只实现批准态，不再改变规范。

## 功能验收
- jianli 项目展示 4 场景并可直接发送到右侧真实 ChatPanel。
- Trace 时间线展示 policy/routing/retrieval|tool/generation/result，step 单调；历史消息无 Trace 正常。
- 写工具仍要求有效登录并沿用 RBAC；挑战按钮不得构造后台旁路。

## 安全与隐私验收
- Trace 精确字段白名单；label/detail 固定模板≤160字符。
- 不包含用户问题、Prompt、知识原文、完整工具参数/结果、邮箱、电话、会议号、company、appointment_id。
- tool_name 仅来自既有工具白名单。

## 性能验收
- 每帧≤1KB，不新增 DB/网络调用；现有首字门槛不变。

## 变更预算
- max_files：8
- expected_prod_lines：320
- expected_test_lines：180

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_agent_lab.py tests/aiqa/test_agent_tools.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app/aiqa/sse.py app/aiqa/service.py tests/aiqa/test_agent_lab.py`
- `cd apps/api && mypy app`
- `pnpm test && pnpm typecheck && pnpm build`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；无迁移或持久化 Trace 数据。

## 强制停止条件
- 需要新增依赖、DB、工具/权限/Prompt、修改未批准事件字段或超出 8 文件时停止并拆分。
- 冻结 TC 失败不得修改其断言。

## 交付证据
- commit / PR：`e1f0636`（页面二并行集成中的 Agent Lab 前端基础）+ `a0b2c9d`（Trace 后端、前端收口与验收）
- 修改文件清单：本任务允许的 8 个路径，未修改 DB、依赖、鉴权、Prompt 或工具白名单
- 测试命令及结果：API 冻结回归 `22 passed`；Web shell `1 passed`；生产构建成功（1792 modules）
- lint / typecheck：`ruff` 通过；`mypy app` 48 source files / 0 errors；`pnpm typecheck` 通过；`git diff --check` 通过
- DB 迁移验证：无
- 验收证据：本地真实 UI 冒烟通过——4 个挑战入口可见；依据问答返回 7 步 Trace；默认收起、点击展开；控制台 0 error；Trace 不含原始问题或工具敏感参数
- 变更预算实际值：8 个允许路径；生产代码约 300 行、测试 168 行，文件数未超预算
- 未解决风险：匿名态多步预约场景按设计只展示登录/权限阻断；登录态完整预约读取仍由既有真实栈测试覆盖
- 是否偏离 TASK：否
- 规范影响结论：updated（上游 CR 已批准）
- spec_sync：clean
- verified_commit：`a0b2c9d`

## 关联
- Change Request：`TASK-CR-AGENT-LAB-001`
- 验收：TC-AI-010
