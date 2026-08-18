# CR-FEISHU-OPENID-001 — 新增 `updateOwnerContactConfig` 契约端点（R13 open_id 配置入口）

## 摘要

- **状态**：proposed（待用户批准）
- **提出日期**：2026-08-18
- **依据**：已批准 SRS v1.3 §3.8（R13 候选人双通道提醒）/ 领域模型 v1.1.5 §6.12（`candidate_feishu_open_id_ciphertext` 收件人解析链路）/ security v0.1（AES-256-GCM、owner_admin RBAC、CSRF）
- **关联任务**：`tasks/TASK-FEISHU-CONTRACT-001.md`（契约 CR）+ 后续 `TASK-FEISHU-CONTRACT-002`（实现）

## 问题陈述

R13 候选人飞书消息的收件人解析依赖 `owner_contact_configs.candidate_feishu_open_id_ciphertext`（AES 密文，领域模型 §6.12）。该字段在迁移 0001 建表后**无任何写入口**——admin 域现有 10 个 operation（`adminListAppointments`/`forceCancelAppointment`/availability overrides 三件套/company exception/3 个 AIQA 只读）均不涉及 owner_contact_configs。因此：

- 桩测试覆盖了"open_id 缺失 → feishu 通道 failed + 告警、email 照常"的降级路径（符合领域模型 §6.1 不变量）
- 但**真实 R13 飞书消息永远无法发送**——缺配置入口

## 变更内容

**OpenAPI v0.2 → v0.3**，新增一个 admin 写端点：

| 项 | 内容 |
|---|---|
| 端点 | `PUT /admin/owner-contact-config` |
| operationId | `updateOwnerContactConfig` |
| 权限 | owner_admin（`cookieSession` security）+ `CsrfToken` 参数（与 `forceCancelAppointment` 等现有写端点一致） |
| 请求体 | `OwnerContactConfigInput`：`{ "candidate_feishu_open_id": string, minLength: 5, maxLength: 100 }`（明文入参） |
| 响应 | `200` `OwnerContactConfigView`：`{ "configured": true }`；`401` Unauthorized / `403` Forbidden / `default` Error（无活跃 owner_admin 场景由 default 兜底，与全契约风格一致——现有端点均无显式 404） |
| 行为语义 | 对唯一活跃 owner_admin（`uq_active_owner_admin`）的 `owner_contact_configs` 行 upsert：无行则 INSERT、有行则 UPDATE `candidate_feishu_open_id_ciphertext`（AES-256-GCM 加密，AAD=owner_contact_configs 表/列/config 行 id）；无活跃 owner_admin → 404 + 运维告警（领域模型 §6.1 不变量：不得任选顶替） |
| 契约新增 schema | `OwnerContactConfigInput`、`OwnerContactConfigView` |

## 不变量与安全（不变）

- 落库仍为 **AES-256-GCM 密文**（沿用 crypto.py FieldCipher）；open_id 明文仅经请求体传输，服务端加密，日志脱敏
- 仅 owner_admin 可配置（候选人=站点 owner 本人，领域模型 §6.1 单 owner 决议）
- 不改变 R13 消息发送语义 / 收件人解析链路 / 通道失败隔离
- 不改 SRS / 领域模型 / 安全设计（配置入口属已批准 MVP 行为的契约补全）

## 受影响工件

| 工件 | 变更 |
|---|---|
| `docs/api/openapi.yaml` | v0.2 → v0.3：新增 `/admin/owner-contact-config` + 2 schema |
| `docs/baseline.yml` | openapi.version=0.3 + status 推进（**待用户批准后由用户显式确认，AI 不自行推进**） |
| 其它规范工件 | none |

## 批准后动作

1. 用户批准本 CR + OpenAPI v0.3
2. 创建实现任务 `TASK-FEISHU-CONTRACT-002`（后端端点 + AES 落库 + 前端 admin 输入框 + 测试）
3. 实现后用户 WSL 验证（配置 open_id → R13 真发飞书消息到 `[open_id已脱敏]`）

## 关联

- 前置：用户已批准端点设计（2026-08-18）
- 候选人 open_id：`[open_id已脱敏]`（用户本人，实现后真连验证用）
