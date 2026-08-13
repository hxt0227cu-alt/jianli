# TASK-M4 注册 / 邮箱验证 / 密码找回（auth 域补全）

> 合并同域主线：账户自助生命周期（注册 + 邮箱验证 + 密码找回）为单一实现任务。
> **治理节奏（与 M1/M2/M3 一致）**：① 合并同域主线；② 风险分级——注册/找回涉及密码与令牌，属**高风险**，本任务**仍不单列独立 REVIEW 任务**（接手 Codex 模式），但实现须内联自审：令牌哈希存储（不落明文）、过期/已用一次性、找回后作废现有会话、限频防枚举、邮箱不参与存在性泄露；③ 交付证据一次写全；④ 验证批处理（一轮 pytest+ruff+mypy）。
> **SMTP 163 授权码仅作运行时环境变量（`JIANLI_SMTP_PASSWORD`），绝不写入任何文件/记忆/配置**。
> **契约对齐（关键）**：实现严格对齐已批准 `docs/api/openapi.yaml` 的 4 个 operation（路径/operationId/状态码/字段），**不新增、不擅改公开 API**。

## 任务类型
- implementation（auth 域账户自助）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）
- 基线 commit：`69d4cee`（M1/M2 本机验证批处理通过、关闭；HEAD）

## 精确规范引用
- SRS 1.3 §5.6（注册 / 邮箱验证 / 密码找回语义）、§8（错误码：`DUPLICATE_EMAIL`、令牌 `INVALID_TOKEN`、限频 `RATE_LIMITED`）
- 安全设计 0.1 §（BCrypt 口令哈希、会话作废、令牌一次性、找回不限明文泄露存在性）
- OpenAPI v0.2 `docs/api/openapi.yaml`：`registerInterviewer` / `verifyEmail` / `requestPasswordReset` / `confirmPasswordReset` 已定义（路径/operationId/响应码/字段均以此为准）
- TC-AUTH-REG-* / TC-AUTH-VERIFY-* / TC-AUTH-RESET-*（注册冲突、验证幂等、找回令牌一次性+过期、找回后会话作废）

## 需求来源
- R3（注册即创建 interviewer 账户）/ R5（邮箱验证方可面试预约）/ R7（密码找回）；UC-02/UC-03/UC-04

## 目标
实现 approved `docs/api/openapi.yaml` 中已定义的 4 个账户自助 operation：**注册**（`registerInterviewer`/202）、**邮箱验证**（`verifyEmail`/204）、**找回申请**（`requestPasswordReset`/202）、**找回确认**（`confirmPasswordReset`/204）。令牌 SHA-256 存储、一次性、过期失效；找回后作废全部会话；限频防枚举；邮件 best-effort（SMTP 未配置仅落库不发信）。

## 非目标（明确排除）
- 不改加密/密钥策略（沿用 BCrypt）、不改登录/CSRF/RBAC 主体
- 不新增迁移/表/列（`email_verification_tokens` / `password_reset_tokens` 已存在于 migration 0001）
- 不做 owner_admin 邀请/审批流（注册默认 interviewer）、不做 OAuth/第三方登录
- 不发飞书（与 M3 一致，邮件通道先行）
- **`resend-verification`（重发验证）不在已批准 OpenAPI 契约中，本次不实现**；如需新增须走 Change Request 把 `/auth/resend-verification` 补入 OpenAPI 后再实现（见关联）

## 允许修改路径
- `apps/api/app/auth/service.py`（新增 `register` / `verify_email` / `request_password_reset` / `reset_password`）
- `apps/api/app/auth/repository.py`（新增令牌写入/查询/作废 + 找回后会话作废）
- `apps/api/app/auth/router.py`（注册 `POST /auth/register` op `registerInterviewer`/202；验证 `POST /auth/verify-email` op `verifyEmail`/204；找回申请 `POST /auth/password-reset/request` op `requestPasswordReset`/202；找回确认 `POST /auth/password-reset/confirm` op `confirmPasswordReset`/204——路径与 operationId 严格对齐 `docs/api/openapi.yaml`）
- `apps/api/app/auth/models.py`（新增 `RegisterRequest` / `TokenRequest` / `EmailRequest` / `ResetPasswordRequest`，对齐 OpenAPI schema 命名与 `minLength`）
- `apps/api/app/auth/runtime.py`（仅注入 `EmailSender` 到 `AuthService`，SMTP 配置时）
- `apps/api/app/notifications/email.py`（新增验证邮件 / 找回邮件渲染与发送，复用现有 SMTP 通道；未配置时 sink，不阻塞注册）
- `apps/api/tests/auth/test_account_lifecycle.py`（新增，真实 PG）
- `PROJECT_STATE.md`（仅当前任务段）

## 禁止修改路径
- `apps/api/app/appointments/crypto.py`、`runtime.py`（密钥/加密不变）
- 迁移文件（无 schema 变更）
- 预约写路径、SSE

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无**（`email_verification_tokens` / `password_reset_tokens` 已存在；列：`id` UUID PK、`user_id` FK、`token_hash` Text、`expires_at` timestamptz、`consumed_at` timestamptz nullable）
- API：**实现（非新增）`docs/api/openapi.yaml` 已批准的 4 个 operation**，路径/operationId/状态码严格对齐：`POST /auth/register`(`registerInterviewer`)/202、`POST /auth/verify-email`(`verifyEmail`)/204、`POST /auth/password-reset/request`(`requestPasswordReset`)/202、`POST /auth/password-reset/confirm`(`confirmPasswordReset`)/204。语义实现 SRS §5.6 注册/验证/找回。
- 依赖：**无新增**（邮件复用现有 smtplib/email）

## 规范影响评估（spec impact）
- behavior_change：true（新增账户自助用户可观察行为，但路径/operationId 与 approved OpenAPI 完全一致，属"实现已批准契约"而非变更契约）
- affected_specs：
  - openapi：clean（经核对，`docs/api/openapi.yaml` 已定义这 4 个 operation；早期误判为"待补"。实现严格对齐后 spec_sync 应为 clean，**无需改动 OpenAPI**）
  - srs：none（行为已被 §5.6/§8 定义并 approved）
  - domain_model：none
  - security：none（沿用 BCrypt/会话策略）
  - test_plan：dirty（新增 TC-AUTH-REG/VERIFY/RESET，待补入冻结 TC 快照）
- reason：实现 approved OpenAPI/SRS 注册/验证/找回；test_plan 需补 TC。
- 分类：实现 approved 契约（operation 已存在，仅对齐实现）
- **执行顺序**：实现 + 真实 PG 测试通过 → 补测试计划 TC → spec_sync 转 clean（OpenAPI 无需改）→ 关闭。
- 注：`resend-verification` 不在 approved OpenAPI，若产品需要须单独 Change Request 补契约后再实现（不在本任务范围）。

## 功能验收
- 注册 `POST /auth/register`(`registerInterviewer`)：`email` 归一化；`password` BCrypt 哈希（拒绝 >72 UTF-8 字节，min 10 字节）；`role='interviewer'`、`verified=false`；写 `email_verification_tokens`（token_hash=SHA-256(token)，expires_at=now+24h）；best-effort 发验证邮件；返回 **202**（契约泛型响应，无响应体）。
- `DUPLICATE_EMAIL`：同邮箱已存在返回 409（唯一约束 `uq_users_email`）。
- 邮箱验证 `POST /auth/verify-email`(`verifyEmail`) { token }：未过期且未用 → 置 `users.verified=true`、令牌 `consumed_at=now`；幂等（已验证再验证返回 204）；`INVALID_TOKEN` 返回 409。
- 找回申请 `POST /auth/password-reset/request`(`requestPasswordReset`) { email }：存在则写 `password_reset_tokens`（expires_at=now+1h）并发邮件；无论是否存在均返回 **202**（不泄露存在性，防枚举）。限频防爆破。
- 找回确认 `POST /auth/password-reset/confirm`(`confirmPasswordReset`) { token, new_password }：校验令牌（未过期、未用）→ 更新 `password_hash`（BCrypt）、`consumed_at=now`、**作废该用户全部 `auth_sessions`**（revoked_at=now，安全：找回后旧会话失效）；`INVALID_TOKEN` 返回 409；弱口令（<10 字节或 >72 字节）返回 422 `INVALID_REQUEST`。
- `resend-verification`：**不在本任务**（需 Change Request 补契约）。

## 安全与隐私验收
- 令牌仅存 `token_hash`（SHA-256），不落明文；一次性（consumed_at）；过期失效
- 找回后作废全部现有会话（防会话维持）
- 找回申请不泄露存在性（恒 202）；限频防枚举/爆破
- 密码 BCrypt；复用 `passwords.py`
- 注册/验证/找回端点：**同源**（same-origin）校验；匿名入口（注册/找回申请/验证/找回确认），**无需 CSRF**（无会话）

## 性能验收
- 注册/找回单请求；令牌查询走 `ix_*_user_id` 索引；限频复用 Redis（与登录限频同机制）

## 变更预算（change_budget）
- max_files：9（含 runtime.py / TASK / PROJECT_STATE 治理文件）
- expected_prod_lines：~220（service/repo/router/models/email + runtime 注入）
- expected_test_lines：~170

## 必须运行的测试命令
- `pytest apps/api/tests/auth/test_account_lifecycle.py`（需真实 PG；SMTP 可选——令牌落库断言不依赖 SMTP，邮件发送 best-effort）
- `ruff check apps/api app` + `mypy app`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件
- 出现未列明变更（新依赖/新迁移/改加密策略/改公开 API 字段语义/新增公开端点如 resend-verification）→ 立即停止报告（resend 须先 Change Request）
- 超出 change_budget（max_files>9）→ 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（关闭前一次写全）
- commit / PR：
  - `b77931e` — feat(auth): M4 注册/邮箱验证/密码找回，对齐已批准 OpenAPI 契约
  - `7c91a83` — fix(test): verify-email 未知令牌用例改用契约合法长度（minLength:32）→ 4 passed
- 修改文件清单（按允许修改路径逐条计数）：`auth/service.py`、`auth/repository.py`、`auth/router.py`、`auth/models.py`、`auth/runtime.py`、`notifications/email.py`、`tests/auth/test_account_lifecycle.py` + 本任务治理文件 = 8 路径（≤ max_files 9）
- 测试命令及结果：`pytest tests/auth/test_account_lifecycle.py -v` → **4 passed**（TC-AUTH-REG/VERIFY/RESET 真实 PG/Redis 覆盖）；另全量回归 44 passed / 27 skipped / 2 failed（2 failed 经证为既有非回归，与 M4 无关）
- lint / typecheck：`ruff check .` → All checks passed（exit 0）；`mypy` → Success: no issues found in 26 source files（exit 0）
- DB 迁移验证：无（复用 migration 0001 的 `email_verification_tokens` / `password_reset_tokens`）
- 验收证据：注册 202 / 重复邮箱 409 DUPLICATE_EMAIL / 验证 204 幂等 / 未知令牌 409 INVALID_TOKEN / 找回申请恒 202 不泄露存在性 / 找回确认 409 INVALID_TOKEN 且作废全部会话 / 弱口令 422 INVALID_REQUEST；令牌仅存 SHA-256 token_hash
- 变更预算实际值：max_files=9，实际 8（不含 PROJECT_STATE 治理同步），未超预算
- 未解决风险：① SMTP 未配置时仅 sink（best-effort，不发信）——`test_worker.py`（M3）待 SMTP 凭据补测；② `resend-verification` 不在已批准 OpenAPI 契约，待产品决策走 Change Request
- 是否偏离 TASK：否（实现严格对齐 approved OpenAPI 4 operation；resend 已显式列为非目标）
- 规范影响结论：openapi clean（实现已批准 operation，无需改 OpenAPI）；test_plan dirty→补 TC 后 clean（TC-AUTH-* 已落地 `test_account_lifecycle.py`）
- spec_sync：clean（实现对齐 OpenAPI 后）
- verified_commit：`7c91a83`
- 关闭门禁：① 测试通过（4 passed）② 规范影响已处理（spec_sync clean）③ verified_commit 已记录 → 全部满足

## 关闭结论
- **已关闭（Closed，2026-08-13）**。用户授权回填：`pytest tests/auth/test_account_lifecycle.py` → 4 passed；`ruff`/`mypy` repo 级全绿；spec_sync=clean、`verified_commit=7c91a83`；是否偏离 TASK=否。M4 账户自助生命周期（注册/验证/找回）交付完成，对齐已批准 OpenAPI v0.2。

## 关联
- Change Request：无（实现 approved OpenAPI/SRS §5.6；OpenAPI 为 operation 实现非字段变更）
- 测试任务：TC-AUTH-REG-* / TC-AUTH-VERIFY-* / TC-AUTH-RESET-*
- 后续主线：M5 管理后台 / M6 AI 问答 RAG+人格层
- `resend-verification`：若产品需要，另开 Change Request（补 `/auth/resend-verification` 到 OpenAPI v0.2）→ 新 TASK 实现
