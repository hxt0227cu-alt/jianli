# TASK-INFRA-LOCAL-001 临时 PostgreSQL 迁移验收环境

## 任务类型
- migration

## 目标
- 在本机临时目录启动仅供 `TASK-DB-001` 使用的 PostgreSQL 实例，完成迁移 `upgrade → downgrade → upgrade` 与约束验收后停止并删除全部数据目录。

## 基线与引用
- 基线 commit：`688e5c7e559a1fc6de1b35879155c90b49043da1`
- `tasks/TASK-DB-001.md`
- `docs/test/test-plan.md` TC-OPS-002

## 允许修改/创建
- `tasks/TASK-INFRA-LOCAL-001.md`（本任务证据）
- 本机临时目录（不纳入 Git）

## 禁止
- 不修改 `sleep202603-an`、生产配置、云资源或仓库业务代码。
- 不提交数据库数据目录、密码、连接串或运行日志中的敏感值。

## 变更预算
- max_files：1 个仓库文件；生产代码 0；测试代码 0。

## 强制停止
- 需要付款、云资源、外部数据库、不可逆外部操作或发现端口/数据目录无法安全限定。
- 临时实例无法在验证后停止并删除，或迁移验证失败。

## 交付证据
- commit / PR：待回填
- 测试与迁移结果：待回填
- 实例停止/数据目录删除：待回填
- 状态：Open

