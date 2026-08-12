# TASK-TEST-BOOKING-002 BOOKING 独立审查覆盖缺口修正

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5；SRS 1.3 / OpenAPI 0.2 / test_plan 0.2（均 approved）
- 被审查实现：`9374a91cd9d332c9dc81c87f8faa16fda5b814d5`
- 独立审查：`ae651c5cda8e4d5062b3e7fe0755d49b5105e30f`，P0=0 / P1=2 / P2=2

## 精确规范引用
- AGENTS.md §7
- test-plan TC-APT-003、TC-AUTH-006、TC-AUTH-008
- TASK-REVIEW-BOOKING-001 P1 findings

## 目标
- 补强真实并发与预约端点安全验收证据，不改变既有断言和用户可观察行为。

## 非目标
- 不修改生产代码、migration、schema、规范、API、依赖或原有成功判定。
- 不用 mock 数据库/Redis 替代真实服务，不降低并发轮数，不添加 skip。

## 允许修改路径
- `apps/api/tests/appointments/test_booking.py`
- `tasks/TASK-TEST-BOOKING-002.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/app/**`、`apps/api/migrations/**`、`docs/**`、`docs/baseline.yml`
- 既有 TC-APT-001～003 断言的删除、放宽或 mock 化

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无。
- 只允许增加测试级并发同步/观测与端点安全断言；不得在生产代码增加测试 hook。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：补足已批准验收项的真实性与异常路径覆盖，不改变标准。

## 功能验收
- TC-APT-003：两个请求使用两个不同 PostgreSQL backend PID，并通过测试侧屏障证明同时到达 Slot `FOR UPDATE` 前；连续至少 10 轮仅一方成功。
- loser 完整回滚：最终恰好 1 Company、1 Appointment、3 个 Slot 全部 `booked` 且归属 winner、2 Event、1 AuditLog；无 loser 公司/预约/事件/审计残留。
- TC-AUTH-008：两个预约 POST 均覆盖匿名、owner_admin、错误/缺失 CSRF、跨源拒绝；合法 interviewer 成功路径不变。
- TC-AUTH-006：create 的 Redis 故障 fail closed，返回 approved `RATE_LIMITED` Problem；preview 不消耗预约提交配额。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：160

## 必须运行的测试命令
- 真实 PostgreSQL/Redis 预约套件；TC-APT-003 连续至少 10 轮。
- 全套 pytest、Ruff、format、mypy、pip check 由恢复后的 BOOKING-001 最终快照执行。

## 回滚方法
- `git revert` 本测试增强提交；无数据库回滚。

## 强制停止条件
- 需要生产 test hook、修改原断言、schema/API/依赖或超过预算。
- 增强后暴露实现失败：返回 BOOKING-001 修代码，不得调整测试规避。

## 交付证据
- commit / PR：授权提交 `519892b`；测试增强 `90884af`；生产修正与最终测试固定提交 `4d5381a`；未创建 PR
- 修改文件清单：`apps/api/tests/appointments/test_booking.py`、`tasks/TASK-TEST-BOOKING-002.md`、`PROJECT_STATE.md`
- 测试命令及结果：第二轮证据修正使用真实 WSL PostgreSQL 16.14 / Redis 7.0.15 执行 `pytest tests/appointments -q` → 14 passed / 0 skipped；全套 `pytest -q` → 57 passed / 0 failed / 0 skipped；`b41b28c` 中 13 passed 为计数笔误
- lint / typecheck：`ruff check .` → pass；`ruff format --check .` → 38 files formatted；`mypy app` → 22 source files / 0 issues；`pip check` → no broken requirements
- DB 迁移验证：无 schema 变更；使用一次性真实 PostgreSQL，全套 26 个 migration 用例通过，独立空库显式 `upgrade head → downgrade base → upgrade head` 通过
- 验收证据：TC-APT-003 连续 10 轮均观测两个不同 `pg_backend_pid()` 且屏障同时到达 Slot `FOR UPDATE` 前；每轮一个 201、一个 `SLOT_TAKEN`，最终 1 Company / 1 Appointment / 3 winner-owned booked Slot / 2 Event / 1 AuditLog；两个 POST 的匿名、owner_admin、缺失/错误 CSRF、跨源拒绝与合法 interviewer 路径通过；create Redis 故障返回 approved `RATE_LIMITED` Problem，preview 不消耗 create 配额
- 变更预算实际值：3 个允许路径；生产 0 行；测试增强提交相对父提交 `test_booking.py +156/-17`，新增 156 行低于 160 行预算
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`4d5381a`
- 状态：Closed（2026-08-12）
- 第二轮证据修正状态：证据计数已向前修正，等待第三轮独立复核；任务功能状态仍 Closed

## 关联
- 被阻塞任务：TASK-BOOKING-001
- 独立审查：TASK-REVIEW-BOOKING-001 `ae651c5`
