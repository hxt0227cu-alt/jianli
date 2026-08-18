# TASK-DEPLOY-001 阿里云生产部署：Docker compose + Nginx/HTTPS + Worker 守护

> **状态：implemented（2026-08-18 用户批准 + 部署栈 5ab96c5；补充备份/owner 初始化见文末「补充改动」小节）**
> 目标环境：阿里云轻量应用服务器（Ubuntu 22.04 LTS）+ 用户自有域名（需 ICP 备案）+ HTTPS。将本地开发栈（FastAPI API + 预约 Worker + PostgreSQL + Redis + 前端 dist）容器化部署，Worker 以独立容器常驻（架构 §6 Outbox 消费者独立进程要求）。

## 任务类型
- implementation  # 实现：部署基建（Dockerfile / compose / Nginx / systemd / 脚本）

## 基线版本与基线 commit
- baseline：SRS 1.3 / 领域模型 1.1.5 / architecture 0.2 / security 0.1 / OpenAPI 0.3（取自 `docs/baseline.yml`）
- 基线 commit：`fc8f46e`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/design/architecture.md` §6（Outbox 消费者独立进程；worker 与 API 同镜像不同入口）
- `docs/design/security.md`（密钥仅运行时环境变量、不进镜像/日志）
- `docker-compose.dev.yml`（现有 PG/Redis 服务定义，作生产 compose 基线）
- `apps/api/app/worker.py`（`run_worker()` 入口，`python -m app.worker`）

## 需求来源
- 用户 2026-08-18 决策：购买阿里云轻量服务器 + 自有域名上线，简历放网站链接
- 部署目标：面试官随时可访问、服务稳定（不依赖本地电脑）、HTTPS、域名备案

## 目标
交付一套可一键上线的生产部署栈：
1. **Dockerfile（API+Worker 共用）**：`apps/api/Dockerfile`，基于 python:3.12-slim，装依赖（httpx 已在 runtime deps）、复制 app/migrations、入口支持两种 command（`uvicorn app.main:app` / `python -m app.worker`）
2. **`docker-compose.prod.yml`**：5 服务——nginx（前端 dist + 反代 /api）、api、worker、postgres（数据卷）、redis；worker `restart: always` + `depends_on: postgres, redis`
3. **Nginx 配置**：`deploy/nginx.conf`——托管前端构建产物 + `/api` 反代 API + HTTPS（Let's Encrypt certbot）配置模板
4. **部署脚本**：`scripts/deploy.sh`——拉镜像→up→健康检查→证书续期提示
5. **`.env.prod.example`**：完整生产环境变量模板（**无真实密钥**，标注每项来源）
6. **部署文档**：`docs/deploy/阿里云部署指南.md`——买服务器→备案→装 Docker→跑脚本→配域名→HTTPS→验证清单

## 非目标（明确排除）
- 不实际购买服务器 / 备案（用户操作）
- 不部署执行（本任务产出文件，执行由用户在服务器上按文档操作）
- 不改业务代码（app/** 只加 Dockerfile 不改逻辑）
- 不做 CI/CD、不做 k8s、不做对象存储迁移（知识库 var/ 目录挂卷处理）
- AIQA 域内容（page2 前端素材等）不涉及

## 允许修改路径
- `apps/api/Dockerfile`（新）
- `apps/api/.dockerignore`（新）
- `docker-compose.prod.yml`（新，根目录）
- `deploy/nginx.conf`（新）
- `deploy/certbot-init.sh`（新，可选）
- `scripts/deploy.sh`（新）
- `scripts/backup.sh`（新，补充改动登记）
- `scripts/create_owner.py` + `scripts/create-owner.sh`（新，补充改动登记）
- `apps/api/.env.prod.example`（新）
- `docs/deploy/阿里云部署指南.md`（新）
- `tasks/TASK-DEPLOY-001.md`（本任务单）

## 禁止修改路径
- `apps/api/app/**` 业务代码（除 Dockerfile 外零改动）
- `apps/web/**`（前端代码；仅构建产物由部署侧消费）
- `docs/**` 既有规范工件（新增 docs/deploy/ 目录除外）
- `docker-compose.dev.yml`（既有开发栈不动）

## 已批准的 DB / API / 依赖变更
- **DB**：无 schema 变更（沿用 0001-0008；生产库首次 `alembic upgrade head` 由部署文档引导）
- **API**：无契约变更（复用 OpenAPI v0.3）
- **依赖**：无新增 Python/npm 依赖（Docker 基础镜像 python:3.12-slim 为基础设施，非项目依赖）
- **基础设施**（AGENTS §4 人审批项）：新增 Docker 容器化 + Nginx + HTTPS 基础设施——本 TASK 草案即审批载体

## 规范影响评估（spec impact）
- behavior_change：**true**（新增生产部署形态 = 可观察变化）→ 分类：**基础设施变更**，非业务语义变更；SRS/领域模型/OpenAPI 无影响（部署方式不属于契约层）
- affected_specs：srs=none / domain_model=none / openapi=none / security=none / test_plan=none
- reason：部署栈不改变任何已批准行为语义；仅新增运行载体

## 功能验收
- `docker compose -f docker-compose.prod.yml build` 成功（WSL 或服务器）
- `docker compose -f docker-compose.prod.yml up -d` 后：nginx 健康、api 健康（`/api/v1/health` 或等价探活）、worker 日志无异常循环、PG/Redis 数据卷持久化
- 前端 `npm run build` 产物被 nginx 正确托管（域名/IP 访问首页 200）
- Worker 容器内跑 `python -m app.worker` 正常轮询（无 SMTP/飞书密钥时降级日志，不崩溃）

## 安全与隐私验收
- **无真实密钥进仓库**：`.env.prod.example` 仅模板；真实密钥在服务器 `.env`（gitignored）
- 密钥清单（部署文档标注来源）：JIANLI_SMTP_*、JIANLI_FEISHU_*、JIANLI_*_HMAC_KEY、JIANLI_FIELD_ENCRYPTION_KEYS、JIANLI_DATABASE_URL、JIANLI_REDIS_URL、JIANLI_LLM_*、JIANLI_ALLOWED_ORIGINS（生产域名）
- HTTPS 强制：Nginx 80→443 跳转 + certbot 证书
- **上线前置：重置今日 5 次泄露凭据**（SMTP×2、飞书 Secret×2、飞书授权），新码仅进服务器 .env

## 性能验收
- 轻量服务器 2C2G 下限：API P95 不受影响（本地已验证）；worker 轮询 2s 间隔开销可忽略
- 健康检查间隔 ≤30s；容器 `restart: always` 保证崩溃自愈

## 变更预算（change_budget）
- max_files：9
- expected_prod_lines：≤ 350（Dockerfile+compose+nginx+scripts+doc）
- expected_test_lines：0（部署验证 = compose up 冒烟，非 pytest）

## 必须运行的测试命令
- `docker compose -f docker-compose.prod.yml config`（compose 语法校验）
- `docker compose -f docker-compose.prod.yml build`（构建成功）
- `docker compose -f docker-compose.prod.yml up -d` + `docker compose ps`（全 healthy）
- `curl -I https://<域名>`（HTTPS 200）
- WSL 本地先跑一遍 prod compose（无密钥降级）确认不崩

## 回滚方法
- `docker compose -f docker-compose.prod.yml down`（停全部，数据卷保留）
- 域名回退 DNS 即可下线；本地开发栈不受影响（docker-compose.dev.yml 独立）

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要在业务代码中注入密钥/改鉴权 → 停止
- 需要新增项目 Python/npm 依赖 → 停止
- 超出 change_budget → 拆任务
- 备案未完成前禁止真实域名上线（部署文档中列为前置门禁）

## 补充改动（2026-08-18 用户批准 TASK 后追加，同属部署栈交付）

> 用户询问「数据存哪/备份」时确认补自动备份；同时发现 owner_admin 初始化缺口（seed 密码为占位符 `seed-kb-not-used`，不可登录），一并补齐。

- `scripts/backup.sh`：生产自动备份——PG 逻辑备份（pg_dump -F c，经 compose exec + cp）+ 知识库卷（jianli_knowledge）tar + 保留策略（KEEP_DAYS 默认 14）+ 可选 OSS 异地上传（ossutil + OSS_BUCKET）；cron 安装示例已写入部署指南第 7 节
- `scripts/create_owner.py`：创建/重置 owner_admin 账号（BCrypt 哈希、幂等 upsert、密码只走环境变量不落盘、防违反部分唯一索引 `uq_active_owner_admin` 的前置检查）
- `scripts/create-owner.sh`：服务器包装（读 .env 拼 DB URL、探测 api 镜像与网络、docker run 复用 api 镜像不经宿主机 Python）
- `docs/deploy/阿里云部署指南.md`：新增 §4.5（owner 账号初始化，必须步骤）+ 验证清单加 admin 登录/备份冒烟项 + 第 7 节备份/管理员命令 + 第 9 节风险更新（异地备份为待办）
- 校验：`bash -n` backup.sh / create-owner.sh ✅；`py_compile` + import 链（WSL python3，sqlalchemy + PasswordHasher）✅；`users.role` 为 PG enum `user_role`，字符串字面量隐式 cast 可行（seed_kb 同款已跑通）

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<待提交后回填>
- 修改文件清单：<与「允许修改路径」逐一对照>
- 测试命令及结果：<compose config/build/up 结果>
- lint / typecheck：无代码门禁（YAML/sh；shellcheck 可选）
- DB 迁移验证：生产库首次 upgrade head 由部署文档引导（本任务不执行）
- 验收证据：<服务器部署后 curl 输出 + docker compose ps>
- 变更预算实际值：<max_files / 行数>
- 未解决风险：备案周期（1-2 周）为上线前置；凭据重置待用户执行
- 是否偏离 TASK：<否 / 偏离项及原因>
- 规范影响结论：none
- spec_sync：clean
- verified_commit：<待服务器部署验证后回填>
- **关闭门禁（四条件）**：① compose build/up 通过；② 规范影响 none；③ spec_sync clean；④ verified_commit 真实 sha。

## 关联
- 前置：阿里云服务器购买 + 域名备案（用户操作，部署文档含清单）
- 前置：凭据重置（今日 5 次泄露）
- 相关：docker-compose.dev.yml（基线）、architecture §6（worker 独立进程）
- 后续：生产库首次迁移 + 域名 HTTPS 配置（部署文档引导）
