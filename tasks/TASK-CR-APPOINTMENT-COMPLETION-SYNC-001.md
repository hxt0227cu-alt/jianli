# TASK-CR-APPOINTMENT-COMPLETION-SYNC-001 完成状态飞书同步规格变更

> 状态：Approved（用户于 2026-08-26 明确要求管理员查看公司/预约时间，并同步飞书多维表格以整理已面试/未面试；此前已授权完成全部修复）。

## 任务类型
- documentation
- change_request
- migration_design

## 基线版本与基线 commit
- baseline：PRD 2.3.5 / 用例 1.7.3 / 领域模型 1.1.7 / SRS 1.6 / 测试计划 0.4
- 基线 commit：`868ffdc`

## 精确规范引用
- PRD R14 / §8.10.2
- UC-10 / UC-11 / UC-23
- SRS §3.6 / §3.8 / §6.2
- domain-model §5 / §6.12
- TC-NOTIFY-011 / TC-OPS-002

## 目标
- 自动完成预约时同事务写 `appointment_completed` Outbox 事实事件。
- Worker 只将该事件同步到飞书多维表格，更新状态为 completed；不向候选人/面试官发送完成邮件或飞书私信。
- 管理端继续展示公司、预约时间与 active/completed/cancelled 状态。

## 非目标
- 不新增公开 API、数据库表/字段、DeliveryPurpose 或外部依赖。
- 不发送“面试已完成”通知，不改变现有新建/改期/取消通知。

## 允许修改路径
- baseline、PRD、use-cases、SRS、domain-model、test-plan、本任务单。

## 禁止修改路径
- `apps/**`、OpenAPI、UI 线框、依赖清单。

## 已批准的 DB / API / 依赖变更
- DB：批准 0010 可逆迁移，为既有 PostgreSQL enum `notification_event_type` 新增 `appointment_completed`；downgrade 删除该类型事件及其级联 Delivery 后重建旧 enum。
- API：无。
- 依赖：无。

## 规范影响评估
- behavior_change：true；PRD/use-cases/SRS/domain/test-plan update。

## 功能验收
- completion 事务同时更新 Appointment 并写唯一 Outbox 事件。
- Worker 对 completion 只 upsert 飞书多维表格，不发送 email/IM 消息。
- 重跑幂等；飞书失败沿用 delivery failed + 告警/重试。

## 变更预算
- max_files：7
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 规范一致性 rg；`git diff --check`。

## 回滚方法
- 回退规格；实现阶段按 0010 downgrade 回退 enum。

## 强制停止条件
- 遵循 `AGENTS.md §2`。

## 交付证据
- commit / PR：`13b5c06`
- 修改文件清单：`docs/baseline.yml`、`docs/requirements/PRD.md`、`docs/requirements/use-cases.md`、`docs/requirements/SRS.md`、`docs/design/domain-model.md`、`docs/test/test-plan.md`、`tasks/TASK-CR-APPOINTMENT-COMPLETION-SYNC-001.md`
- 测试命令及结果：规范关键词一致性检查通过；`git diff --check` 通过
- lint / typecheck：不适用
- DB 迁移验证：设计为可逆，实测在实现任务
- 验收证据：PRD/用例/SRS/领域模型/测试计划均明确完成事件仅同步飞书多维表格，不发送 email/IM
- 变更预算实际值：7 files / 规范与治理文档变更
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`13b5c06`

## 关联
- `TASK-APPOINTMENT-WINDOW-001`
