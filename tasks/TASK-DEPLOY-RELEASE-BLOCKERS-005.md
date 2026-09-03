# TASK-DEPLOY-RELEASE-BLOCKERS-005 生产交付确定性阻塞修复

> 状态：In Progress（2026-08-31）。上线前独立安全审查发现生产栈仍存在确定性启动与边界缺陷；用户已授权修复全部上线阻塞。

## 任务类型
- implementation（基础设施与安全配置缺陷修复）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/design/architecture.md` §9.1～§9.4
- `docs/design/security.md` §3、§6、§9、§12
- `docs/test/test-plan.md` TC-OPS-001、TC-OPS-003、TC-OPS-004、TC-SEC-007

## 目标
1. 修正 Compose PostgreSQL healthcheck 变量与 `up --wait` 用法，生产预检强制 production/smtp/HTTPS/完整关键配置。
2. Redis 启用独立随机密码，数据库/缓存使用内部后端网络；Nginx 仅能访问 API，不能横向访问 PostgreSQL/Redis。
3. API 只信固定前端网络 CIDR 的代理头，恢复真实客户端 IP/HTTPS scheme，不信任任意来源。
4. HTTP bootstrap 只开放 ACME 与健康检查，其余 503；HTTPS 增加 HSTS/CSP 等安全头，并把 210MiB 请求体限制收窄到知识库上传端点。
5. 前端在专用多阶段 Nginx 镜像内从锁文件构建，避免 `git clone` 后 `dist/` 缺失却健康误报。
6. API 镜像补齐 Psycopg 纯 Python 运行所需 `libpq5`；API 家族服务复用同一镜像标签。
7. 部署/备份/恢复/管理员/证书脚本在 Linux clone 后具有可执行位。

## 非目标
- 不修改公开 API、DB schema、业务鉴权、字段加密、RAG 检索或前端产品内容。
- 不在本机联网拉取镜像、系统包或漏洞库；首次全新镜像 smoke 由联网环境完成。

## 允许修改路径
- `docker-compose.prod.yml`
- `apps/api/.env.prod.example`
- `apps/api/Dockerfile`
- `.dockerignore`
- `deploy/Dockerfile.nginx`
- `deploy/nginx.conf`
- `deploy/nginx-https.conf.template`
- `scripts/deploy.sh`
- `scripts/create-owner.sh`（仅 Git executable mode）
- `deploy/certbot-init.sh`（仅 Git executable mode）
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-DEPLOY-RELEASE-BLOCKERS-005.md`
- `scripts/backup.sh`、`scripts/restore.sh`（仅 Git executable mode；内容归 TASK-004）

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化。
- API：无。
- 安全配置：新增 `JIANLI_REDIS_PASSWORD`；生产网络拆为固定 CIDR 的 frontend/backend/egress；API 仅信 frontend CIDR 代理头；HTTP 应用入口关闭、HTTPS 安全头与上传端点限流收紧。
- 基础设施依赖：API Debian slim 镜像安装运行时 `libpq5`；新增 Node→Nginx 多阶段 Web 镜像构建，复用现有 pnpm lock，不新增 npm/pip 包。
- 镜像：API 家族使用同一 `${JIANLI_API_IMAGE}`；Web 使用 `${JIANLI_WEB_IMAGE}`。digest/SBOM/漏洞门禁由独立供应链任务承接。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：使生产实现符合已批准架构、安全和运维要求，不改变产品契约。

## 验收
- 自定义 PG user/db 时 healthcheck 正确；`docker compose up -d --wait --wait-timeout` 语法有效。
- 缺 production/smtp/HTTPS/Redis/关键外部通道配置时部署预检失败且不打印值。
- Redis 未授权 `PING` 失败、带密码成功；Nginx 网络不可达 PostgreSQL/Redis，API/Worker 正常使用缓存并可外连。
- Nginx HTTP 业务路径 503；HTTPS 有安全头，SSE 不缓冲，只有知识库上传端点允许 210MiB。
- Web 镜像含非空 `index.html`；Nginx healthcheck 同时检查制品与配置端点。
- API 新镜像可 `import psycopg`、启动并连接 PG。
- 相关 Linux 脚本 Git mode 为 `100755`。

## 变更预算
- max_files：14
- expected_prod_lines：≤ 320
- expected_test_lines：0
- expected_doc_lines：≤ 80

## 必须运行的测试命令
- `bash -n scripts/deploy.sh`
- `docker compose --profile tools config`
- 占位/弱值/HTTP origin/console email/短 Redis 密码拒绝测试
- 缓存镜像可用时的 Redis auth、网络隔离、Nginx `-t`/headers/SSE/upload 与 API import smoke
- `pnpm test && pnpm typecheck && pnpm build`
- `git diff --check`、`git ls-files --stage` executable mode 核对

## 回滚方法
- 回退本任务配置/脚本/镜像定义与文件 mode；数据卷不删除。

## 强制停止条件
- 需要改公开 API/schema/业务权限、引入 npm/pip 包、降低安全头/限流或触达真实生产数据。
- 冻结验收失败或超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无 schema 迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：首次联网构建与真实域名 HTTPS smoke 待外部环境
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
