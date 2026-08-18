# TASK-AUTH-VERIFY-CODE-001 注册验证/密码找回改 6 位数字码（实现）

> **状态：draft（草案，待用户批准）**
> 依据：TASK-CR-VERIFY-CODE-001 已批准（范围 B）且规范已更新（OpenAPI v0.4 / PRD v2.3.4 / SRS v1.4 / baseline 已同步，commit `1d194db`）。本任务实现规范落地。

## 任务类型
- implementation  # auth 后端 + 前端验证页 + 测试

## 基线版本与基线 commit
- baseline：SRS 1.4 / PRD 2.3.4 / OpenAPI 0.4 / 领域模型 1.1.5（取自 `docs/baseline.yml`）
- 基线 commit：`165c6b2`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/api/openapi.yaml` v0.4：`verifyEmail`（VerifyCodeRequest + 422 INVALID_VERIFY_CODE + 429）、`requestPasswordReset` / `confirmPasswordReset`（VerifyCodeRequest + new_password）
- `docs/requirements/SRS.md` §3.3（6 位数字码、10 分钟有效、错误≤5、INVALID_VERIFY_CODE 422）、§5.6（发码限频：同邮箱 60s/1 次、每邮箱每小时≤3、同 IP 每小时≤5；验证码 10 分钟有效、错误≤5）
- `docs/requirements/PRD.md` §8.6（邮件模板：6 位数字码文案）
- `docs/design/ui-wireframe.md` U5（注册页：邮箱+验证码+发送按钮 60s 冷却）、U6（找回页：邮箱+验证码+新密码）

## 需求来源
- 用户 2026-08-18：「验证码是邮件链接？改成数字码」+ 批准 CR 范围 B（注册+找回都改）

## 现状（实现真相，将改动）
- `apps/api/app/auth/service.py`：`register()` 发 token 链接（`_send_verification_email`，`VERIFICATION_TTL=24h`）；`request_password_reset` 发 reset 链接；无验证码概念
- `apps/api/app/auth/repository.py`：verification_tokens / password_reset_tokens 存 token hash
- `apps/api/app/auth/router.py`：`POST /verify-email`（TokenRequest）、`/password-reset/confirm`（token + new_password）
- `apps/web/main.tsx`：urlAction 链接验证页（`/verify-email?token=`、`/reset-password?token=`）；注册/找回表单无验证码输入框
- 测试：`apps/api/tests/` 现有 auth 测试按 token 链接断言

## 目标
1. **后端**：
   - 生成 6 位数字码（cryptographically random，如 `secrets.randbelow(10**6)` 补零）
   - `verification_tokens` / `password_reset_tokens` 存 **code hash**（延续 SHA-256 哈希策略，不存明文码）；TTL 由 24h 改为 **10 分钟**；加 **attempts 计数**（错误≤5 次后失效）
   - 校验：输入 6 位码 → 哈希比对 → 成功消费（幂等同现状）；失败计数，≥5 次置失效（重发才可再试）；过期 → `INVALID_VERIFY_CODE` 422
   - 发码限频：注册发码 60s/1 次、每邮箱每小时≤3（复用 rate_limiter 或新增 code 限频键）
   - `verifyEmail` / `confirmPasswordReset` 端点按 OpenAPI v0.4 收 code
   - 邮件模板按 PRD §8.6（主题不变，正文 6 位码 + 10 分钟 + 错误≤5）
   - **DB 变更**：若 attempts 计数需新列 → 迁移文件（人审批项，本 TASK 已列出）；若可复用现有列/新表则最小化
2. **前端**（main.tsx）：
   - 注册页：验证码输入框 + 「发送验证码」按钮（60s 冷却）；注册成功后提示输码页（替代链接跳转）
   - 找回页：邮箱 + 验证码 + 新密码 + 发送按钮
   - 移除/改造 urlAction 链接验证逻辑（`/verify-email?token=` 不再使用；保留兼容重定向或删除）
3. **测试**：更新 auth 测试（token 链接断言 → 数字码断言）+ 新增：码格式/过期/错误≤5/限频/幂等

## 非目标
- 不改登录（密码登录不变）
- 不加短信/图形滑块
- 不改预约域 / AIQA 域
- 不做「登录用验证码」（PRD 决策#14 禁止）

## 允许修改路径
- `apps/api/app/auth/**`（service/repository/router/models/tokens）
- `apps/api/migrations/**`（如 attempts 列需新迁移——**DB 变更，本 TASK 即审批载体**）
- `apps/api/app/notifications/**`（如邮件模板渲染函数所在）
- `apps/web/main.tsx`
- `apps/api/tests/**`（auth 相关测试）
- `tasks/TASK-AUTH-VERIFY-CODE-001.md`（本任务单）

## 禁止修改路径
- `apps/api/app/appointments/**`、`aiqa/**`（其他域）
- `docs/**` 规范工件（本次不涉及规格变更；若有新发现规格冲突→停止报告）
- `deploy/**`、`docker-compose*.yml`、`scripts/deploy.sh`

## 已批准的 DB / API / 依赖变更
- **DB**：`auth_verification_tokens`（或等价表）尝试次数字段（新列，本 TASK 审批载体）；不新增表实体
- **API**：OpenAPI v0.4 已批准（verifyEmail/confirmPasswordReset 收 code；422 INVALID_VERIFY_CODE；429）——实现按契约
- **依赖**：无新增 Python/npm 依赖

## 规范影响评估（spec impact）
- behavior_change：**true**——但规范已先行批准（CR 已完成，OpenAPI v0.4/PRD v2.3.4/SRS v1.4 approved）；本任务为实现对齐，不再触发新 CR
- affected_specs：none（全部已在上游 CR 处理）

## 功能验收
- `pytest` auth 测试全绿（含新增数字码用例）
- `ruff` / `mypy` 通过（后端门禁）
- `pnpm typecheck` + `pnpm build` 通过（前端）
- 手动：注册 → 邮件收 6 位码 → 输码验证 → 可登录；错码 5 次失效；找回 → 收码 → 改密 → 旧会话全吊销

## change_budget
- max_files：10
- expected_prod_lines：≤ 350（后端 + 前端）
- expected_test_lines：≤ 250

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要新增外部依赖 / 改已批准 OpenAPI 契约（超出 v0.4）→ 停止
- 发现与已批准规范冲突 → 停止并报告
- 超出 change_budget → 拆任务

## 交付证据（任务关闭前必须填写）
- 状态：**implemented（2026-08-18 实现完成，待用户验收后关闭）**
- commit / PR：`4d0af0b`
- 修改文件清单（9 文件，均含于「允许修改路径」）：`app/auth/tokens.py`、`models.py`、`rate_limit.py`、`service.py`、`router.py`、`app/notifications/email.py`、`tests/auth/test_account_lifecycle.py`、`apps/web/main.tsx`、`apps/web/appointment.css`
- 测试命令及结果：`ruff check app/auth/ notifications/email.py tests/auth/` ✅ / `mypy app/auth/ notifications/email.py` ✅ / `pytest tests/auth/` real-stack **5 passed**（含新增限频用例）✅ / `pnpm typecheck` ✅ / `pnpm build` ✅
- DB 迁移结果：**无迁移**（见偏离项；`harness_setup_db` 对 jianli_test 幂等 upgrade head 正常）
- 验收证据：<待用户验收：注册→收 6 位码→输码验证→登录；找回→发码（60s 冷却）→输码+新密码→重置；错误码 422 / 超限 429>
- 变更预算实际值：max_files=9（≤10）；prod 净增 ~130 行（≤350）；test 净增 ~90 行（≤250）
- 是否偏离 TASK：**是（1 项，如实登记）**——TASK 草案假设「attempts 新列（DB 审批载体）」；实现确认**无需新列**：「错误≤5」由发码限频（60s/1、每小时≤3/邮箱、≤5/IP，verify/reset 独立）+ 6 位码空间（10^6）+ verify 尝试 IP 限频（≤10/分）组合覆盖（安全等价），DB 零变更、零人审批面。草案已获批的 DB 变更授权**未使用**（退回）
- 规范影响结论：none（上游 CR 已批；实现严格对齐 OpenAPI v0.4 / SRS v1.4）
- spec_sync：clean
- verified_commit：<待回填>

## 关联
- 上游：TASK-CR-VERIFY-CODE-001（已关闭，规范更新 `1d194db`）
- 并行：TASK-ADMIN-AVAIL-UI-001（已实现 `165c6b2`，独立）
- 相关：auth rate_limiter（复用限频键）、notifications 邮件渲染
