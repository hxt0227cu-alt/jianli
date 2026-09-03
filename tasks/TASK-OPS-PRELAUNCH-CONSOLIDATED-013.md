# TASK-OPS-PRELAUNCH-CONSOLIDATED-013 上线运维安全合并收口

> 状态：In Progress（2026-08-31）。用户已授权修复全部上线阻塞；本单合并承接 `TASK-DEPLOY-HARDEN-003`、`TASK-DEPLOY-RELEASE-BLOCKERS-005` 与 `TASK-CERTBOT-ATOMIC-001` 的重叠脚本、Compose 和部署文档。备份恢复与镜像构建已分别拆至 `TASK-BACKUP-RESTORE-IMPLEMENTATION-019`、`TASK-IMAGE-BUILD-REPRO-020`，不得重复计算。

## 任务类型
- implementation / infrastructure security（不改变产品契约）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/design/architecture.md` §9.1～§9.4
- `docs/design/security.md` §6、§9、§12
- `docs/test/test-plan.md` TC-OPS-001、TC-OPS-003、TC-OPS-004、TC-SEC-007

## 目标
1. 使生产 Compose、镜像和 Nginx 以锁文件、强密钥、内网分区及最小暴露面确定性启动。
2. 让生产 env 文件成为 Compose 唯一配置源，并校验 Web URL、允许 Origin 与证书域名一致。
3. 让证书配置切换在失败时原子回滚，并验证实际 X.509 域名与安全有效期窗口。
4. 修正文档中的工具安装、cron 环境导出、网络防火墙及真实恢复演练口径。

## 非目标
- 不改变公开 API、SSE、数据库 schema、业务逻辑、鉴权、字段加密、检索算法或评测阈值。
- 不在本机拉取镜像、安装系统包或访问真实生产数据。
- 不把当前单机 Compose 宣称为已批准的正式云拓扑；拓扑选择仍需用户完成。

## 允许修改路径
- `apps/api/.env.prod.example`
- `deploy/nginx.conf`
- `deploy/nginx-https.conf.template`
- `deploy/certbot-init.sh`
- `docker-compose.prod.yml`
- `scripts/deploy.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-OPS-PRELAUNCH-CONSOLIDATED-013.md`
- 上述被合并/拆分任务单（仅状态与交付证据）

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；仅允许对显式隔离的空白恢复库做演练。
- API：无。
- 依赖：无项目依赖；只复用任务已列明的 Docker/Compose、Linux/Python 标准工具及现有镜像。
- 安全配置：允许新增/收紧 Redis 密码、固定 CIDR、Origin/域名一致性、网络分区、HTTPS 安全头、备份恢复边界。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：使交付实现符合已批准的安全、架构和运维验收，不改变用户可观察的产品行为。

## 验收
- `bash -n` 通过全部变更 Shell；弱值、HTTP URL、Origin/域名冲突、host env 覆盖均 fail closed 且不打印密钥。
- Compose 静态渲染成功；PostgreSQL/Redis 仅在内部网络，Nginx 不能横向访问数据服务，监控管理端仅 loopback 暴露。
- Nginx HTTP 业务路径关闭，HTTPS/SSE/上传限制及证书原子切换保持有效。
- 备份/恢复行为由 `TASK-BACKUP-RESTORE-IMPLEMENTATION-019` 独立验收，本单只验证部署文档调用口径。
- cron 明确 export 仓库外 `0600` 口令；首次联网构建、备份恢复和真实 HTTPS smoke 保留为外部环境证据。

## 变更预算
- max_files：12
- expected_prod_lines：≤ 560
- expected_test_lines：0
- expected_doc_lines：≤ 240

## 必须运行的测试命令
- `bash -n scripts/deploy.sh deploy/certbot-init.sh`
- `docker compose --profile tools --env-file <redacted-test-env> -f docker-compose.prod.yml config`
- 弱值、Origin/域名冲突、host env 覆盖与错误证书拒绝演练
- 缓存镜像可用时执行 Redis auth、网络隔离、Nginx、API import 与隔离恢复 smoke
- `pnpm test && pnpm typecheck && pnpm build`
- `git diff --check` 与 executable mode 核对

## 回滚方法
- 回退本任务列明的交付文件；不删除卷、证书或任何真实数据。

## 强制停止条件
- 需要改公开契约/schema/业务权限、引入项目依赖、降低安全控制、触达真实生产数据或超过本合并预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无 schema 迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：正式云拓扑、供应链联网扫描、真实域名签发与隔离恢复演练需外部环境
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
