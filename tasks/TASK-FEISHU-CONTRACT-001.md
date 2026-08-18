# TASK-FEISHU-CONTRACT-001 CR：新增 updateOwnerContactConfig 契约端点（R13 open_id 配置入口）

> **状态：draft（CR 草案，待用户批准后生效；批准后由独立 implementation TASK 实现代码）**
> 依据已批准 SRS v1.3 §3.8（R13 候选人双通道）/ 领域模型 v1.1.5 §6.12（candidate_notification 收件人解析：活跃 owner_admin → OwnerContactConfig.candidate_feishu_open_id_ciphertext，AES 密文）+ security v0.1（敏感字段 AES-256-GCM、owner_admin RBAC）。属**已批准 MVP 行为缺配置入口**的契约补全，非新需求语义变更。

## 任务类型
- documentation  # 文档：Change Request + OpenAPI 契约更新

## 基线版本与基线 commit
- baseline：SRS 1.3 / 领域模型 1.1.5 / architecture 0.2 / security 0.1 / OpenAPI 0.2（取自 `docs/baseline.yml`）
- 基线 commit：`c87b6c6`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.8（R13 双通道提醒、候选人=owner_admin 本人、飞书接收标识）
- `docs/design/domain-model.md` §6.1（`uq_active_owner_admin` 部分唯一索引 + 运行不变量：恰一活跃 owner_admin）
- `docs/design/domain-model.md` §6.12（`candidate_feishu_open_id_ciphertext` 字段语义：AES 密文、收件人解析链路固定）
- `docs/design/security.md`（AES-256-GCM 字段加密、owner_admin RBAC、CSRF）
- `docs/api/openapi.yaml`（v0.2 现有 admin operation 风格：CsrfToken 参数、owner_admin security、Problem 错误响应）

## 需求来源
- R13（双通道提醒，UC-12）：候选人（owner_admin）飞书消息发送需要 `candidate_feishu_open_id_ciphertext` 非空
- 现状缺口：该字段 0001 建表后**无任何写入口**（admin 域 10 个 operation 无 owner_contact 相关）→ R13 飞书消息无法真发（当前仅缺 open_id 时 failed + 告警的降级路径）

## 目标
变更请求：**OpenAPI v0.2 → v0.3**，新增一个 admin 写端点：

| 项 | 内容 |
|---|---|
| 端点 | `PUT /admin/owner-contact-config` |
| operationId | `updateOwnerContactConfig` |
| 权限 | owner_admin + `CsrfToken`（写操作，同现有 admin 写端点） |
| 请求体 | `OwnerContactConfigInput`：`{ "candidate_feishu_open_id": string }`（明文入参，服务端 AES 加密落库） |
| 响应 | `200` `OwnerContactConfigView`：`{ "configured": true }`；401/403/404 Problem 错误 |
| 行为语义 | 对唯一活跃 owner_admin 的 `owner_contact_configs` 行 upsert：无行则建、有行则更新 `candidate_feishu_open_id_ciphertext`（AES-256-GCM，AAD=owner_contact_configs 表/列/config 行 id）；无活跃 owner_admin → 404 + 告警（领域模型 §6.1 不变量） |

## 非目标（明确排除）
- 不实现代码/前端/测试（本任务仅契约；实现走后续独立 TASK）
- 不新增其它配置字段（仅 candidate_feishu_open_id_ciphertext；candidate_phone_ciphertext 暂不纳入）
- 不改变 R13 消息发送语义、不改变收件人解析链路、不新增公开（非 admin）端点
- 不改 SRS / 领域模型 / 安全设计（R13 已批准，本 CR 仅补配置入口契约）

## 允许修改路径
- `docs/api/openapi.yaml`（v0.2 → v0.3：新增 `/admin/owner-contact-config` path + `OwnerContactConfigInput`/`OwnerContactConfigView` schema）
- `docs/change-requests/CR-FEISHU-OPENID-001.md`（本 CR 文档，如目录不存在则创建）
- `tasks/TASK-FEISHU-CONTRACT-001.md`（本任务单）
- `docs/baseline.yml`（openapi.version 0.2 → 0.3 + status 推进；仅限 CR 批准后由用户显式确认）

## 禁止修改路径
- `apps/**`（代码、测试、迁移）
- `docs/requirements/**`、`docs/design/**`（SRS/领域模型/架构/安全设计不改）
- 既有 OpenAPI operation / schema（只增不删不改）

## 已批准的 DB / API / 依赖变更
- 无（契约先行；DB 字段 0001 已建、无需迁移；无新依赖）

## 规范影响评估（spec impact）
- behavior_change：**true**（新增 admin 配置端点 = 用户可观察行为变化）→ 分类：**真正改变用户可观察行为 → 先 Change Request → 更新并 approve 规范 → 再创建 implementation TASK**
- affected_specs：
  - openapi：**update**（v0.2 → v0.3，新增 1 operation + 2 schema）
  - srs：none（R13 已批准，配置入口是补全非语义变更）
  - domain_model：none（字段已批准）
  - security：none（沿用既有 AES/RBAC/CSRF 模式）
  - test_plan：none（实现阶段补 TC）

## 功能验收（契约层）
- Redocly 校验 0 error / 0 warning（与既有契约一致）
- 新端点出现在 `/admin/owner-contact-config`，operationId=`updateOwnerContactConfig`，含 CsrfToken 参数与 200/401/403/404 响应

## 安全与隐私验收（契约层）
- 请求体声明明文 open_id；落库语义在实现 TASK 中 AES 加密（本契约仅声明行为）
- 仅 owner_admin security（cookieSession），写强制 CSRF

## 性能验收
- 无新增生产路径（契约文档）

## 变更预算（change_budget）
- max_files：3（openapi.yaml + CR 文档 + 任务单）
- expected_prod_lines：0（纯契约）
- expected_test_lines：0

## 必须运行的测试命令
- `npx @redocly/cli lint docs/api/openapi.yaml`（或项目既有 Redocly 命令）→ 0 error / 0 warning

## 回滚方法
- `git checkout -- docs/api/openapi.yaml`（还原 v0.2；未批准前不推进 baseline 状态）

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 若新增端点与已批准 SRS/领域模型语义冲突 → 停止报告
- 若需改 SRS/领域模型/安全设计（超出现状）→ 停止，扩 CR 范围
- 超出 change_budget → 拆任务

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<待提交后回填>
- 修改文件清单：<与「允许修改路径」逐一对照>
- 测试命令及结果：Redocly lint → <0 error / 0 warning>
- lint / typecheck：Redocly（YAML 无 py/ts 门禁）
- DB 迁移验证：无
- 验收证据：<契约 diff 摘要 + Redocly 输出>
- 变更预算实际值：<max_files / 行数，与预算对照>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否 / 偏离项及原因>
- 规范影响结论：openapi updated（v0.3 待用户批准）
- spec_sync：clean（仅 openapi 单工件推进；SRS/领域模型 based_on 不变）
- verified_commit：<待提交后回填>
- **关闭门禁（四条件）**：① Redocly 通过；② 规范影响已处理（openapi v0.3 待用户批准后视为处理）；③ spec_sync clean；④ verified_commit 真实 sha。

## 关联
- Change Request：`docs/change-requests/CR-FEISHU-OPENID-001.md`
- 实现任务：后续 TASK-FEISHU-CONTRACT-002（owner_admin 端点 + AES 落库 + 前端输入框 + 测试）——**须在本 CR 批准后创建**
- 前置：用户已批准端点设计（2026-08-18）；候选人 open_id=`[open_id已脱敏]`（用户本人，用于实现后真连验证）
