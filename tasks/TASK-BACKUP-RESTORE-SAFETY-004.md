# TASK-BACKUP-RESTORE-SAFETY-004 备份恢复边界二次加固

> 状态：Superseded（2026-08-31）。实现与最终证据统一由拆分后的 `TASK-BACKUP-RESTORE-IMPLEMENTATION-019` 承接；本单不得独立关闭或宣称预算合规。

## 任务类型
- implementation（运维安全缺陷修复）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/design/architecture.md` §9.3～§9.4
- `docs/design/security.md` §9、§12
- `docs/test/test-plan.md` TC-OPS-004、TC-SEC-007
- `tasks/TASK-DEPLOY-HARDEN-003.md`

## 目标
1. 恢复目标知识目录不得等于生产目录或落在其子目录中。
2. 恢复数据库必须已存在且为空，防止把归档叠加到已有数据。
3. 解包前拒绝路径穿越、符号链接、硬链接、设备文件等特殊成员。
4. 知识卷备份使用 API 镜像必备的 Python 标准库，不再假定 slim 镜像内存在 `tar`；备份窗口短暂停止 API 写入口并核对 active 文档对象完整性。
5. 恢复使用独立角色/密码与受控 restore root，先安全解包到同盘 staging，再单事务恢复并原子切换目录。
6. 备份使用互斥锁与纳秒+PID 文件名，禁止并发进程互相覆盖或误删产物。

## 非目标
- 不修改公开 API、数据库 schema、业务逻辑、加密算法或备份格式后缀。
- 不联网安装工具，不对真实生产库执行恢复。

## 允许修改路径
- `scripts/backup.sh`
- `scripts/restore.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-BACKUP-RESTORE-SAFETY-004.md`

## 禁止修改路径
- `apps/**`、`docker-compose*.yml`、迁移、需求与接口规范、依赖清单。

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；仅允许连接显式指定的空白隔离恢复库进行演练。
- API：无。
- 依赖：无项目依赖；复用目标 Linux 的 `docker`、`python3`、`psql`、`pg_dump`、`pg_restore`、`tar`、`sha256sum`、`openssl`、`flock`。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：收紧既有备份恢复运维入口，不改变产品可观察行为。

## 验收
- 正常加密备份可恢复到空白隔离 DB 与全新隔离目录。
- 生产知识目录及其子目录、非空 DB、路径穿越与特殊类型归档均被拒绝。
- API 容器内无 `tar` 时知识卷仍可由 Python 标准库流式归档。
- 备份期间 API 短暂停写，active/indexed DB 清单在加密前必须全部存在于知识归档；退出时恢复原运行状态。
- staging/最终目录限定在受控 restore root，且恢复凭据与生产不同。
- 临时明文与失败输出仍会清理，secret 不进入日志。

## 变更预算
- max_files：4
- expected_prod_lines：≤ 90
- expected_test_lines：0
- expected_doc_lines：≤ 30

## 必须运行的测试命令
- `bash -n scripts/backup.sh scripts/restore.sh`
- 缓存镜像下隔离 DB/知识目录备份→恢复演练
- 非空 DB、生产目录子路径、危险归档成员拒绝演练
- `git diff --check`

## 回滚方法
- 回退本任务脚本与文档改动；不删除任何真实数据或卷。

## 强制停止条件
- 需要改变加密算法、公开契约、schema、引入项目依赖或触达真实生产数据。
- 冻结验收失败或超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用（Shell 语法与演练代替）
- DB 迁移验证：无 schema 迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
