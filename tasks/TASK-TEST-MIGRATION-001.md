# TASK-TEST-MIGRATION-001 冻结迁移测试向后兼容修正

## 任务类型
- test / approved test maintenance

## 当前阶段
- 状态：Closed
- 用户批准：2026-08-11 明确批准迁移冻结测试兼容性修正。

## 基线版本与基线 commit
- baseline：领域模型 1.1.5 / test_plan 0.2（approved）
- 基线 commit：`5e49d48`

## 精确规范引用
- `docs/test/test-plan.md` TC-OPS-002
- `tasks/TASK-DB-001.md` 已关闭证据
- `docs/reviews/db-002-migration-plan.md` 已批准新增五表范围

## 目标
- 把 DB-001 身份域测试从“数据库 head 只能有六张业务表”修正为“DB-001 六张身份域表必须完整存在”，使冻结测试可兼容合法后续 migration。

## 非目标
- 不删除、跳过或放宽 DB-001 的列、类型、nullability、PK/FK/UK/index/enum/约束断言。
- 不修改 migration、DB-002 新表测试、依赖、业务代码或规范正文。

## 允许修改路径
- `apps/api/tests/migrations/test_identity_schema.py`
- `tasks/TASK-TEST-MIGRATION-001.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/api/migrations/**`、`apps/api/app/**`、`apps/web/**`
- approved 规范正文、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无。
- frozen test：用户批准仅将 `set(get_table_names()) == DOMAIN_TABLES | {alembic_version}` 改为等价的子集断言 `set(get_table_names()) >= DOMAIN_TABLES`；其它断言不得改变。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：测试维护以适配 approved 增量 migration，不改变产品行为或验收方向。

## 验收
- DB-001 六表仍逐一存在，所有身份域精确断言保持不变。
- DB-002 新增表不再使身份域测试因“存在额外合法表”而失败。
- TC-OPS-002 真实 PostgreSQL 零 skip。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：2

## 必须运行的测试命令
- `python -m pytest tests/migrations -q -ra`（与 DB-002 真实数据库验证合并执行）
- Ruff check/format

## 回滚方法
- 回退本任务测试修正；不涉及数据库变更。

## 强制停止条件
- 需要修改除表集合断言外的冻结断言、出现测试失败或超过预算。

## 交付证据
- commit / PR：任务建立 `7b26f4b`；兼容修正 `c85bdf3`；Ruff 等价语法规范化随 `280ba83`
- 修改文件清单：`apps/api/tests/migrations/test_identity_schema.py`、`tasks/TASK-TEST-MIGRATION-001.md`、`PROJECT_STATE.md`
- 测试命令及结果：真实 PostgreSQL migration 测试 22 passed / 0 skipped；身份域列、类型、PK/FK/UK/index/enum 精确断言未改
- lint / typecheck：Ruff check/format pass；mypy 0 issues
- DB 迁移验证：无独立 migration；与 DB-002 真实 up/down/up 一并验证
- 验收证据：DB-002 合法新增表存在时，身份域六表子集断言通过；down base 后身份域仍严格清空
- 变更预算实际值：3/3 文件；生产 0/0 行；测试 1/2 行
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`2fd1199`
- 状态：Closed
