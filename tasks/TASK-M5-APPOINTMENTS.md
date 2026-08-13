# TASK-M5 管理后台（admin 操作域，无新迁移子集）

> 合并同域主线：管理后台必备的 owner_admin 管控操作归并为单一实现任务。
> **治理节奏（与 M1–M4 一致）**：① 合并同域主线；② 风险分级——force-cancel / availability override / company exception 涉及预约占用与 owner 意图真相源，属**高风险**，本任务**不单列独立 REVIEW 任务**（接手 Codex 模式），但实现须内联自审：RBAC owner_admin 强制、override 与 Slot 物化在同一事务、force-cancel 原子回滚占用；③ 交付证据一次写全；④ 验证批处理（一轮 pytest+ruff+mypy）。
> **DB 迁移铁律**：本任务**不得新建任何迁移/表/列/索引**——凡依赖缺失表的 admin operation 一律列为非目标，须先走独立迁移任务（人工审批）再另开实现任务。

## 任务类型
- implementation（admin 域管控）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）；development_gate 全放行
- 基线 commit：`7c91a83`（TASK-M4 关闭快照，HEAD）

## 精确规范引用（AI 只读取这些章节）
- OpenAPI v0.2 `docs/api/openapi.yaml` 已批准 admin operation（路径/operationId/状态码/字段严格对齐）：
  - `GET /admin/appointments` → `adminListAppointments`
  - `POST /admin/appointments/{appointment_id}/force-cancel` → `forceCancelAppointment`（204）
  - `GET /admin/availability-overrides` → `listAvailabilityOverrides`
  - `POST /admin/availability-overrides` → `createAvailabilityOverride`
  - `PUT /admin/availability-overrides/{override_id}` → `updateAvailabilityOverride`
  - `DELETE /admin/availability-overrides/{override_id}` → `deleteAvailabilityOverride`
  - `POST /admin/company-booking-exceptions` → `createCompanyBookingException`
- 安全设计 0.1：RBAC（`owner_admin` 角色强制）、审计（`audit_logs` 写入 admin 动作）、AES-256-GCM 字段解密（company_name 等密文在读路径窄化）
- 领域模型 v1.1.5 §6.5（Company）/ §6.9（AvailabilityOverride，owner 意图真相源）/ §6.17（CompanyBookingException，一次性例外授权）
- TC 见测试计划 v0.2 冻结 TC（admin 相关；若缺则按 AGENTS.md §7 先固定验收测试）

## 需求来源
- R9（owner_admin 后台管控预约）/ R10（owner 标红/覆盖可用性）/ R11（公司去重例外授权）/ UC-09..UC-12（后台操作）

## 目标
实现已批准 OpenAPI v0.2 中**依赖既有表、无需新迁移**的 7 个 admin operation：预约列表与强制取消、可用性覆盖 CRUD、公司预约例外创建。全部端点强制 `role=owner_admin` RBAC，admin 写操作落 `audit_logs`，availability override 变更在同一事务同步受影响 Slot 物化并触发 SSE。

## 非目标（明确排除，依赖缺失表，须先独立迁移任务）
- `PUT /admin/announcements/current`（`updateAnnouncement`）——缺 `page_announcements` 表
- `GET /admin/notification-deliveries`（`listNotificationFailures`）与 `POST .../resend`（`resendNotificationDelivery`）——缺 `notification_deliveries` 表（M3 已显式延后）
- `GET/POST /admin/knowledge-documents`、`DELETE /admin/knowledge-documents/{id}`（list/upload/delete）——缺 `knowledge_documents` / `knowledge_index_versions` 表，且属 M6 RAG 范畴
- 上述任一如需实现：先 Change Request（若契约需改）→ 独立迁移任务（人工审批建表）→ 另开实现任务。本任务不碰迁移、不碰加密策略、不碰 RAG 摄取。

## 允许修改路径
- `apps/api/app/admin/router.py`（新建：挂载 7 个 admin operation，统一 `owner_admin` 依赖注入）
- `apps/api/app/admin/service.py`（新建：admin 业务逻辑——列表/force-cancel/override CRUD/company exception）
- `apps/api/app/admin/repository.py`（新建：admin 查询与写操作，复用既有 `appointments`/`availability` SQL）
- `apps/api/app/admin/models.py`（新建：请求/响应 schema，对齐 OpenAPI `AvailabilityOverride`/`AvailabilityOverrideInput`/`CompanyBookingException` 命名与字段）
- `apps/api/app/admin/runtime.py`（新建：仅注入既有 repository/service，无新依赖）
- `apps/api/app/appointments/service.py`（扩展：`_force_cancel`、availability override 读/写/删、company_booking_exception 创建；复用现有事务与 `_decrypt_appointment`）
- `apps/api/app/appointments/repository.py`（扩展：admin 列表/override/exception 的 SQL，复用 `FOR UPDATE` 与现有索引）
- `apps/api/app/auth/*`（仅复用既有 RBAC 依赖注入，不改动鉴权主体）
- `apps/api/app/main.py`（仅挂载 admin router）
- `apps/api/tests/admin/test_admin_actions.py`（新建，真实 PG/Redis）
- `PROJECT_STATE.md`（仅当前任务段）

## 禁止修改路径
- `apps/api/migrations/**`（无 schema 变更；非目标项若被误触发立即 Stop & Report）
- `apps/api/app/appointments/crypto.py`（加密/密钥策略不变）
- 预约写路径的既有成功语义（preview/create/update/cancel/listMy 不得破坏）
- 登录/CSRF/限频主体

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无**（复用 `appointments`/`appointment_slots`/`availability_overrides`/`company_booking_exceptions`/`audit_logs`/`users` 既有表；列与约束见 migration 0001–0003 与领域模型 §6）
- API：**实现（非新增）`docs/api/openapi.yaml` 已批准的 7 个 admin operation**，路径/operationId/状态码严格对齐；语义实现 SRS/领域模型 §6.5/§6.9/§6.17。
- 依赖：**无新增**

## 规范影响评估（spec impact）
- behavior_change：true（新增 admin 用户可观察行为，但 operation 与 approved OpenAPI 完全一致，属"实现已批准契约"）
- affected_specs：
  - openapi：clean（7 个 operation 已定义；非目标 4 个 operation 不实现故不改契约）
  - srs：none
  - domain_model：none
  - security：none（沿用 RBAC/审计/AES）
  - test_plan：dirty（需补 admin TC，落 `test_admin_actions.py` 后转 clean）
- reason：实现 approved OpenAPI admin 子集；非目标项因缺表留待迁移任务，不改本契约。
- 分类：实现 approved 契约（operation 已存在，仅对齐实现）
- **执行顺序**：实现 + 真实 PG 测试通过 → 补 admin TC → spec_sync 转 clean → 关闭

## 功能验收
- `adminListAppointments`：返回预约列表（含 company_name 解密、状态、时间），仅 `owner_admin` 可见；分页/过滤对齐 OpenAPI。
- `forceCancelAppointment`：作废指定预约（置 `appointments.status=cancelled`）、释放并 `owner_lock` 其占用 Slot（与 M1 cancel 同语义，但由 owner 主动触发）、写 `audit_logs`；204；占用冲突经事务回滚。
- `listAvailabilityOverrides` / `createAvailabilityOverride` / `updateAvailabilityOverride` / `deleteAvailabilityOverride`：override 为 owner 意图真相源；**创建/修改/删除须在同一事务内同步受影响 `appointment_slots.status` 物化并触发 SSE**；不允许两个冲突 override 同时覆盖同一时段（领域模型 §6.9）；`CHECK(end_at > start_at)`。
- `createCompanyBookingException`：写 `company_booking_exceptions`（interviewer_user_id + company_fingerprint HMAC + approved_by=当前 owner_admin + reason + expires_at），写 `audit_logs`；重复/过期/已撤销校验对齐领域模型 §6.17。

## 安全与隐私验收
- 全部 7 端点强制 `role=owner_admin`（复用 auth RBAC 依赖，非 owner_admin → 403）
- admin 写操作落 `audit_logs`（actor/action/目标 id/时间）
- 密文列（company_name 等）在读路径 `cast(str, ...)` 窄化，零运行时变化
- 不泄露 interviewer 凭据；force-cancel 不绕过占用一致性

## 性能验收
- 列表走既有索引（`ix_appointments_*`）；override/exception 查询走 `ix_availability_overrides_created_by` / `ix_company_booking_exceptions_interviewer_user_id`
- override 事务内 Slot 物化范围限定受影响时段，不全表扫

## 变更预算（change_budget）
- max_files：12（含新建 admin 包 5 文件 + appointments 扩展 2 + main 挂载 1 + tests 1 + 本任务单 + PROJECT_STATE）
- expected_prod_lines：~320
- expected_test_lines：~220

## 必须运行的测试命令
- `pytest apps/api/tests/admin/test_admin_actions.py`（真实 PG/Redis，RBAC + force-cancel + override CRUD + exception）
- `ruff check .` + `mypy`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 出现未列明变更（新依赖/新迁移/改加密策略/改公开 API 字段语义/实现非目标 4 个 operation 中任一）→ 立即停止报告（非目标项须先 Change Request + 独立迁移任务）
- 超出 change_budget（max_files>12）→ 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`5245cfa`（M5 实现 + 契约偏离修正 + 证据回填；8 files / +1000）
- 修改文件清单：
  - `apps/api/app/admin/__init__.py`（新建，包标记）
  - `apps/api/app/admin/models.py`（新建，请求/响应 schema 严格对齐 OpenAPI `AvailabilityOverride`/`AvailabilityOverrideInput`/`CompanyBookingException`/`CompanyBookingExceptionInput`）
  - `apps/api/app/admin/router.py`（新建，7 operation 路由 + `owner_admin` RBAC + CSRF 拆分；**修正契约偏离**：`createCompanyBookingException` 原误加必填 `Idempotency-Key` 头，已删除以对齐 OpenAPI v0.2 该 operation 仅声明 `CsrfToken`）
  - `apps/api/app/appointments/service.py`（扩展 8 方法：`admin_list_appointments`/`force_cancel`/`list_overrides`/`create_override`/`update_override`/`delete_override`/`create_company_exception`/`_rematerialize_window`；复用引擎/解密/审计/释放）
  - `apps/api/app/factory.py`（扩展：挂载 `create_admin_router`）
  - `apps/api/tests/admin/test_admin_actions.py`（新建，真实 PG/Redis 集成测试 7 case）
- 测试命令及结果：
  - `ruff check .`：**All checks passed ✅**
  - `mypy`：**Success: no issues found in 29 source files ✅**
  - DB-free wiring smoke：BookingService 8 方法齐全、router 注册全部 7 operationId ✅
  - **真实 PG/Redis 集成测试 `pytest tests/admin/test_admin_actions.py`：BLOCKED ❌** ——本环境无 Docker（`docker`/`docker-compose` 二进制缺失）、无本地 PG/Redis（`127.0.0.1:55432` 与 `127.0.0.1:63790` 均 CLOSED），dev 栈（`docker-compose.dev.yml`）无法启动，集成测试无法执行。待用户在含 Docker 环境启动 dev 栈后复跑。
- lint / typecheck：ruff ✅ + mypy ✅（见上）
- DB 迁移验证：无 schema 变更（复用 `appointments`/`appointment_slots`/`availability_overrides`/`company_booking_exceptions`/`audit_logs`/`users` 既有表，未新建迁移/表/列/索引）✅
- 验收证据：DB-free wiring smoke 已验证路由注册与模型构建；RBAC/审计/物化逻辑经代码内联自审（owner_admin 强制、写操作落 audit_logs、override 与 Slot 物化同事务、force-cancel 占用 `owner_locked` 原子回滚、company exception 一次性 HMAC 去重 + 过期校验）；**真实 RBAC 403 / 审计落库 / 物化断言待集成测试执行**（env 阻塞）。
- 变更预算实际值：max_files 预算 12，实际 6 文件（admin 3 新建 + appointments/service 改 + factory 改 + test 新建）+ 本任务单 + PROJECT_STATE，未超预算 ✅
- 未解决风险：
  - ① 真实 PG/Redis 集成测试因本环境无 Docker 被阻塞，无 `verified_commit`，任务依关闭门禁不得标 Closed；
  - ② 非目标 4 operation（`updateAnnouncement` / `notification-deliveries` 增删 / `knowledge-documents` 增删）因缺表留待独立迁移任务（人工审批）；
  - ③ override–Slot 物化一致性需并发验证（集成测试覆盖单连接路径，缺并发竞争 case）；
  - ④ 【已修复】`createCompanyBookingException` 契约偏离：误加必填 `Idempotency-Key` 头已删除，现对齐 OpenAPI v0.2。
- 是否偏离 TASK：实现架构微调——admin 业务方法挂在 `BookingService`（复用引擎/解密/审计/释放逻辑），`admin/` 包仅含 `models.py`+`router.py`（未单列规划中的 `service.py`/`repository.py`/`runtime.py`）；属实现组织优化，功能与 OpenAPI 7 operation 完全对齐，未偏离范围/预算。非目标 4 operation 未实现（如实登记）。
- 规范影响结论：openapi clean（实现已批准 7 operation，未改契约，且已修正 createCompanyBookingException 偏离）；test_plan dirty（admin TC 已写 `test_admin_actions.py`，待真实测试通过转 clean）
- spec_sync：实现对齐 OpenAPI 后 clean（集成测试通过前维持 dirty→待 clean）
- verified_commit：**PENDING**（待集成测试在含 Docker 环境通过后再回填真实 sha）
- 关闭门禁：① 测试通过 ❌（env 阻塞）② 规范影响已处理（spec_sync clean）⏳ ③ verified_commit 已记录 ❌（pending）→ **当前不得关闭，待用户启动 dev 栈复跑测试并授权关闭**

## 关联
- 依赖独立迁移任务（待用户批准，非本任务）：`page_announcements`（公告）、`notification_deliveries`（通知重发，M3 延后）、`knowledge_documents`+`knowledge_index_versions`（知识库，M6）
- 后续主线：M6 AI 问答 RAG + 人格层（知识库摄取 + 检索 + 数字分身）
