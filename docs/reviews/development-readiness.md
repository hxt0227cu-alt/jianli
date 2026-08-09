# 开发准入评审（2026-08-09）

## 结论

**BLOCKED：当前 6/10 项 approved，4/10 项 review。** 设计链已经完整，尚差人工批准与下游 `spec_sync` 收口；不是内容未产出，也不是代码或环境故障。

## 1. development_gate 实际状态

| 工件 | 版本 | 状态 | 结论 |
|---|---:|---|---|
| PRD | 2.3.3 | approved | PASS |
| use_cases | 1.7.2 | approved | PASS |
| domain_model | 1.1.5 | approved | PASS |
| SRS | 1.2 | review | BLOCK |
| ui_wireframe | 1.0 | approved | PASS |
| architecture | 0.2 | approved | PASS |
| security | 0.1 | review | BLOCK |
| openapi | 0.1 | review | BLOCK |
| test_plan | 0.1 | review | BLOCK |
| ai_governance | 1.0.1 | approved | PASS |

唯一判定源为 `docs/baseline.yml`。任何汇报、TASK 或提交信息都不能替代这里的状态。

## 2. 待用户一次性评审的内容包

| 决定 | 当前内容快照 | 需要确认的实质 |
|---|---|---|
| 批准 SRS 1.2 | `b162c0a` | `AUTH_EXPIRED` 仅会话过期；限频=`RATE_LIMITED`；Override 两个回滚错误码 |
| 批准 security 0.1 | `119d35f` | BCrypt cost 12；PostgreSQL 不透明会话；Redis 限频；IMAP 退信；AES-256-GCM/HMAC 与密钥轮换 |
| 批准 OpenAPI/SSE 0.1 | `4fb0d01` + `1f7eb3d` | 33 个操作、Cookie/CSRF/RBAC/429、Slot/AI SSE 恢复；Redocly 0 error |
| 批准 test-plan 0.1 | `204c2b8` | 69 个冻结 TC；R1-R26 与 33 operationId 全覆盖；真实 PostgreSQL/Redis 并发与安全门禁 |
| 接受 ADR-IMPL-001 | `a059263` | React/TypeScript/Vite + FastAPI/Python + PostgreSQL/pgvector + Redis + 独立 Worker 的依赖边界 |

批准安全设计仍不等于批准具体鉴权、加密、外部通知或 migration 实现。它们必须在各自代码 TASK 中给出实际 diff、测试和回滚，由用户另行审查。

## 3. 批准后的固定执行顺序

1. 生成 SRS 与 security 的独立批准锚点。
2. 对 OpenAPI/SSE 做一次上游 impact review；确认错误码、安全头、Cookie/CSRF 与限频契约一致后批准。
3. 对 test-plan 做一次 impact review；确认冻结 TC 未降级后批准。
4. 将 ADR-IMPL-001 从 `proposed` 推进为 `accepted`。
5. 回填各 TASK 的 `approval_commit` / `verified_commit`，把 `spec_sync` 转为 clean。
6. 重新读取 baseline；十项全部 approved 才把本准入结论改为 PASS。
7. 建立独立 implementation TASK 和独立审查任务；开发任务只写获批范围，当前任务负责监督与验收。

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

WEB-SHELL 可以最先形成视觉成果，但按仓库规则仍须等十项门禁通过和 ADR accepted 后才能写入；不能用“只是前端”绕过准入。

## 5. 外部阻塞与可并行事项

- 付款前确认：域名、腾讯云资源、托管 PostgreSQL/Redis、对象存储或其他付费服务。
- 不可逆前确认：域名注册、备案提交、生产 DNS、生产凭证授权、正式部署切流。
- 可先做：本地开发、静态视觉验收、协议级替身、测试容器、迁移草案与本地 up/down；其中安全/迁移/通知代码仍要在合并前由用户审批。
- `sleep202603-an` 永久只读，仅可提取已核验证据与可复用视觉素材副本；不得修改其工作树。
