# TASK-REVIEW-DB-003 DB-003 独立迁移审查

## 任务类型
- test / review

## 目标
- 独立检查 DB-003 的 DDL、可逆性、Schema 精确性、真实 PostgreSQL 测试和范围预算。

## 审查对象
- TASK-DB-003 最终实现 commit（待回填）
- 领域模型 §6.11/§6.15、架构 §4.1、TC-APT-001～003

## 允许修改路径
- `tasks/TASK-REVIEW-DB-003.md`（仅审查证据；审查角色不修改 migration 或测试）

## 必查项
- 两表、两 enum、字段类型/nullability、UK/index 与 `a6e06ea` 逐项一致。
- downgrade 不删除 DB-001/DB-002 对象；无 FK/trigger/function/extension/server default。
- 未新增依赖、API、业务代码、NotificationDelivery 或外部调用。
- 真实 PostgreSQL migration 测试零 skip；预算真实；`sleep202603-an` 零修改。

## 交付证据
- 审查结论：待回填
- findings：待回填
- verified_commit：待回填
- 状态：Open
