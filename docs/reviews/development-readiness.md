# 开发准入评审（2026-08-09）

## 结论

**PASS：10/10 项 approved。** SRS、安全、OpenAPI/SSE、测试计划均已完成 impact review、批准与 `spec_sync=clean`；实现栈 ADR 已 accepted，且实现任务与独立审查任务已建立。

## 1. development_gate 实际状态

| 工件 | 版本 | 状态 | 结论 |
|---|---:|---|---|
| PRD | 2.3.3 | approved | PASS |
| use_cases | 1.7.2 | approved | PASS |
| domain_model | 1.1.5 | approved | PASS |
| SRS | 1.2 | approved | PASS |
| ui_wireframe | 1.0 | approved | PASS |
| architecture | 0.2 | approved | PASS |
| security | 0.1 | approved | PASS |
| openapi | 0.1 | approved | PASS |
| test_plan | 0.1 | approved | PASS |
| ai_governance | 1.0.1 | approved | PASS |

唯一判定源为 `docs/baseline.yml`。任何汇报、TASK 或提交信息都不能替代这里的状态。

## 2. 待用户一次性评审的内容包

| 决定 | 当前内容快照 | 需要确认的实质 |
|---|---|---|
| 批准 SRS 1.2 | `ab4b94e` / `1c443eb` | `AUTH_EXPIRED` 仅会话过期；限频=`RATE_LIMITED`；Override 两个回滚错误码 |
| 批准 security 0.1 | `c2f08f2` / `010e3e1` | BCrypt cost 12；PostgreSQL 不透明会话；Redis 限频；IMAP 退信；AES-256-GCM/HMAC 与密钥轮换 |
| 批准 OpenAPI/SSE 0.1 | `2c8cede` / `3e2b58b` | 33 个操作、显式 401/403、CSRF、条件鉴权、密码字节规则；Redocly 0 error / 0 warning |
| 批准 test-plan 0.1 | `60b56b2` / `ebe6c1a` | 69 个冻结 TC；R1-R26 与 33 operationId 全覆盖；真实 PostgreSQL/Redis 并发与安全门禁 |
| 接受 ADR-IMPL-001 | `0a86a96` / `99678dc` | React/TypeScript/Vite + FastAPI/Python + PostgreSQL/pgvector + Redis + 独立 Worker 的依赖边界 |

批准安全设计仍不等于批准具体鉴权、加密、外部通知或 migration 实现。它们必须在各自代码 TASK 中给出实际 diff、测试和回滚，由用户另行审查。

## 3. 批准后的固定执行顺序

1. SRS/security/OpenAPI/test_plan 已完成独立批准与 `spec_sync=clean` 收口。
2. ADR-IMPL-001 已从 `proposed` 推进为 `accepted`。
3. `TASK-IMPL-WEB-001` 与 `TASK-REVIEW-WEB-001` 已建立，开发任务只写获批范围，当前任务负责监督与验收。
4. 当前复核通过后允许启动独立开发窗口。

## 4. 首批开发拆分

| 顺序 | 实现任务 | 交付目标 | 人工审查点 |
|---|---|---|---|
| 1 | WEB-SHELL | React 框架、三页导航、页面一/二真实内容、响应式阻断 | 无外部写；优先产出今晚可展示页面 |
| 2 | DB-MIGRATION-001 | 领域模型 1.1.5 的 schema、约束、索引与 up/down | 数据库迁移必须用户审批 |
| 3 | AUTH-001 | 注册/验证/登录/会话/找回/CSRF/限频 | 鉴权、BCrypt、Redis、Cookie 必须用户审批 |
| 4 | AI-001 | 页面问答、RAG、推荐问题、AI SSE | Prompt 与工具权限必须用户审批；无预约工具 |
| 5 | APPOINTMENT-001 | Slot、预览、创建/改期/取消、并发锁序、Slot SSE | 真实 PostgreSQL 并发冻结 TC |
| 6 | NOTIFY-001 | Outbox/邮件/飞书/退信/提醒/失败中心 | 外部通知必须用户审批；本地协议替身先行 |
| 7 | ADMIN-001 | Override、公告、知识库、应急只读、例外 | RBAC/IDOR、上传解析和审计 |
| 8 | RELEASE-001 | Compose、staging、域名/HTTPS/备份/监控 | 付款、云资源、域名和不可逆操作先确认 |

WEB-SHELL 是首个获准实现任务，可先形成今晚可展示的视觉成果；后端、鉴权、迁移、通知和基础设施仍必须拆分为独立任务并接受相应人审。

## 5. 外部阻塞与可并行事项

- 付款前确认：域名、腾讯云资源、托管 PostgreSQL/Redis、对象存储或其他付费服务。
- 不可逆前确认：域名注册、备案提交、生产 DNS、生产凭证授权、正式部署切流。
- 可先做：本地开发、静态视觉验收、协议级替身、测试容器、迁移草案与本地 up/down；其中安全/迁移/通知代码仍要在合并前由用户审批。
- `sleep202603-an` 永久只读，仅可提取已核验证据与可复用视觉素材副本；不得修改其工作树。
