# TASK-TEST-DB-002-REFERENTIAL 预约域 enum 与外键验收

## 任务类型
- test

## 当前阶段
- 状态：Closed
- 拆分原因：`TASK-TEST-DB-002-CONSTRAINTS` 完整覆盖经 Ruff 格式化后仍超过 190 行预算；本任务独立承载 enum/FK 拒绝路径，不事后上调原预算。

## 基线版本与基线 commit
- baseline：领域模型 1.1.5 / test_plan 0.2（approved）
- 基线 commit：`b314b42`

## 精确规范引用
- `docs/design/domain-model.md` §6.5～§6.9、§6.17
- `docs/reviews/db-002-migration-plan.md` 验证矩阵
- TC-OPS-002、TC-APT-007～011 的数据层约束前置条件

## 目标
- 在真实 PostgreSQL 中验证 DB-002 三个 enum 与普通 FK 的拒绝路径。

## 非目标
- 不修改 migration、冻结断言、唯一/CHECK 测试、业务代码、API 或规范。

## 允许修改路径
- `apps/api/tests/migrations/test_booking_referential.py`
- `tasks/TASK-TEST-DB-002-REFERENTIAL.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/api/migrations/**`、`apps/api/app/**`、`apps/web/**`
- approved 规范正文、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；仅验证用户已批准 DB-002 评审包列明的三个 enum 与普通 FK。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：测试拆分，不改变产品或数据库契约。

## 验收
- `appointment_status`、`slot_status`、`availability_override_action` 非法值均被拒绝。
- 缺失普通 FK 被拒绝；真实 PostgreSQL 零 skip，不使用 mock。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：90

## 必须运行的测试命令
- `python -m pytest tests/migrations -q -ra`
- Ruff check/format、pip check

## 回滚方法
- 回退测试文件；无数据库变更。

## 强制停止条件
- 需要新约束/字段/API/依赖、降低冻结断言、真实测试失败或超过预算。

## 交付证据
- commit / PR：任务建立 `366063a`；实现 `280ba83`
- 修改文件清单：`apps/api/tests/migrations/test_booking_referential.py`、`tasks/TASK-TEST-DB-002-REFERENTIAL.md`、`PROJECT_STATE.md`
- 测试命令及结果：真实 PostgreSQL migration 测试 22 passed / 0 skipped；三个 enum 与缺失 FK 均被数据库拒绝
- lint / typecheck：Ruff check/format pass；pip check pass
- DB 迁移验证：与 TASK-DB-002 共用一次性 PostgreSQL
- 验收证据：`appointment_status`、`slot_status`、`availability_override_action` 非法值与缺失普通 FK 路径通过
- 变更预算实际值：3/3 文件；生产 0/0 行；测试 90/90 行
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`2fd1199`
- 状态：Closed

## 关联
- 来源：`TASK-TEST-DB-002-CONSTRAINTS`
