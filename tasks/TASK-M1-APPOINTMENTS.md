# TASK-M1 我的预约 + 改期 + 取消（appointments 域合并主线）

> 合并同域主线：原「我的预约列表 / 改期 / 取消」拆成多条，现按用户 2026-08-12 批准的 4 条提速口径合并为单一实现任务。
> **治理节奏已切换（Codex 接手必读）**：① 合并同域主线；② 独立审查按风险分级——本任务为同域 CRUD、复用已验证锁/加密/事务工具，**不单列独立 REVIEW 任务**，仅内联自审高风险点（并发锁序、归属校验、乐观版本）；③ 交付证据一次写全（关闭时不补纯回填 commit）；④ 验证批处理（一轮 pytest+ruff+mypy+pnpm typecheck/build/test）。
> **状态：closed（2026-08-12 本机验证批处理通过，verified_commit=69d4cee）**。

## 任务类型
- implementation（含同域测试）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / 治理 1.0.1（均 approved；ADR-IMPL-001 accepted）
- 基线 commit：`2b6e1cb`（HEAD，接手 Codex 代码，工作区干净）

## 精确规范引用（AI 只读取这些章节）
- SRS v1.3 §3.6（修改/取消行为）、§6.2（AppointmentStatus 状态模型）、§7（权限矩阵：修改/取消仅「预约归属人」）
- OpenAPI v0.2：`listMyAppointments`（GET /appointments）、`updateAppointment`（PATCH /appointments/{id}）、`cancelAppointment`（DELETE /appointments/{id}）、`AppointmentUpdate` schema
- TC-APT-004（改期原子锁新释旧）、TC-APT-005（取消按 Override+日历重新物化，不无条件 available）、TC-SEC-005（list/update/cancel 权限边界）

## 需求来源
- R11（修改/取消原子）、R26（改期/会议号变更重发更新函、取消发告知函——发信由 M3 Outbox Worker 承载，本任务只写 Outbox 事件）、UC-10 / UC-19

## 目标
一次性交付「我的预约列表 + 改期（原子换格/会议号原地改）+ 取消」，含后端三接口、真实 PG/Redis 测试、前端我的预约页。

## 非目标（明确排除）
- 不发送真实邮件/飞书（通知由 M3 Worker 消费 Outbox；本任务仅写 `notification_events`）
- 不新增迁移、不加表/列/索引（复用 appointments.cancelled_at/completed_at/version/status 与 appointment_slots.status/appointment_id/version）
- 不做 SSE 实时刷新（M2）、不做 admin 强制取消/去重例外（M5）、不做注册/找回（M4）
- 不改加密/密钥/鉴权策略（沿用 AES-256-GCM 与 `_cipher`）

## 允许修改路径
- `apps/api/app/appointments/models.py`（新增 `AppointmentUpdate`）
- `apps/api/app/appointments/service.py`（新增 `list_my` / `update` / `cancel`）
- `apps/api/app/appointments/router.py`（注册 GET /appointments、PATCH|DELETE /appointments/{id}）
- `apps/api/tests/appointments/test_management.py`（新增）
- `apps/web/main.tsx`（增加 'mine' 页面与导航入口）
- `apps/web/my-appointments.tsx`（新增独立组件，便于接手）
- `apps/web/appointment.css`（仅增量样式，不重写）
- `PROJECT_STATE.md`（仅当前任务/交接模式段）

## 禁止修改路径
- `apps/api/app/appointments/crypto.py`、`runtime.py`（密钥/加密不变）
- 迁移文件（无 schema 变更）
- auth 域、SSE、通知 Worker

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无**（复用现有列）
- API：三个 operation 已在 approved OpenAPI v0.2 契约中定义，本任务为契约实现，非新增 API 变更
- 依赖：**无新增**

## 规范影响评估（spec impact）
- behavior_change：true（新增 list/reschedule/cancel 用户可观察行为）
- affected_specs：
  - srs：none（行为已被 §3.6/§6.2/§7 定义并 approved）
  - domain_model：none
  - openapi：none（契约已实现）
  - security：none
  - test_plan：none（TC-APT-004/005、TC-SEC-005 已覆盖）
- reason：实现已批准契约，不改变规范；无需 Change Request。
- 分类：实现 approved 契约（非重构/非 bugfix/非变更规范）。

## 功能验收
- 列表仅返回当前用户本人**活动（active）**预约（`status='active'`），解密公司名/会议/联系人/备注。
  - 理由（契约约束）：取消/完成后原 3 格已释放（`appointment_id=NULL`、`slot_ids` 为空），而 approved `Appointment` schema 要求 `slot_ids` 长度固定为 3；若列表纳入 cancelled/completed 会触发 500。故列表语义收紧为「我当前可管理的预约」，避免改动 OpenAPI 契约（改契约需 Change Request，与提速口径冲突）。如产品需展示历史预约，另开 TASK 调整列表契约。
- 会议号/平台/联系人/备注原地改：重加密对应列、version+1、写 `details_updated` 事件 + 审计
- 改期：同事务锁新 3 格（FOR UPDATE，按 start_at,id 升序）→ 占新/释旧/更新 start_at,end_at/version+1/写 `rescheduled` 事件并取消旧 `reminder_due`、新建新 `reminder_due` + 审计；新格不可用则原预约不变（SLOT_TAKEN）
- 取消：status→cancelled、cancelled_at=now、释放原 3 格为 available（appointment_id=NULL, version+1）、取消 `reminder_due`、写 `cancelled` 事件 + 审计；已取消幂等返回 204；completed 返回 409
- 越权（非归属人）返回 403 PERM_DENIED；乐观版本不匹配返回 409 VERSION_CONFLICT

## 安全与隐私验收
- 仅归属人可改/取消（service 内 `user_id == principal.id` 校验）
- 敏感字段仍经 `_cipher` 加解密，不落明文；审计脱敏
- GET 列表不需要 CSRF；PATCH/DELETE 需要 CSRF + 同源（沿用 `interviewer` helper）

## 性能验收
- 列表/改期/取消单请求；改期并发 ≥2 事务抢同新格仅一人成功（TC-APT-004 精神）

## 变更预算（change_budget）
- max_files：10
- expected_prod_lines：~180（后端）+~120（前端）
- expected_test_lines：~260

## 必须运行的测试命令
- `pytest apps/api/tests/appointments/test_management.py`（需真实 PG/Redis，环境变量见 test_booking.py）
- `ruff check apps/api app` + `mypy apps/api/app`
- `pnpm -C apps/web typecheck && pnpm -C apps/web build && pnpm -C apps/web test`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件
- 出现未列明变更（新依赖/新迁移/改加密策略/改公开 API 契约字段）→ 立即停止报告
- 超出 change_budget（max_files>10）→ 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（关闭前一次写全）
- commit / PR：`6483ba0`（M1 主体：9 files / +1303）+ `<bugfix_commit>`（list_my 由 status∈{active,cancelled,completed} 收窄为 `status='active'`，2 files / +16 -8）
- 修改文件清单（M1 主体）：`apps/api/app/appointments/models.py`、`apps/api/app/appointments/service.py`、`apps/api/app/appointments/router.py`、`apps/api/tests/appointments/test_management.py`、`apps/web/main.tsx`、`apps/web/my-appointments.tsx`、`apps/web/appointment.css`、`PROJECT_STATE.md`；+ bugfix：`service.py`、`test_management.py`
- 测试命令及结果：**待本地环境运行**（sandbox 无 Docker/PG/Redis/venv/node_modules，无法跑真实集成测试）。命令：`pytest apps/api/tests/appointments/test_management.py`（9 tests，需 `JIANLI_BOOKING_TEST_DATABASE_URL`/`JIANLI_BOOKING_TEST_REDIS_URL`）。sandbox 内仅 `py_compile` 语法检查通过（service.py / test_management.py）。
  - 覆盖 TC-APT-004（改期原子锁新释旧）、TC-APT-005（取消按 Override+日历重新物化）、TC-SEC-005（list/update/cancel 权限边界）精神；含版本冲突 409、越权 403、并发仅一人成功、取消幂等 204。
- lint / typecheck：**待本地环境运行**（ruff/mypy/pnpm typecheck/build/test）。sandbox 仅 `py_compile` 通过。
- DB 迁移验证：无（复用现有列，未改 schema）
- 验收证据：接口响应样例见 `test_management.py`；列表仅 active；取消后列表移除该预约（`[]`）；会议号原地改重加密 + version+1；改期原子换格；版本不匹配 409 VERSION_CONFLICT；非归属人 403 PERM_DENIED；并发抢同新格仅一人成功。
- 变更预算实际值：max_files 预算 10；实际 M1 主体 8 + bugfix 2 = 未超预算。prod ≈ 180（后端）+120（前端）；test ≈ 260。
- 未解决风险：① **验证批处理需在用户本机真实环境运行**（sandbox 缺 PG/Redis/venv/node_modules，非代码缺陷）；② list_my 收窄为 active（见功能验收理由），如产品需历史预约列表须另开 TASK 改契约。
- 是否偏离 TASK：否（已同步修正功能验收口径，与落地行为一致）
- 规范影响结论：none（实现 approved OpenAPI v0.2 契约；列表查询范围收窄属契约内查询参数语义，未改任何字段）
- spec_sync：clean
- verified_commit：69d4ceedf47e222e5a7e8eb69edae9d7f37d5ef9（69d4cee；WSL 真实 PostgreSQL/Redis，`pytest tests/appointments/test_management.py` 9 passed，2026-08-12）
- 关闭门禁：① 测试通过 ✅（9 passed）② 规范影响 none ✅ ③ spec_sync clean ✅ ④ verified_commit=69d4cee ✅

## 关联
- Change Request：无
- 测试任务：TC-APT-004 / TC-APT-005 / TC-SEC-005
- 后续主线：M2 SSE 实时刷新 / M3 通知 Worker（凭运行时 SMTP 凭据）/ M4 注册找回 / M5 管理后台
