# ADR-IMPL-001：MVP 实现技术栈

- 状态：proposed
- 日期：2026-08-09
- 决策者：用户（AI 不代签 accepted）
- 依据：architecture 0.2 approved / security 0.1 review / OpenAPI-SSE 0.1 review / test-plan 0.1 review

## 1. 决策

采用 TypeScript Web 前端 + Python 模块化单体后端：

| 层 | 唯一推荐 | 用途 |
|---|---|---|
| Web | React 19、TypeScript 5、Vite 7、React Router、TanStack Query、Lucide React | 三个公开页面、认证、预约与 admin；SSE 客户端直接使用浏览器 `EventSource` |
| API | Python 3.12、FastAPI、Uvicorn、Pydantic 2 | OpenAPI-first HTTP/SSE、输入校验、统一错误体 |
| 数据 | SQLAlchemy 2、Alembic、psycopg 3、pgvector | PostgreSQL 事务、迁移、向量检索；关键锁事务允许使用参数化 SQL |
| 安全 | `bcrypt`、`cryptography`、`redis` | BCrypt、AES-256-GCM/HMAC、跨实例限频；方案以批准后的 security 为准 |
| 外部调用 | HTTPX、OpenAI Python SDK | 飞书与 DeepSeek OpenAI-compatible API；不引入 Agent 编排框架 |
| 文档解析 | PyMuPDF、python-docx、pytesseract | PDF/DOCX/OCR；OCR 进程受资源与超时限制 |
| Worker | 同一 Python 包的独立进程入口 | Outbox、Sweeper、Reminder、IMAP bounce；不引入 Celery 或消息队列 |
| 前端测试 | Vitest、Testing Library、Playwright、axe-core | 单元、可访问性、桌面 E2E 与截图回归 |
| 后端测试 | pytest、pytest-asyncio、HTTPX | 单元、契约、真实 PostgreSQL/Redis 集成与并发测试 |
| 工程门禁 | ESLint、Prettier、Ruff、mypy、Redocly CLI | 格式、类型、OpenAPI 标准 lint |
| 本地/交付 | Docker Compose | PostgreSQL+pgvector、Redis、API、Worker；生产云资源另行批准 |

所有直接依赖在首次 implementation TASK 中锁定精确版本并提交 lockfile；不得仅使用宽松版本范围。新增未列依赖必须 Stop & Report。

## 2. 仓库布局

```text
apps/web/             React/Vite
apps/api/app/         FastAPI 模块化单体
apps/api/migrations/  Alembic
apps/api/tests/       Python 测试
tests/e2e/            Playwright
infra/compose/        本地与可逆 smoke 配置
```

后端按业务模块分包（auth、appointments、notifications、knowledge、ai、admin），共享代码仅在第三次真实复用时抽取。API、Worker 和 Scheduler 共用领域/数据访问代码，但以不同进程入口运行。

## 3. 选择理由

- Python 对 RAG、文档解析和 DeepSeek 接入最直接；FastAPI 可从同一 schema 保持 OpenAPI 实现一致。
- React/TypeScript 适合高交互预约网格、SSE 状态收敛和可访问性测试，也能把页面二做成面试可演示的作品页。
- PostgreSQL/pgvector 复用已批准架构，不增加独立向量库；Redis 仅承担安全设计中的限频。
- 独立 Python Worker 足够覆盖当前低吞吐 Outbox，不引入 Celery、Kafka、RabbitMQ 或微服务。
- 前后端分语言增加少量工程成本，但更能展示 AI 全栈岗位所需的产品前端、契约、后端事务和 AI 工程能力。

## 4. 明确不采用

- LangGraph、MCP、Mem0、Agent 自动预约：baseline 明确 deferred/禁止。
- Next.js SSR：三页主体可静态交付，SSR 增加部署与 Cookie 边界复杂度而无必要收益。
- NestJS：本项目的 AI/RAG 与文档处理以 Python 更低摩擦；`sleep202603-an` 已能作为 NestJS 工程证据，不必在本项目重复。
- Celery、Kafka、RabbitMQ、独立向量数据库、Kubernetes：超出 MVP 规模和已批准架构。
- ORM 自动生成关键并发事务：预约锁序、`SKIP LOCKED`、CAS 和部分索引使用显式 SQL/迁移验证，避免 ORM 隐藏语义。

## 5. 人工批准边界

接受本 ADR 只批准技术栈与依赖类别，不等于批准：

- security v0.1 中的 BCrypt、会话、Redis、IMAP、AES/HMAC 与密钥策略；
- 数据库 migration 的实际 SQL；
- 鉴权、加密、外部通知、Prompt/工具权限实现；
- 腾讯云、域名、备案、SMTP/IMAP、飞书或任何付费/不可逆外部操作。

上述项目仍须按各 implementation/migration TASK 单独提交用户审查。

## 6. 重裁触发

- 托管 PostgreSQL 无法启用 pgvector；
- 浏览器目标或 SEO 要求变为必须 SSR；
- 事件量、实例数或延迟超过 architecture 0.2 的升级阈值；
- 需要新增消息中间件、Agent 框架、外部向量库或改变部署形态；
- 冻结测试无法在该栈真实执行。
