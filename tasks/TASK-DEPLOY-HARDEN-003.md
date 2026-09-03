# TASK-DEPLOY-HARDEN-003 生产配置、知识库与备份恢复硬化

> 状态：Implemented / Awaiting final integration verification（2026-08-31）。承接上线前审计确认的生产阻塞；用户明确要求修复。

## 任务类型
- implementation（基础设施与运维缺陷修复）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/design/architecture.md` §9.1～§9.4
- `docs/design/security.md` §6、§9、§12
- `docs/test/test-plan.md` TC-ADMIN-003、TC-OPS-001、TC-OPS-003、TC-OPS-004、TC-SEC-007
- `tasks/TASK-DEPLOY-HARDEN-002.md`

## 需求来源
- 生产 env 模板缺必需变量、知识卷首启权限/语料初始化断链、Nginx 上传限制不匹配、备份明文且无恢复演练入口、敏感产物可能被 Git 跟踪。

## 目标
1. 使生产 env 模板与 Compose 必需变量一致，并拒绝默认弱密码上线。
2. 保证非 root API 能写新知识卷；把 canonical corpus 作为生产工件并提供幂等初始化步骤。
3. 让 Nginx 上传上限覆盖 approved 单文件/单次文件数，最终仍由 API 严格校验。
4. 忽略备份和证书私钥；备份采用 0600/安全临时目录、加密、校验和，并提供隔离恢复脚本。
5. 改善构建上下文、容器日志轮转和可验证的部署前检查；不伪造真实域名/证书证据。

## 非目标
- 不修改公开 API、DB schema、鉴权/加密业务策略、RAG 检索算法或阈值。
- 不购买服务器、修改 DNS、签发真实证书、轮换外部凭据、联网拉镜像或漏洞库。
- 不在本任务宣称真实生产备份恢复已完成；只提供可执行机制并在隔离测试库验证。

## 允许修改路径
- `docker-compose.prod.yml`
- `apps/api/.env.prod.example`
- `apps/api/Dockerfile`
- `apps/api/.dockerignore`
- `apps/api/app/aiqa/**`（仅 canonical corpus 工件化）
- `apps/api/scripts/seed_kb.py`
- `apps/api/tests/aiqa/test_rag_eval.py`（仅改为引用等价 canonical corpus，不改问题/阈值/断言）
- `deploy/nginx.conf`
- `deploy/nginx-https.conf.template`
- `.gitignore`
- `scripts/deploy.sh`
- `scripts/backup.sh`
- `scripts/restore.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-DEPLOY-HARDEN-003.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/migrations/**`
- `docs/requirements/**`、`docs/api/**`、领域模型与安全规范
- 认证、预约、通知、Agent 工具权限与 Prompt
- 评测问题、命中率/拒答率/隐私断言或检索阈值

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；允许对既有表执行幂等 canonical corpus 初始化及隔离恢复验证。
- API：无。
- 依赖：不新增 pip/npm 依赖；备份/恢复使用目标 Linux 已有的 `pg_dump`、`pg_restore`、`tar`、`sha256sum`、`openssl`，部署前必须显式检查，缺失即失败。
- 基础设施：允许新增 `seed-kb` 一次性步骤、Compose 日志轮转/资源限制和生产预检；均不改变业务契约。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：补齐已 approved 的生产安全、知识库初始化、上传与备份恢复实现。

## 功能验收
- `.env.prod.example` 可完整渲染 Compose，但部署脚本拒绝占位密码/密钥。
- 新知识卷由 `appuser` 可写；canonical 20 篇语料可幂等初始化并验证 active/indexed 数。
- HTTP/HTTPS Nginx 上传上限一致，SSE buffering 仍关闭。
- 备份输出只有加密包和校验文件；恢复前校验完整性并要求显式隔离目标。
- `backups/`、证书私钥目录不会进入 Git。

## 安全与隐私验收
- 任何脚本不输出 secret；临时明文目录为 0700 且退出清理；输出文件 0600。
- 恢复脚本禁止默认覆盖生产目标，必须显式设置独立目标 DB 与知识目录。

## 性能验收
- 备份/恢复流式处理；不把完整 dump 读入内存。
- 容器日志启用大小/文件数轮转；资源限制不阻断既有 2C4G 推荐配置。

## 变更预算
- max_files：16
- expected_prod_lines：≤ 250
- expected_test_lines：≤ 360

## 必须运行的测试命令
- 生产 Compose 模板渲染与服务依赖检查
- `bash -n scripts/deploy.sh scripts/backup.sh scripts/restore.sh`
- canonical corpus 冻结 RAG 测试（真实 BGE-M3 可用时复验）
- 临时测试数据库/知识目录备份→独立目标恢复演练
- `ruff check . && mypy app`
- `git diff --check` 与 tracked secret pattern scan

## 回滚方法
- 回退 Compose/Dockerfile/Nginx/脚本与 corpus 工件化；不删除任何生产卷。
- 恢复演练仅针对任务专用测试 DB/目录，可直接丢弃。

## 强制停止条件
- 需要新增业务 API、迁移、包依赖、权限/密钥策略或调整 RAG 阈值/评测断言。
- 无法在预算内把 canonical corpus 与测试单一来源化。
- 冻结测试失败或超出文件预算。

## 交付证据
- commit / PR：待主代理生成（实现代理按指示未提交）
- 修改文件清单（15）：`.gitignore`、`apps/api/.dockerignore`、`apps/api/.env.prod.example`、`apps/api/Dockerfile`、`apps/api/app/aiqa/canonical_corpus.py`、`apps/api/scripts/seed_kb.py`、`apps/api/tests/aiqa/test_rag_eval.py`、`deploy/nginx.conf`、`deploy/nginx-https.conf.template`、`docker-compose.prod.yml`、`docs/deploy/阿里云部署指南.md`、`scripts/backup.sh`、`scripts/deploy.sh`、`scripts/restore.sh`、本任务单。
- 测试命令及结果：
  - WSL `bash -n scripts/deploy.sh scripts/backup.sh scripts/restore.sh` → pass。
  - WSL `docker compose --env-file apps/api/.env.prod.example -f docker-compose.prod.yml --profile tools config --services` → pass，13 个生产/工具服务可展开。
  - WSL `pytest tests/scripts/test_seed_kb.py -q` → `3 passed in 5.98s`（含 failed reason 安全脱敏冻结回归）。
  - 旧测试语料与生产 `CANONICAL_CORPUS` AST 值逐字比较 → `PASS docs=20`；评测问题、阈值、断言未改。真实 BGE-M3 本轮前置同基线为 `7 passed in 135.61s`，按主代理指示不重复外调，最终合并后由主代理决定是否复验。
  - WSL 缓存镜像隔离测试：新 named volume 经 `knowledge-init` 后 UID/GID `10001` 可写，目录模式 `0700` → pass。
  - WSL 缓存 `pgvector/pgvector:pg16` 隔离演练：数据库 + 知识目录 → 加密包/校验文件 → 独立 DB/新目录恢复；仅两个 `0600` 输出、恢复目录 `0700`、DB/文件一致、篡改校验拒绝 → pass；测试容器与临时目录已清理。
  - 部署占位值拒绝测试 → pass；Nginx HTTP/HTTPS `210m` 与 SSE `proxy_buffering off` 静态断言 → pass。
  - `git diff --check`（本任务路径）→ pass；高置信 secret pattern 与敏感运行产物 tracked scan → pass。
- lint / typecheck：WSL `ruff check . && mypy app` → `All checks passed`；`Success: no issues found in 53 source files`。
- DB 迁移验证：无 schema 迁移；未执行生产迁移；上述隔离 backup/restore 演练通过。
- 验收证据：Grafana 必需变量已进入生产模板且部署预检拒绝占位/弱值；备份强口令不进入 Compose 共用 `.env`；知识卷首启权限与 20 篇生产初始化闭环；Nginx 批量上传上限、敏感目录忽略、加密校验备份、显式隔离恢复、构建上下文与全服务日志轮转均已实现。
- 变更预算实际值：15/16 文件；生产/配置/脚本新增 249 行（≤250，另删 122 行）；测试新增 1 行、删除 257 行（语料迁至生产 SSOT，≤360）；部署文档新增 43 行、删除 8 行；未修改 `PROJECT_STATE.md`，留给主代理统一收口。
- 未解决风险：未伪造真实服务器/域名/证书/凭据轮换证据；WSL 缓存缺少 `nginx:1.27-alpine`、`certbot/certbot:v3.2.0`、`otel/opentelemetry-collector-contrib:0.140.0`、`grafana/grafana:12.3.0`、`prom/prometheus:v3.7.3`，依指示未联网拉取，故完整生产容器健康 smoke 待目标服务器；目标 Linux 必须安装预检要求的 PostgreSQL 客户端工具。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待主代理最终提交后回填
