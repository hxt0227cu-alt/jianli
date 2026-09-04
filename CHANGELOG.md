# Changelog

本项目遵循语义化版本节奏但尚未打正式 tag，以下按阶段汇总里程碑（详见 `PROJECT_STATE.md` 任务台账）。

## [Unreleased]

- 公开仓库初始化：数据脱敏、示例简历素材、README / LICENSE / CONTRIBUTING / SECURITY 补充。

## 2026-09（知识库刷新 + 开源发布）

- **知识库随新简历刷新**（TASK-KB-RESUME-REFRESH-001，2026-09-04）：CORPUS 扩至 23 篇真实语料、content.py 静态兜底与 persona few-shot 同步、seed_kb 分批上传修复（20+3）；
- **RAG 评测全链路验证**：真实 LLM + BGE-M3 38 题严格一致率 38/38=100%（SLO ≥94% 达成）、越界拒答 reject 10/10、极端相似 extreme 9/9 硬断言通过；
- **开源发布**：全历史 commit PII 脱敏重写（姓名 / 学校 / 手机号 / 邮箱 / 专利号 / open_id → 占位符），推送至公开 GitHub 仓库。

## 2026-08（M 系列里程碑）

### M6 · AI 问答域 + 知识库（2026-08-13）

- RAG + 人格层（L1）：静态页知识源 → 知识库优先检索（pgvector）→ 无依据拒答；
- 会话持久化、知识库上传 / 删除 / 热更新（md/txt/PDF，10MB 上限）；
- `streamAnswer` SSE 流式（started → delta* → citations → completed）。

### M5 · 预约通知与 SSE（2026-08 中旬）

- Outbox 可靠通知：`NotificationEvent` + Worker 领取 / 重试 / 超时回收 / 幂等投递；
- 邮件 + 飞书多维表格同步与消息提醒双通道；临近提醒调度；
- SSE 面试表实时推送。

### M4 · 面试预约（2026-08 上旬）

- 动态时段物化 + 统一锁顺序 + 行锁 + 幂等，解决并发超卖；
- 敏感字段 AES-256-GCM 加密、公司指纹去重；
- 预约 / 改期 / 取消全流程 + owner_admin 管理。

### M3 · 通知 Worker（2026-08 中旬）

- 独立通知 Worker 进程、SMTP 投递、投递状态机与重试。

### M2 · 认证（2026-08 上旬）

- 注册 / 登录 / 找回 / 邮箱验证码、CSRF、限频、记住我、字段加密。

### M1 · 后端骨架与领域建模（2026-08 初）

- FastAPI + SQLAlchemy + Alembic 骨架；领域模型 / SRS / 架构 / 安全设计评审通过；
- 身份 / 预约 / Outbox / AIQA 四组 schema 迁移（0001–0004）。

## 2026-07 · 规划与设计

- PRD v2.3 基线、用例规约、领域模型、架构设计、安全设计、OpenAPI 契约评审；
- 建立 AI 治理流程（任务驱动 / 双角色审查 / 门禁 / 唯一真相源）。

## 早期 · 简历素材与知识库语料

- 个人简历语料整理（示例）、荔枝毕设与睡眠健康项目素材沉淀。
