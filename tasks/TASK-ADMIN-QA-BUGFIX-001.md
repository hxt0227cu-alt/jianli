# TASK-ADMIN-QA-BUGFIX-001 管理端问答历史真实 Schema 修复

> 状态：Closed（2026-08-26，verified_commit=`741c242`）。用户明确要求把管理员查看面试官问题的功能做好。本任务只修复既有 approved 行为与既有 3 个 operation 的运行时缺陷。

## 基线与规范引用

- baseline：PRD 2.3.4 / use-cases 1.7.2 / domain-model 1.1.5 / SRS 1.4 / OpenAPI 0.4
- 基线 commit：`e0a2333`
- `docs/requirements/PRD.md` §4.7 对话记录查看、§8.6 对话隐私告知
- `docs/requirements/SRS.md` §3.9、§7 权限矩阵
- `docs/design/ui-wireframe.md` A3 对话记录查看
- `docs/design/domain-model.md` §6 Conversation / Message（实现表列以 migration 0004 为准）
- 既有实现提交：`62620df`（admin cockpit 三个 operation）

## 目标

1. 将 admin 对话查询从不存在的 `conversation_id` 修正为 migration 0004 的真实 `conv_id`。
2. 在应用工厂挂载 admin cockpit 既有实现所需的 engine。
3. 补 owner_admin 可读、interviewer 禁止、列表/详情/基础统计可查询的回归测试。

## 非目标

- 不新增/修改公开 API、响应字段或 OpenAPI。
- 不新增迁移，不写入 `grounded`、`citations_count`、`latency_ms`、`quality_score`。
- 不改变对话留存、匿名不持久化、owner 只读等隐私策略。
- 不修改前端；现有 admin UI 继续消费既有字段。

## 允许修改路径

- `apps/api/app/admin/router.py`
- `apps/api/app/factory.py`
- `apps/api/tests/admin/test_admin_qa.py`
- `tasks/TASK-ADMIN-QA-BUGFIX-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径

- `apps/api/migrations/**`
- `docs/api/**`、`docs/requirements/**`、`docs/design/**`
- `apps/web/**`
- `apps/api/app/aiqa/**`

## 已批准的 DB / API / 依赖变更

- DB：无；修复查询以对齐现有 `conversation_messages.conv_id`。
- API：无；复用 `62620df` 已存在的 `adminListConversations`、`adminListConversationMessages`、`getAIQAStats`。
- 依赖：无。

## 规范影响评估

- behavior_change：false（bug 修复使实现回到 approved PRD/SRS 行为）
- affected_specs：none
- spec_sync：clean

## 验收与预算

- owner_admin：列表、消息详情和基础统计 200，内容与计数正确。
- interviewer：三个 endpoint 均 403。
- 未知 conversation 返回空 items（保持既有实现语义，本任务不改契约）。
- `ruff check`、任务测试、`mypy app` 通过。
- change_budget：max_files=5 / expected_prod_lines≤20 / expected_test_lines≤180。

## 回滚

- 回退本任务提交；无迁移、无数据回滚。

## 强制停止条件

- 需要新增字段、迁移、响应字段、鉴权策略或依赖。
- 冻结测试失败或超过预算。

## 交付证据

- commit / PR：`741c242`
- 修改文件：`apps/api/app/admin/router.py`、`apps/api/app/factory.py`、`apps/api/tests/admin/test_admin_qa.py`、本任务单、`PROJECT_STATE.md`
- 测试命令及结果：`pytest tests/admin/test_admin_qa.py -v`（WSL Docker 容器 IP，隔离 `jianli_auth_001_db` + Redis DB 15）→ **1 passed**；owner 三接口 200 且内容/计数正确，interviewer 三接口均 403
- lint / typecheck：任务路径 Ruff PASS；`mypy app` PASS（46 source files / 0 error）
- DB 迁移：不涉及
- 未解决风险：质量/延迟/grounding 指标另走 CR + migration，不得混入
- 是否偏离 TASK：否
- 建议审查重点：RBAC、真实列名、消息跨用户泄漏边界
- verified_commit：`741c242`
