# TASK-BACKUP-RESTORE-IMPLEMENTATION-019 备份恢复实现独立收口

> 状态：In Progress（2026-08-31）。从超预算的运维合并任务中按文件边界拆出；承接 `TASK-BACKUP-RESTORE-SAFETY-004`，不得与 `TASK-OPS-PRELAUNCH-CONSOLIDATED-013` 重复计算。

## 任务类型
- implementation / operations security（不改变产品契约）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/design/architecture.md` §9.3～§9.4
- `docs/design/security.md` §9、§12
- `docs/test/test-plan.md` TC-OPS-001、TC-OPS-004

## 目标
1. 加密备份在停止知识写入口后，一致导出 PostgreSQL 与 active knowledge 对象，并在退出或信号时恢复服务、清理明文和失败产物。
2. 备份源拒绝 symlink、hardlink、FIFO、Unix socket 与设备节点；归档只允许普通文件/目录。
3. 恢复只接受校验通过的加密包、空白隔离数据库和受控全新目录；解包前拒绝路径穿越、重复、链接、设备与大小/数量炸弹。
4. 保持互斥、原子目录切换、独立恢复凭据和可重复的隔离演练边界。

## 非目标
- 不修改部署 Compose、公开 API、数据库 schema、业务逻辑、加密算法、依赖或真实生产数据。
- 不在本机联网安装工具，不把静态/负向测试冒充真实生产恢复演练。

## 允许修改路径
- `scripts/backup.sh`
- `scripts/restore.sh`
- `tasks/TASK-BACKUP-RESTORE-IMPLEMENTATION-019.md`

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；仅允许显式空白隔离恢复库。
- API：无。
- 依赖：无项目依赖；只使用已列入部署前置条件的 Docker、PostgreSQL 客户端、OpenSSL、flock、coreutils 与 Python 标准库。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：使既有备份恢复运维入口符合已批准的 RPO/RTO 与安全边界。

## 验收
- `bash -n scripts/backup.sh scripts/restore.sh`。
- 普通文件树可归档；symlink、hardlink、FIFO、Unix socket 与设备节点均非零拒绝且不保留失败包或明文。
- 恶意外包/知识归档的绝对路径、`..`、重复、链接、设备、超大小/数量成员均非零拒绝。
- 联网/目标环境就绪后执行正常备份→空白隔离库/新目录恢复，核对表、行数、20 篇语料与 RTO。
- `git diff --check`；`backup.sh`、`restore.sh` 在 Git 中为 `100755`。

## 变更预算
- max_files：3
- expected_prod_lines：≤380
- expected_test_lines：0
- expected_doc_lines：≤80

## 回滚与强制停止
- 回滚：回退本任务三个文件；不删除卷、归档或任何真实数据。
- 停止：需要改 schema/API/加密格式、引入依赖、触达真实生产数据、冻结测试失败或超预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：Shell 语法代替，待回填
- DB 迁移验证：无 schema 迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：真实空白库恢复/RTO 需目标环境
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
