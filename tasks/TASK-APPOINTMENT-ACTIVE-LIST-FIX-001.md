# TASK-APPOINTMENT-ACTIVE-LIST-FIX-001 取消预约后本人列表 500 修复

> 状态：In Progress（2026-08-31）。用户在完成上线前全量测试后明确要求修复全部上线阻塞。

## 任务类型
- implementation（既有行为缺陷修复）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / OpenAPI 0.9 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/requirements/SRS.md` §3.6、§7
- `docs/api/openapi.yaml` operationId `listMyAppointments`
- `docs/test/test-plan.md` TC-APT-004、TC-APT-005、TC-SEC-005
- 冻结复现：`apps/api/tests/appointments/test_management.py::test_list_my_returns_only_own_active_appointments`

## 需求来源
- 当前用户只能查看并管理自己的预约；已取消终态不得因已释放 Slot 被反序列化而使接口 500，已自动完结记录仍应可查看。

## 目标
- 让 `listMyAppointments` 返回当前用户的 active/completed 预约，排除 cancelled 记录；取消后再次查询稳定返回 200 空列表。

## 非目标
- 不改变取消事务、Slot 释放、通知、飞书同步或历史保留策略。
- 不新增历史预约公开 API，不修改前端。

## 允许修改路径
- `apps/api/app/appointments/service.py`
- `apps/api/tests/appointments/**`（仅允许新增实现回归；冻结复现断言不得修改）
- `tasks/TASK-APPOINTMENT-ACTIVE-LIST-FIX-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/migrations/**`
- `docs/api/**`、`docs/requirements/**`、`docs/design/**`
- 认证、加密、通知、Agent 工具实现

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无；恢复 approved `listMyAppointments` 当前预约语义。
- 依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：Bug 修复使实现重新符合既有 SRS/OpenAPI 与冻结测试。

## 功能验收
- active/completed 本人预约正常返回；他人预约不可见。
- 取消本人预约后再次 GET `/appointments` 返回 200 且 `items=[]`。
- cancelled 终态不会进入列表或触发 Slot 数量模型错误；过期预约自动转 completed 后仍可查看且不阻塞新建。

## 安全与隐私验收
- SQL 仍强制 `user_id` 归属过滤，不扩大可见范围。

## 性能验收
- 使用现有索引过滤；不得引入逐条额外查询以外的新复杂度。

## 变更预算
- max_files：4
- expected_prod_lines：≤ 10
- expected_test_lines：≤ 30

## 必须运行的测试命令
- `pytest tests/appointments/test_management.py -q`
- `pytest tests/appointments/test_booking.py tests/appointments/test_security.py -q`
- `ruff check app/appointments tests/appointments`
- `mypy app`

## 回滚方法
- 回退本任务对查询条件的修改；无数据迁移。

## 强制停止条件
- 需要新增 API、迁移、依赖、状态或改变历史保留策略。
- 冻结复现测试仍失败或需修改断言。
- 超出变更预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
