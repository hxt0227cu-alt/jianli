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
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：由 BOOKING-001 最终回归回填
- DB 迁移验证：无 schema 变更；使用一次性真实 PostgreSQL
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Approved for execution

## 关联
- 被阻塞任务：TASK-BOOKING-001
- 独立审查：TASK-REVIEW-BOOKING-001 `ae651c5`
