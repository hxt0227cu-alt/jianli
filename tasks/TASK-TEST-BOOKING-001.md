# TASK-TEST-BOOKING-001 TC-APT-003 轮次隔离兼容性修正

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5；SRS 1.3 / OpenAPI 0.2 / test_plan 0.2（均 approved）
- 基线 commit：`9dc6379`
- 触发证据：BOOKING-001 真实 PostgreSQL 首轮验证为 7 passed / 1 failed；TC-APT-003 第二轮起 `notification_events` / `audit_logs` 跨轮累积。

## 精确规范引用
- AGENTS.md §7（冻结验收测试必须由独立测试变更任务修改）
- test-plan TC-APT-002 / TC-APT-003
- migration `0002_booking_schema`、`0003_outbox_audit_schema` 的实际 FK 定义

## 目标
- 修正 BOOKING 冻结集成测试的每轮数据库清理，使无 FK 的 `notification_events.biz_id` 与 `audit_logs.target` 不跨轮累积。

## 非目标
- 不修改任何生产代码、migration、schema、规范或公开契约。
- 不改变 TC-APT-001～003 的断言、并发轮数、成功/失败判定或真实 PostgreSQL 要求。
- 不用 mock、skip、放宽计数或只运行单轮绕过失败。

## 允许修改路径
- `apps/api/tests/appointments/test_booking.py`
- `tasks/TASK-TEST-BOOKING-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/app/**`
- `apps/api/migrations/**`
- `docs/**`、`docs/baseline.yml`
- 其他测试文件与 TASK-BOOKING-001 冻结验收口径

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无。
- 仅允许测试 fixture/轮次 setup 显式清理 `audit_logs`、`notification_events` 及其余预约测试数据；不得修改表结构或生产清理逻辑。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：测试隔离缺陷修正，不改变任何验收期望或用户可观察行为。

## 功能验收
- TC-APT-003 连续至少 10 轮，每轮初始数据库状态一致；仅一个并发请求成功，另一返回 `SLOT_TAKEN`。
- 每轮成功后仍严格断言 1 Appointment、3 booked Slot、2 NotificationEvent、1 AuditLog；不得改为累计值或宽松比较。
- 全套预约测试无新增 skip，AUTH/migration 回归不受影响。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：20

## 必须运行的测试命令
- 真实 PostgreSQL/Redis TC-APT-001～003；TC-APT-003 连续至少 10 轮。
- 全套 pytest、Ruff、format、mypy、pip check 由恢复后的 BOOKING-001 执行。

## 回滚方法
- `git revert` 本测试兼容性提交；不涉及 migration down。

## 强制停止条件
- 需要修改冻结断言、并发轮数、生产代码、schema/API/依赖或超过预算。
- 修正清理后仍出现事务/并发行为失败；应返回 BOOKING-001 实现修正，不得继续改测试。

## 交付证据
- commit / PR：授权提交 `bd433cc`（本分支引入为 `c624780`）；测试兼容性提交 `b8b241f`
- 修改文件清单：`apps/api/tests/appointments/test_booking.py`、本任务、`PROJECT_STATE.md`
- 测试命令及结果：一次性真实 PostgreSQL 16 + Redis 7 环境执行 `pytest tests/appointments -q` → 8 passed / 0 failed / 0 skipped；TC-APT-003 完整 10 轮
- lint / typecheck：由 BOOKING-001 全套验证回填
- DB 迁移验证：无 schema 变更；同一一次性空库 `0001 → 0002 → 0003` upgrade 通过
- 验收证据：每轮仍严格断言 1 Appointment、3 booked Slot、2 NotificationEvent、1 AuditLog；并发结果保持 201 + `SLOT_TAKEN`
- 变更预算实际值：3 个文件；生产代码 0 行；测试代码 `+10/-6`
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`b8b241f`
- 状态：Closed

## 关联
- 被阻塞任务：TASK-BOOKING-001
- 缺陷来源：冻结 TC-APT-003 测试 fixture 未清理无 FK 的 Outbox/Audit 行
