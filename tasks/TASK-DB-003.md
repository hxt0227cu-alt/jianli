# TASK-DB-003 预约创建 Outbox 与审计表迁移评审

## 任务类型
- migration

## 当前阶段
- 状态：Closed
- 用户批准：2026-08-11 用户明确批准 `a6e06ea` 的 DB-003 迁移方案，授权按评审包实施；仅限一次性测试库，不含生产迁移。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.2 / test_plan 0.2（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`37430e6`

## 精确规范引用
- `docs/design/domain-model.md` §6.11、§6.15
- `docs/design/architecture.md` §4.0～§4.1
- `docs/requirements/SRS.md` §3.5、§5.1～§5.3、§8
- `docs/test/test-plan.md` TC-APT-001～003
- OpenAPI operationId：`previewAppointment`、`createAppointment`

## 需求来源
- BOOKING-001 的冻结前置条件：TC-APT-002 要求预约事务同时写 Appointment、3 Slot、NotificationEvent、AuditLog。

## 目标
- 以一份可逆 migration 创建 `notification_events` 与 `audit_logs`、两组 enum 及 approved 约束，解除 BOOKING-001 的持久化阻塞。

## 非目标
- 不实现 Repository、API、预约事务、SSE、NotificationDelivery、Worker、外部通知或生产部署。
- 不修改已批准规范，不执行生产数据库变更。

## 允许修改路径
- `apps/api/migrations/versions/0003_outbox_audit_schema.py`
- `apps/api/tests/migrations/test_outbox_audit_schema.py`
- `docs/reviews/db-003-outbox-audit-plan.md`
- `tasks/TASK-DB-003.md`
- `tasks/TASK-REVIEW-DB-003.md`
- `PROJECT_STATE.md`（仅任务态与阻塞）

## 禁止修改路径
- `apps/api/app/**`、`apps/web/**`、`infra/**`、approved 规范正文
- `apps/api/migrations/versions/0001_identity_schema.py`、`0002_booking_schema.py`
- `sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB：新增 enum `notification_event_type` 与 `notification_event_status`，标签严格按 `a6e06ea` 评审包。
- DB：新增 `notification_events` 与 `audit_logs` 两表，字段类型和 NULL/NOT NULL 严格按评审包。
- DB：新增 `notification_events.idempotency_key` UNIQUE、`ix_notification_events_biz_id` 与部分索引 `ix_notification_events_pending_schedule`。
- DB：新增可逆 `0003_outbox_audit_schema`，down revision=`0002_booking_schema`；不新增 FK/trigger/function/extension/server default。
- API/SSE/依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只把 approved 领域实体整理为待人工批准的物理迁移方案。

## 验收
- migration 只含 `notification_events` 与 `audit_logs`，逐字段对齐已批准评审包。
- 两个 enum、UNIQUE、两个普通/部分索引及 NULL/NOT NULL 在真实 PostgreSQL 逐项验证。
- `upgrade head → downgrade 0002_booking_schema → upgrade head` 可逆，DB-001/DB-002 数据不受影响。
- NotificationDelivery、通知发送或外部调用不进入本批。

## 变更预算
- max_files：6
- expected_prod_lines：180
- expected_test_lines：240

## 必须运行的测试命令
- 一次性真实 PostgreSQL：`alembic upgrade head` → `alembic downgrade 0002_booking_schema` → `alembic upgrade head`
- `python -m pytest tests/migrations -q -ra`，零 skip
- Ruff check/format、mypy、pip check

## 回滚方法
- 仅在一次性测试库执行 `alembic downgrade 0002_booking_schema`；生产 downgrade 另行人工批准。

## 强制停止条件
- 需要新增评审包未列明的字段/状态/FK/索引/依赖/API；冻结测试失败；超过预算。

## 交付证据
- commit / PR：评审包 `a6e06ea`；批准范围登记 `9d99992`；实现 `2a7e33a`；测试隔离修正 `4f3b74c`
- 修改文件清单：`docs/reviews/db-003-outbox-audit-plan.md`、`apps/api/migrations/versions/0003_outbox_audit_schema.py`、`apps/api/tests/migrations/test_outbox_audit_schema.py`、`tasks/TASK-DB-003.md`、`tasks/TASK-REVIEW-DB-003.md`、`PROJECT_STATE.md`
- 测试命令及结果：真实 PostgreSQL migration 测试连续两遍均 26 passed / 0 skipped；全套 42 passed / 1 skipped（仅 AUTH 需要 Redis，与 DB-003 无关）
- lint / typecheck：Ruff check/format pass；mypy 16 source files / 0 issues；pip check pass
- DB 迁移验证：`upgrade head → downgrade 0002_booking_schema → upgrade head` 通过；最终 revision=`0003_outbox_audit_schema`
- 验收证据：两表、两 enum、字段/nullability、UNIQUE、两个索引及部分谓词通过；真实库 server defaults/FK/triggers 均为 0；独立审查 P0/P1/P2=0
- 变更预算实际值：6/6 文件；生产 79/180 行；测试 206/240 行
- 未解决风险：无任务阻塞风险；14 条既存 Alembic `path_separator` 弃用警告不影响 DDL
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`4f3b74c`
- 状态：Closed

## 关联
- 前置：TASK-DB-002（Closed，verified_commit=`2fd1199`）
- 后续：TASK-BOOKING-001
