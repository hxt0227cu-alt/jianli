# Jianli · AI Agent 问答与面试预约系统

> 以真实简历为语料的 **AI Agent 问答 + 面试预约** 一体化系统。浏览器端 React 单页应用，后端 FastAPI + PostgreSQL/pgvector + Redis，自研 Agent 执行循环（工具编排 / RBAC / 有界上下文）、混合检索 RAG（BGE-M3 + 可选 Cross-Encoder Rerank）、SSE 流式工具轨迹、Outbox 可靠通知（邮件 + 飞书），并内置完整的评测与 CI 质量门禁。

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [架构总览](#架构总览)
- [快速开始（本地开发）](#快速开始本地开发)
- [项目结构](#项目结构)
- [测试与质量门禁](#测试与质量门禁)
- [部署](#部署)
- [文档导航](#文档导航)
- [安全说明](#安全说明)
- [License](#license)

---

## 项目简介

Jianli 面向「求职者在线简历 + 面试预约」业务场景：访客浏览真实简历、通过 AI 问答追问项目经历（RAG 有据回答、拒绝越界编造），面试官登录后按动态时段预约面试；预约、改期、取消全流程并发安全，通知经邮件 / 飞书双通道可靠送达。

项目采用**单仓库（monorepo）+ 单体模块化**架构，并配套一套由 **AI Agent 驱动的治理流程**（任务单驱动、双角色审查、规范唯一真相源、变更门禁、可审计状态机），仓库内 `tasks/`、`PROJECT_STATE.md`、`docs/baseline.yml` 即该治理过程的完整证据。

## 核心特性

- **AI 简历问答（Grounded RAG）**
  - 混合检索：BGE-M3 向量（pgvector，1024 维）+ BM25，RRF 融合，可选 Qwen3-Reranker 精排；
  - 证据门（最小相似度阈值）把关，无依据即拒答（offtopic），不编造；
  - 第一人称人格层（L1），SSE 流式输出 `started → delta* → citations → completed`。
- **自研 Agent 执行循环**
  - 工具白名单（搜索知识 / 创建·查询·取消·改期预约）+ RBAC（面试官仅本人、owner_admin 可旁路管理他人）；
  - 最多 4 步工具规划，模型输出不直接可信，服务端校验后复用同一套 `BookingService` 事务与审计；
  - 有界上下文、防注入、越权攻击与无依据拒答均有真实用例覆盖。
- **并发安全的面试预约**
  - 动态时段（Slot）物化 + 统一锁顺序（L0→L3）+ 行锁 + 幂等，杜绝超卖；
  - 敏感字段 AES-256-GCM 加密存储，公司名指纹去重；
  - SSE 实时推送面试表变更，前端连接级序号收敛。
- **Outbox 可靠通知**
  - 业务事务同库写 `NotificationEvent`（Outbox），独立 Worker 领取 / 重试 / 超时回收；
  - 邮件（SMTP）+ 飞书多维表格同步与消息提醒双通道，互不兜底、失败告警。
- **可观测性**
  - OpenTelemetry 追踪 + Prometheus 指标 + Grafana 面板（Agent 概览），OpenAPI 契约齐全。
- **质量门禁**
  - pytest / ruff / mypy / Vitest / Playwright / 迁移 up-down 验证 / RAG 评测回归，统一由 `agent-quality-gate` CI 工作流串行执行。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19、TypeScript、Vite、SSE |
| 后端 | Python 3.12、FastAPI、SQLAlchemy、Alembic |
| 数据 | PostgreSQL 16 + pgvector、Redis 7 |
| AI | DeepSeek（OpenAI 兼容）、BGE-M3 Embedding、Qwen3-Reranker（可选） |
| 集成 | SMTP（163）、飞书开放 API（多维表格 + 机器人消息） |
| 部署 | Docker Compose、Nginx、Certbot（HTTPS）、GitHub Actions |
| 可观测 | OpenTelemetry、Prometheus、Grafana |

## 架构总览

```
[浏览器 React SPA]──HTTPS/SSE──▶[FastAPI API 单体模块]
                                        │
   ┌───────────┬───────────────┬────────┴─────────────┬──────────────┐
   ▼           ▼               ▼                      ▼              ▼
[Auth]    [Slots/       [Knowledge/RAG]         [Notifications]  [Admin/知识库]
           Appointments]                         Outbox Worker
   │           │               │                      │
   ▼           ▼               ▼                      ▼
   ┌───────────┴───────────────┴──────────────────────┴─────────────┐
   │        PostgreSQL（关系数据 + pgvector 向量）  +  Redis          │
   └────────────────────────────────────────────────────────────────┘
        ▲                                 ▲
   [SMTP 邮件]                        [飞书 OpenAPI]
        └──────────[OTel/Prometheus/Grafana]──────────┘
```

完整设计见 [docs/design/architecture.md](docs/design/architecture.md)、[docs/design/domain-model.md](docs/design/domain-model.md)、[docs/design/security.md](docs/design/security.md)。

## 快速开始（本地开发）

### 前置依赖

- Python 3.12、Node.js 20+、pnpm 9
- Docker + Docker Compose（提供 PostgreSQL/pgvector 与 Redis）

### 1. 启动基础设施

```bash
docker compose -f docker-compose.dev.yml up -d
# PostgreSQL 127.0.0.1:55432，Redis 127.0.0.1:63790
```

### 2. 后端（apps/api）

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.lock

# 生成本地开发环境变量（首次运行，写入 gitignore 的 .env.local）
# WSL/bash:
source ../scripts/dev-env.sh
# 真实凭据只走运行时 export，不落盘：
# export JIANLI_LLM_API_KEY='sk-...'
# export JIANLI_SMTP_PASSWORD='...'

alembic upgrade head          # 执行迁移
python -m uvicorn app.main:app --reload
```

未配置 `JIANLI_LLM_*` 时自动回退 Stub 网关与本地哈希 Embedding，无 LLM 也可跑通测试。

### 3. 前端（仓库根）

前端工程（Vite + React + TypeScript）在**仓库根目录**，`vite.config.ts` 以 `apps/web` 为 root：

```bash
pnpm install
pnpm dev        # http://localhost:5173
```

### 4. 测试

```bash
# 后端
cd apps/api && python -m pytest -q
python -m ruff check . && python -m mypy app

# 前端（仓库根，vite root = apps/web）
pnpm test && pnpm typecheck && pnpm build
```

> 真实集成 / 迁移 / RAG 评测需真实 PG/Redis 与密钥，命令见 [docs/test/test-plan.md](docs/test/test-plan.md) 与 [docs/HARNESS.md](docs/HARNESS.md)。

## 项目结构

```
jianli/
├── apps/
│   ├── api/                  # FastAPI 后端（monorepo 主服务）
│   │   ├── app/
│   │   │   ├── auth/         # 认证：注册/登录/找回/CSRF/限频/字段加密
│   │   │   ├── appointments/ # 时段物化与预约：事务/锁/SSE
│   │   │   ├── aiqa/         # AI 问答：RAG/人格/Agent 工具循环/知识库
│   │   │   ├── notifications/# Outbox Worker：邮件 + 飞书
│   │   │   └── admin/        # 管理端：预约/知识库/联系人配置
│   │   ├── migrations/       # Alembic 迁移（0001–0010）
│   │   └── tests/            # pytest 测试（单元/集成/迁移/安全）
│   └── web/                  # React 前端源码（vite root；三页面 + admin + 登录）
├── deploy/                   # Nginx、Certbot、Observability（OTel/Prometheus/Grafana）
├── docs/                     # PRD/SRS/领域模型/架构/ADR/OpenAPI/测试计划
├── scripts/                  # dev/deploy/backup/restore/verify/评测脚本
├── tasks/                    # 任务单（AI 治理证据，TASK-*.md）
├── tests/web-shell/          # Playwright / Vitest 端到端
├── package.json              # 前端工程入口（仓库根；vite root = apps/web）
├── vite.config.ts            # 前端构建配置
├── AGENTS.md                 # AI 编码协作规范（治理约束）
├── PROJECT_STATE.md          # 项目状态与任务台账
└── docs/baseline.yml         # 规范唯一真相源（版本/状态/门禁）
```

## 测试与质量门禁

- **单元 / 集成**：pytest（auth / appointments / aiqa / notifications / migrations / scripts）
- **前端**：Vitest + Playwright（web-shell）
- **静态与类型**：ruff check / format、mypy
- **迁移**：Alembic up → down → up 校验
- **RAG 评测**：真实知识库 + BGE-M3/pgvector 复验（事实一致性、越界拒答、隐私拒答）
- **CI**：`.github/workflows/agent-quality-gate.yml`（backend-agent → rag-integration → web-delivery 串行门禁）

## 部署

生产部署基于 Docker Compose（`docker-compose.prod.yml`）：PostgreSQL / Redis / migrate / API / Worker / Nginx / Certbot / 可观测栈，通过 `.env`（不入库）注入密钥，部署预检会拒绝 `CHANGE_ME`、弱口令与缺失变量。完整步骤（含阿里云/腾讯云、域名、HTTPS、备份恢复）见：

- [docs/deploy/阿里云部署指南.md](docs/deploy/阿里云部署指南.md)
- [deploy/certbot-init.sh](deploy/certbot-init.sh)
- [scripts/deploy.sh](scripts/deploy.sh)、[scripts/backup.sh](scripts/backup.sh)、[scripts/restore.sh](scripts/restore.sh)

## 文档导航

| 文档 | 说明 |
|------|------|
| [docs/requirements/PRD.md](docs/requirements/PRD.md) | 产品需求（v2.3） |
| [docs/requirements/SRS.md](docs/requirements/SRS.md) | 软件需求规格（v1.9） |
| [docs/design/architecture.md](docs/design/architecture.md) | 架构设计（v0.6） |
| [docs/design/domain-model.md](docs/design/domain-model.md) | 领域模型（v1.1.8） |
| [docs/design/security.md](docs/design/security.md) | 安全设计 |
| [docs/api/openapi.yaml](docs/api/openapi.yaml) | OpenAPI 契约 |
| [docs/api/sse.md](docs/api/sse.md) | SSE 事件协议 |
| [docs/HARNESS.md](docs/HARNESS.md) | 评测 / Harness 工程实践 |
| [docs/test/test-plan.md](docs/test/test-plan.md) | 测试计划 |

## 安全说明

- **密钥不入库**：所有 `JIANLI_*` 密钥、API Key、授权码、飞书 App Secret 一律运行时注入（`.env` / `export`），仓库只提供脱敏模板 `apps/api/.env.prod.example`。
- **数据脱敏**：本仓库已对个人联系方式（手机号、邮箱）、平台凭据（飞书 App ID / Token / open_id）与本地路径做脱敏处理；`apps/web/public/resume.md` 为脱敏后的示例简历，`resume.pdf` / `resume-preview.png` 为对应示例渲染，请按需替换为自有素材。
- **纵深防御**：字段级加密、CSRF、限频、CORS 白名单、RBAC、注入防护、供应链安全扫描，详见 [docs/design/security.md](docs/design/security.md) 与 [SECURITY.md](SECURITY.md)。

## License

[MIT](LICENSE) © 2026 Jianli
