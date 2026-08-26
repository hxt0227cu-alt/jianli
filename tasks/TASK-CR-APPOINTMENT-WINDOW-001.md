# TASK-CR-APPOINTMENT-WINDOW-001 预约生命周期与三自然周窗口规格变更

> 状态：Approved（用户于 2026-08-26 明确要求过期预约自动作废、预约/管理端统一三自然周排表及精确时间点不可约设置，并要求调整页面布局与字号）。

## 任务类型
- documentation
- change_request

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.6 / SRS 1.5 / OpenAPI 0.6 / 测试计划 0.3
- 基线 commit：`99362de`

## 精确规范引用
- `docs/requirements/PRD.md §4.5`
- `docs/requirements/use-cases.md UC-07 / UC-09 / UC-10 / UC-13`
- `docs/requirements/SRS.md §3.4 / §3.5 / §3.6 / §3.9 / §6.2`
- `docs/design/domain-model.md §5 / §6.6`
- `docs/design/ui-wireframe.md U3 / A4`
- `docs/api/openapi.yaml` `getSlotSnapshot`
- `docs/test/test-plan.md` TC-UI-005 / TC-APT-007

## 目标
1. `active` 预约在 `end_at <= now()` 后自动转为 `completed`，不再占用一人一个 active 预约约束。
2. 可约窗口统一为从明天起至下下周同星期（含首尾）共 15 个自然日，覆盖当前周剩余部分与后续两个自然周。
3. `getSlotSnapshot.week_offset` 扩至 0/1/2；预约与改期 UI 使用同一窗口。
4. 管理端继续复用 `AvailabilityOverride`，读取同一隐私安全 Slot 快照并允许点击格子带入与 Slot 边界对齐的精确起止时间段，设置不可约/恢复可约。
5. 预约页充分使用无聊天栏页面宽度并提升日历、摘要与步骤字号。

## 非目标
- 不新增预约状态、数据库字段、索引或迁移。
- 不新增公开 operationId、外部依赖、通知通道或权限。
- 不改变一人一个 active 预约、Slot 行锁、加密和 Outbox 语义。

## 允许修改路径
- `docs/baseline.yml`
- `docs/requirements/PRD.md`
- `docs/requirements/use-cases.md`
- `docs/requirements/SRS.md`
- `docs/design/domain-model.md`
- `docs/design/ui-wireframe.md`
- `docs/api/openapi.yaml`
- `docs/test/test-plan.md`
- 本任务单

## 禁止修改路径
- `apps/**`、`migrations/**`、依赖清单与部署配置。

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变更；批准既有 Appointment 行的 `active → completed` 自动状态迁移。
- API：批准 `getSlotSnapshot.week_offset` 枚举由 `[0,1]` 扩为 `[0,1,2]`；只读角色由 interviewer 扩为 interviewer/owner_admin，响应 Schema 与隐私安全 ownership 语义不变。
- 依赖：无。

## 规范影响评估
- behavior_change：true
- affected_specs：PRD / use_cases / SRS / domain_model / UI / OpenAPI / test_plan = update
- reason：改变预约有效期与可展示/可预约日期窗口，必须先同步并批准规格。

## 功能验收
- 所有规范统一采用 15 天三自然周窗口，无残留“两完整自然周/14 天”。
- 所有规范统一说明过期 active 自动完成，`completed_at` 置为预约 `end_at`。
- 管理端精确时段 override 与预约端读取同一 Slot 真相源。

## 安全与性能验收
- 不放宽 RBAC/CSRF/PII 遮挡。
- 自动完成使用集合更新或有界查询，不逐行 N+1。

## 变更预算
- max_files：9
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- `rg` 一致性检查：两周/14 天旧口径不得残留在生效规范。
- OpenAPI YAML 解析。

## 回滚方法
- 回退本规格提交；不涉及运行数据。

## 强制停止条件
- 遵循 `AGENTS.md §2`。

## 交付证据
- commit / PR：`2ec808d`（主规格）+ `bc430ca`（管理端同源快照补充）
- 修改文件清单：baseline、PRD、use-cases、SRS、domain-model、ui-wireframe、OpenAPI、test-plan、本任务单（9/9）
- 测试命令及结果：`rg` 生效章节一致性检查通过；OpenAPI version/enum 结构断言通过（文本结构）；`git diff --check` 通过
- lint / typecheck：文档任务不适用
- DB 迁移验证：无迁移
- 验收证据：周三 2026-08-26 示例统一为 2026-08-27 至 2026-09-10；week_offset=[0,1,2]；owner_admin 可读隐私安全快照
- 变更预算实际值：9/9 文件；生产/测试代码 0 行
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`bc430ca`

## 关联
- 实现任务：`TASK-APPOINTMENT-WINDOW-001`
