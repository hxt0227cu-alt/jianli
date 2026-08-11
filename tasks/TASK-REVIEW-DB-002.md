# TASK-REVIEW-DB-002 DB-002 独立迁移审查

## 任务类型
- test / review

## 目标
- 独立检查 DB-002 的 DDL、锁文件边界、可逆性、Schema 精确性、真实 PostgreSQL 测试和范围预算。

## 审查对象
- TASK-DB-002 最终实现 commit `2fd1199`（含实现 `280ba83` 与回归补齐）
- TC-OPS-002、领域模型 §6.5～§6.9/§6.17

## 允许修改路径
- `tasks/TASK-REVIEW-DB-002.md`（仅审查证据；审查角色不修改 migration 或测试）

## 必查项
- 五表、三 enum、字段类型/nullability、FK/UK/CHECK/index 与批准评审包逐项一致。
- downgrade 不删除 DB-001 身份域对象；无 trigger/function/extension/新依赖/API/业务代码。
- 冻结测试真实 PostgreSQL 零 skip，未改宽断言或用 mock 替代迁移。
- 文件数与代码行预算真实；`sleep202603-an` 零修改。

## 交付证据
- 审查结论：通过；独立只读审查最终 P0=0、P1=0、P2=0
- findings：首次审查发现 `uq_active_company` 不同例外放行正向路径缺口（P2）；`2fd1199` 在 188/190 行预算内补齐，增量复核确认关闭；DDL、downgrade、依赖与范围均无其它发现
- verified_commit：`2fd1199`
- 状态：Closed
