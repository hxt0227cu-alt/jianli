# Jianli API

Jianli 后端服务：认证、面试预约、AI 问答（RAG + Agent 工具循环）、知识库管理与 Outbox 通知。

## 模块

| 模块 | 职责 |
|------|------|
| `app/auth/` | 注册 / 登录 / 找回 / CSRF / 限频 / 字段加密 |
| `app/appointments/` | 时段物化与预约（事务 / 锁 / SSE） |
| `app/aiqa/` | AI 问答：检索 / 人格层 / Agent 工具循环 / 知识库 |
| `app/notifications/` | Outbox Worker：邮件 + 飞书 |
| `app/admin/` | 管理端：预约 / 知识库 / 联系人配置 |

## 本地运行

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.lock

alembic upgrade head
python -m uvicorn app.main:app --reload
```

配置读取 `JIANLI_*` 环境变量（模板见 `.env.prod.example`；本地开发可 `source ../scripts/dev-env.sh` 生成 gitignore 的 `.env.local`）。

## Worker

独立通知 Worker 进程（Outbox 消费 / 重试 / 临近提醒 / 飞书同步）：

```bash
python -m app.worker
```

## 质量门禁

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy app
```

## 接口契约

- OpenAPI：`../docs/api/openapi.yaml`
- SSE 协议：`../docs/api/sse.md`
