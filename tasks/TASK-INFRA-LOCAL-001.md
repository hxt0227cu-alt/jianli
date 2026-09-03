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
- commit / PR：`8a76936`（任务建立）；被验证实现快照=`2179821`
- 环境：PostgreSQL 17.6 官方 Windows 页面指向的 EDB portable archive；SHA-256=`D378882ABD001A186735ACD6F6BA716BCA6CCD192E800412D4FD15ED25376B3E`；Python 3.12.13 临时 venv；实例仅监听 `127.0.0.1` 随机高端口
- 测试与迁移结果：`pytest tests/migrations -q -ra` → 10 passed / 0 skipped；真实 `upgrade → downgrade → upgrade` 通过；降级残留检查与最终 revision/6 表重建通过；Ruff/format/mypy/pip check 全部通过
- 实例停止/数据目录删除：最终 PostgreSQL PID、监听端口、关联进程均为 0；临时根目录 `C:\Users\<user>\AppData\Local\Temp\jianli-task-infra-local-001-7b037ffbc9c94b64a6bc14ee11aedef5` 已删除，data、归档、解压二进制、venv、口令文件和日志均不存在
- 敏感信息：数据库 URL 与随机口令未提交、未回填到仓库；未连接公网或生产数据库
- 未解决风险：无
- 是否偏离 TASK：否
- verified_commit：`2179821`
- 状态：Closed
- 关闭结论：一次性本地验收环境已完成任务且完全清理，不保留常驻 PostgreSQL 或数据。
