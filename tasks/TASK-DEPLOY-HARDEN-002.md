# TASK-DEPLOY-HARDEN-002 生产部署栈发布阻塞修复

> 状态：Implemented / Awaiting container smoke（2026-08-26）。用户已明确授权解决上线前 7 个硬阻塞，并要求遇到网络问题立即停下寻求配合；本任务只承载其中不改变业务契约的部署基础设施修复。

## 任务类型

- implementation（基础设施缺陷修复）

## 基线版本与基线 commit

- baseline：PRD 2.3.4 / use-cases 1.7.2 / domain-model 1.1.5 / SRS 1.4 / architecture 0.2 / security 0.1 / OpenAPI 0.4
- 基线 commit：`fbb1af6`

## 精确规范引用

- `docs/design/architecture.md` §6（API / Worker 独立进程与 Outbox）
- `docs/design/security.md` 中生产密钥、TLS 与运行时配置要求
- `tasks/TASK-DEPLOY-001.md`（已获批的 Docker Compose + Nginx + HTTPS 基础设施范围）
- 当前实现路由：`apps/api/app/auth/router.py`、`apps/api/app/appointments/router.py`、`apps/api/app/aiqa/router.py`、`apps/api/app/admin/router.py`（只读核对，不修改）

## 目标

1. 修复 Nginx 仅反代 `/api/`、而前端实际调用根路径 API 的致命错配。
2. 修复首次启动时证书不存在导致 Nginx 无法启动，以及 compose 缺少 `certbot` 服务的问题。
3. 在 API / Worker 启动前显式执行 `alembic upgrade head`，避免空库直接启动业务进程。
4. 为 API、Worker、Nginx 增加不新增公开业务 API 的运行探活与启动依赖。
5. 让部署脚本分成可验证的 HTTP 启动、证书签发、HTTPS 切换步骤，并保留失败回滚路径。

## 非目标

- 不新增或修改任何公开 API / SSE 契约。
- 不新增数据库表、字段、索引或迁移。
- 不改认证、加密、密钥、邮件或 Agent 权限策略。
- 不购买服务器、备案、修改 DNS、签发真实证书或写入真实密钥。
- 不处理预约时段初始化、验证码重发、管理端问答审计或当前未提交业务代码；分别由后续任务承载。

## 允许修改路径

- `docker-compose.prod.yml`
- `deploy/nginx.conf`
- `deploy/nginx-https.conf.template`
- `deploy/certbot-init.sh`
- `scripts/deploy.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-DEPLOY-HARDEN-002.md`
- `PROJECT_STATE.md`

## 禁止修改路径

- `apps/api/app/**`
- `apps/api/migrations/**`
- `apps/web/**`
- `docs/api/**`、`docs/requirements/**`、`docs/design/**`
- 依赖锁文件

## 已批准的 DB / API / 依赖变更

- DB：无 schema 变化；仅在容器启动序列中执行既有 `alembic upgrade head`。
- API：无；Nginx 只代理当前代码与 approved OpenAPI 已存在的根路径端点。
- 依赖：无项目依赖新增；compose 增加官方 `certbot/certbot` 基础设施镜像，属于用户已批准的 HTTPS 部署栈修复。
- 基础设施：修复 TASK-DEPLOY-001 已批准但未完成验证的 Compose/Nginx/Certbot/探活实现；用户于 2026-08-26 明确授权解决上线硬阻塞。

## 规范影响评估

- behavior_change：false（修复部署实现使其符合既有外部契约；不改变业务可观察语义）
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- spec_sync：clean

## 验收

- `docker compose --env-file <临时占位 env> -f docker-compose.prod.yml config` 成功。
- `bash -n scripts/deploy.sh deploy/certbot-init.sh` 成功。
- HTTP 阶段 Nginx 配置不引用尚不存在的证书；HTTPS 模板才引用证书。
- 当前前端使用的 `/auth`、`/answers:stream`、`/appointments`、`/slots`、`/admin`、`/pages`、`/conversations` 均被代理，SSE buffering 关闭。
- API/Worker 在 migration 成功后启动；migration 失败时不得继续。
- 不因网络失败重复拉取镜像；立即报告并给出用户可执行命令。

## change_budget

- max_files：8
- expected_prod_lines：≤ 420
- expected_test_lines：0

## 回滚

- 恢复本任务修改前的 compose/Nginx/脚本文件；`docker compose down` 默认保留数据卷。
- HTTPS 切换失败时恢复 `deploy/nginx.conf` 的 HTTP 配置并重启 Nginx。

## 强制停止条件

- 需要新增业务 API、迁移、依赖或改变鉴权/密钥策略。
- 超出 8 个文件或 420 行预算。
- 冻结测试失败。
- Docker/证书公网访问失败时停止并请求用户配合，不长时间重试。

## 交付证据

- commit / PR：实现提交待生成后回填
- 修改文件清单：`docker-compose.prod.yml`、`deploy/nginx.conf`、`deploy/nginx-https.conf.template`、`deploy/certbot-init.sh`、`scripts/deploy.sh`、`docs/deploy/阿里云部署指南.md`、本任务单、`PROJECT_STATE.md`
- 测试命令及结果：
  - `JIANLI_ENV_FILE=apps/api/.env.prod.example docker compose --env-file apps/api/.env.prod.example -f docker-compose.prod.yml config` → PASS
  - 上述命令增加 `--profile tools ... config --services` → PASS，7 服务包含 migrate/certbot
  - `bash -n scripts/deploy.sh deploy/certbot-init.sh` → PASS
  - HTTP/HTTPS Nginx 路由、括号、bootstrap 无 TLS 引用静态断言 → PASS
  - `git diff --check` → PASS（仅工作区既有 CRLF 提示）
- lint / typecheck：无业务代码变化；YAML/Compose 与 Shell 静态门禁通过
- 数据库迁移结果：本任务不执行生产迁移；验证启动顺序与既有迁移命令
- 验收证据：根路径 API 7 组与 2 个 SSE 路径在 HTTP/HTTPS 配置中均覆盖；migrate 为 API/Worker 的 `service_completed_successfully` 前置；三个长驻服务均有 healthcheck
- 变更预算实际值：8 文件（= max_files）；生产/脚本/文档净增量低于 420 行
- 未解决风险：本机未缓存 Nginx/Certbot 镜像，按用户网络止损要求未拉取；`nginx -t`、全容器 healthy、真实域名/DNS/证书须后续 smoke
- 是否偏离 TASK：否
- 建议审查重点：首次 HTTP 启动、API 路由覆盖、SSE、迁移失败传播、HTTPS 切换回滚
- verified_commit：待容器 smoke 后回填
