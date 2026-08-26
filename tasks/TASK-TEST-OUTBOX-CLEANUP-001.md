# TASK-TEST-OUTBOX-CLEANUP-001 Outbox 迁移测试清理夹具同步

> 状态：In Progress（2026-08-26）。

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
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 关闭门禁：In Progress
