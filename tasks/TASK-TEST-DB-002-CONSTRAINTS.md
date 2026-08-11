# TASK-TEST-DB-002-CONSTRAINTS 预约域数据库约束验收

## 任务类型
- test

## 当前阶段
- 状态：In Progress
- 拆分原因：DB-002 测试经 Ruff 格式化后超过 320 行预算，按硬规则拆分，不事后上调预算。

## 基线版本与基线 commit
- baseline：领域模型 1.1.5 / test_plan 0.2（approved）
- 基线 commit：`7b26f4b`

## 精确规范引用
- `docs/design/domain-model.md` §6.5～§6.9、§6.17
- `docs/reviews/db-002-migration-plan.md` 验证矩阵
- TC-OPS-002、TC-APT-007～011 的数据层约束前置条件

## 目标
- 在真实 PostgreSQL 中验证 DB-002 的唯一约束、CHECK、enum 与 FK 拒绝路径。

## 非目标
- 不修改 migration、冻结断言、业务代码、API 或规范。

## 允许修改路径
- `apps/api/tests/migrations/test_booking_constraints.py`
- `tasks/TASK-TEST-DB-002-CONSTRAINTS.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/api/migrations/**`、`apps/api/app/**`、`apps/web/**`
- approved 规范正文、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；仅测试用户已批准 DB-002 评审包列明的约束。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：实现 approved 测试矩阵，不改变产品或数据库契约。

## 验收
- 重复公司指纹、active user/company、未消费例外、例外重复使用、Slot 起止/时长均被对应约束拒绝。
- Override 空/反向范围、非法 enum、缺失 FK 被拒绝。
- 真实 PostgreSQL 零 skip；不使用 mock。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：190

## 必须运行的测试命令
- `python -m pytest tests/migrations -q -ra`
- Ruff check/format、pip check

## 回滚方法
- 回退测试文件；无数据库变更。

## 强制停止条件
- 需要新约束/字段/API/依赖、降低冻结断言、真实测试失败或超过预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：与 TASK-DB-002 共用一次性 PostgreSQL
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open
