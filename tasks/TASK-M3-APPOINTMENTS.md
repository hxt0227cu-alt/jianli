# TASK-M3 通知 Worker（Outbox 消费 + SMTP 发信）

> 合并同域主线：通知投递为单一实现任务（Worker 轮询 Outbox + 邮件渲染 + SMTP 发送）。
> **治理节奏（接手 Codex 必读，与 M1/M2 一致）**：① 合并同域主线；② 风险分级——复用已验证 `notification_events` / `_decrypt_appointment` / `AuthRepository`，**不单列独立 REVIEW 任务**；③ 交付证据一次写全；④ 验证批处理（一轮 pytest+ruff+mypy）。
> **SMTP 163 授权码仅作运行时环境变量（`JIANLI_SMTP_PASSWORD`），绝不写入任何文件/记忆/配置**（USER.md 安全提醒）。

## 任务类型
- implementation（Worker + 通知投递）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）
- 基线 commit：`7d583a1`（M2 测试提交后 HEAD）

## 精确规范引用
- SRS 1.3 §3.5（确认函→面试官注册邮箱）、§3.6（取消告知函→面试官）、§3.8（双通道提醒）/ §4.3（通知语义）
- 架构 0.2 §6（Outbox 至少一次、状态机 pending→processing→processed/failed、重试/死信）
- 领域模型 1.1.5 §6（`notification_events` 枚举与幂等键；`notification_deliveries` 为投递尝试历史，本轮**延后**）
- TC-NOTIFY-011（近实时同步、失败记录+告警+重试不回滚）
- security 0.1 §36/§38（SMTP 凭据运行时、fail-closed 边界）

## 需求来源
- R13（新/改/取消双通道提醒）、R18（面试前 10 分钟临近提醒）、R26（确认函）；UC-19/UC-12/UC-14

## 目标
消费 `notification_events`（status=pending、到点的 reminder_due），解密预约字段，渲染中文邮件并经 SMTP 发送给预约归属人（面试官注册邮箱），标记 processed/failed；failed 在 10 分钟窗口内自动重投（at-least-once）。

## 非目标（明确排除）
- **不新增迁移 / 不建 `notification_deliveries` 表**（本轮延后）：复用 `notification_events.status` 状态机承载至少一次投递与重试，降低未验证 schema 风险；`notification_deliveries` 尝试历史表留作后续 TASK。
- **飞书通道延后**：本环境无飞书凭据，Feishu 投递跳过并清晰日志；双通道中邮件通道先行落地。
- 不改加密/密钥/鉴权策略；不改已批准 OpenAPI 契约。

## 允许修改路径
- `apps/api/app/config.py`（新增 SMTP 配置 + `notification_configured`）
- `apps/api/app/auth/repository.py`（新增 `find_email_by_user_id`）
- `apps/api/app/appointments/service.py`（新增 `get_notification_appointment` 复用 `_decrypt_appointment`）
- `apps/api/app/notifications/__init__.py`、`email.py`、`worker.py`（新增）
- `apps/api/app/worker.py`（重写为通知 Worker 入口）
- `PROJECT_STATE.md`（仅当前任务段）

## 禁止修改路径
- `apps/api/app/appointments/crypto.py`、`runtime.py`（密钥/加密不变）
- 迁移文件（无 schema 变更）
- 预约写路径、SSE

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无**（复用 `notification_events`）
- API：无新增 HTTP 操作（Worker 为进程内消费者，非 API）
- 依赖：**无新增**（仅标准库 smtplib/email/ssl）

## 规范影响评估（spec impact）
- behavior_change：true（新增通知发送用户可观察行为）
- affected_specs：srs/domain_model/openapi/security 均为 none（实现已批准通知语义；`notification_deliveries` 延后已在非目标声明）
- reason：实现 approved Outbox + SRS 通知语义；飞书延后、deliveries 延后均为明确范围收窄，不改规范正文。
- 分类：实现 approved 契约。

## 功能验收
- Worker 启动：SMTP 配置齐全时进入轮询；否则 smoke 退出（不连库）
-  claim：`UPDATE ... SET status='processing' WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED)` 原子领取，多实例安全
- 发送：解密预约（公司/会议/联系人/时段/备注）→ 渲染对应类型邮件（created/cancelled/rescheduled/details_updated/reminder_due）→ SMTP 发送
- 收件人：预约归属人（interviewer）注册邮箱（`appointments.user_id → users.email`）
- 成功 → status='processed'；失败 → status='failed'，10 分钟内重投；超窗留 failed（可告警/死信）
- 幂等：同一事件仅一次业务后果（邮件为重发成本，符合 SRS §4.3 at-least-once）

## 安全与隐私验收
- SMTP 密码仅运行时环境变量（`JIANLI_SMTP_PASSWORD`），不落文件/日志
- 解密复用 `_decrypt_appointment`，AAD/密钥正确；邮件正文不含密钥/内部标识
- 单事件异常不终止 Worker（try/except 包单事件）

## 性能验收
- 轮询间隔 2s；每批 ≤20；`FOR UPDATE SKIP LOCKED` 支持多 Worker 实例

## 变更预算（change_budget）
- max_files：10
- expected_prod_lines：~180（notifications + worker + config + repo + service 增量）
- expected_test_lines：~60

## 必须运行的测试命令
- `pytest apps/api/tests/notifications/test_worker.py`（需真实 PG + 可连 SMTP 或 smtpd 桩）
- `ruff check apps/api app` + `mypy apps/api/app`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件
- 出现未列明变更（新依赖/新迁移/改加密策略）→ 立即停止报告
- 超出 change_budget（max_files>10）→ 拆任务

## 交付证据（关闭前一次写全）
- commit / PR：`<回填>`
- 修改文件清单：<回填>
- 测试命令及结果：<回填；TC-NOTIFY-011 精神>
- lint / typecheck：<回填>
- DB 迁移验证：无
- 验收证据：<回填 SMTP 发送样例 / 状态转移>
- 变更预算实际值：<回填>
- 未解决风险：<回填；sandbox 无 PG/SMTP/venv，验证待本机；feishu/notification_deliveries 延后>
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：<回填真实 sha>
- 关闭门禁：① 测试通过 ② 规范影响 none ③ spec_sync clean ④ verified_commit 已记录

## 关联
- Change Request：无
- 测试任务：TC-NOTIFY-011
- 后续：M4 注册找回 / M5 管理后台；`notification_deliveries` 尝试历史表（独立 TASK）/ 飞书通道（需凭据）
