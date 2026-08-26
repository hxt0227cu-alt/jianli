# TASK-TEST-OUTBOX-CLEANUP-001 Outbox 迁移测试清理夹具同步

> 状态：Closed（2026-08-26，verified_commit=`7563965`）。

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 领域模型 1.1.6 / SRS 1.5 / OpenAPI 0.6
- 基线 commit：`ac0f087`

## 精确规范引用
- migration `0008_notification_deliveries`
- `tests/migrations/test_outbox_audit_schema.py` 既有清理夹具
- 用户对全部当前发布修复的显式授权

## 目标
使旧 outbox 迁移测试夹具在新增 delivery 外键后仍能可靠清理数据，不改变任何验收断言。

## 非目标
- 不修改业务实现、迁移、schema、API、依赖或断言。

## 允许修改路径
- `tests/migrations/test_outbox_audit_schema.py`
- `tasks/TASK-TEST-OUTBOX-CLEANUP-001.md`

## 禁止修改路径
- 除上述路径外全部文件。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：仅同步测试 teardown 与既有外键关系。

## 功能验收
- 原有 4 个 outbox/audit migration 测试断言不变并全部通过。

## 安全与隐私验收
- 只操作专用测试库。

## 性能验收
- 不适用。

## 变更预算
- max_files：2
- expected_prod_lines：0
- expected_test_lines：≤3

## 必须运行的测试命令
- `JIANLI_TEST_DATABASE_URL=.../jianli_tc_ops_002_db pytest tests/migrations/test_outbox_audit_schema.py -q`

## 回滚方法
- `git revert` 本任务提交。

## 交付证据
- commit / PR：`7563965`
- 修改文件清单：测试夹具与任务单 2 文件。
- 测试命令及结果：`test_outbox_audit_schema.py` 4 passed；同专库其余 migration 套件 26 passed 后仅该旧 teardown 失败，修复后归零。
- lint / typecheck：Ruff passed；Mypy 47 source files / 0 error。
- DB 迁移验证：专用 `jianli_tc_ops_002_db` 上 0001–0009 up/down 回归通过。
- 验收证据：清理语句同时 truncate 子表 `notification_deliveries`、父表 `notification_events` 与 `audit_logs`，原断言未变。
- 变更预算实际值：2/2 文件，生产 0 行，测试 3 新增 / 1 删除。
- 未解决风险：无。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`7563965`
- 关闭门禁：Closed
