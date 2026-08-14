# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（**SRS v1.1 / approved**（v1.0 于 `26ae844` 批准、v1.1 退信(Bounce) 缺陷修正于 `00e125c` 批准；TASK-SRS-002 已关闭、TASK-UI-002 已同步退信并关闭、SRS 现为行为唯一源）；domain_model **v1.1.5 / approved**（TASK-DM-003 已关闭、下游 SRS/架构已同步）；TASK-DM-001 历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点、v1.1.4 批准锚点 `f537296` 保留为历史；**UI 线框 v1.0 / approved**（经用户 2026-08-08 独立评审批准，approval_commit=`38b102a`；TASK-UI-002/TASK-UI-003 均已闭合、TASK-UI-001 已关闭）；现进入架构/ADR 阶段）

> ### 交接模式（2026-08-12 切换 — Codex / 下一 AI 接手必读）
> - **治理节奏已切换为功能交付优先**：用户批准 4 条提速口径 —— ① 合并同域主线；② 独立审查按风险分级（同域 CRUD 不单列 REVIEW 任务，仅内联自审并发/归属/乐观版本）；③ 交付证据一次写全（关闭时不补纯回填 commit）；④ 验证批处理（一轮 pytest+ruff+mypy+pnpm typecheck/build/test）。
> - **仓库可被任意 AI 直接接手**：对齐锚点 = `AGENTS.md` + `docs/baseline.yml` + `PROJECT_STATE.md`（本文件）+ `tasks/TASK-*.md` + Git 历史；不依赖对话记忆。工作区须干净（无未提交改动）。
> - **SMTP 163 授权码已提供**：仅运行时环境变量使用，**绝不写入任何文档/配置/记忆文件**（见「本周阻塞」）。M3 通知 Worker 凭运行时凭据一次做通；未提供时先实现本地 sink 版（真实 Outbox 消费、不真发信）。
> - **未变铁律**：MVP 硬规则、冻结 TC 断言、DB 迁移人审批、加密/鉴权策略、`.workbuddy/` 不入库。

---

## 当前阶段

编码准入已开放；前端展示壳与 FastAPI 后端骨架已交付，后续实现仍受独立审查、冻结 TC 与人工审批边界约束。

- **领域模型 v1.1.5 / status=approved**（TASK-DM-003 已关闭，2026-08-08 末用户批准，独立批准锚点 `f412c7d`）：已完成 SRS、UI、architecture 下游同步；architecture v0.2 当前已 approved，正文 based_on 已同步 SRS v1.2。
- **SRS v1.2 / status=approved**（v1.1 历史快照 `00e125c` 保留；v1.2 用户于 2026-08-10 批准，独立批准锚点 `ab4b94e`）：统一 `AUTH_EXPIRED`/`RATE_LIMITED` 语义并正式定义 `OVERRIDE_NOT_FOUND`/`OVERRIDE_RANGE_EMPTY`；SRS 仍为行为唯一源，`based_on` 与 domain-model v1.1.5 对齐。
- **UI 线框 v1.0（TASK-UI-001 / ui-wireframe.md）**：UI 线框 v1.0 经用户 2026-08-08 独立评审批准（approval_commit=`38b102a`，baseline.status=`approved`）；影响评审（TASK-UI-IMPACT-001）结论=基本可沿用 + 1 处缺口；内容缺口由 TASK-UI-002 执行并闭合（A6/A7 失败三态 + 退信），8 项后续内容修正由 **TASK-UI-003** 一次性修正并闭合（对齐 SRS v1.1、消除误导实现表述）；TASK-UI-001 已关闭。下游进入架构/ADR 阶段。
- **架构设计 v0.2 已批准**：内容快照=`3a18b7f`，approval_commit=`da3f6fc`；TASK-ARCH-001/002/003 与 TASK-ARCH-IMPACT-001 已收口，正文已同步 SRS v1.2。
- **安全设计 v0.1 已批准**（TASK-SEC-001 已关闭）：SRS v1.2 impact-sync=`151509f`，approval_commit=`c2f08f2`，BCrypt/会话/Redis 限频/IMAP 退信/AES-256-GCM/RBAC/LLM 与上传边界开始约束下游实现。
- **OpenAPI/SSE v0.1 已批准**（TASK-API-001 已关闭）：安全契约修正快照=`fd9747c`，approval_commit=`2c8cede`；显式 401/403、CSRF、匿名/登录 AI SSE 分支与密码 UTF-8 字节语义已通过 Redocly 0 error / 0 warning。
- **测试计划 v0.1 已批准**（TASK-TEST-001 已关闭）：冻结 TC 快照=`204c2b8`，impact-sync=`c4e76f4`，approval_commit=`60b56b2`；69 个 TC 覆盖 R1-R26 与 33 个 operationId，断言与真实依赖级别不得由实现任务降低。

---

## 当前任务

- **TASK-DM-001**：历史**已关闭**（对应 domain_model v1.1.3，批准锚点 `f64b6de`）。不重开；其成果由 v1.1.4 取代。
- **TASK-DM-002**：**已关闭（Closed，2026-08-08）**——领域模型 v1.1.3→v1.1.4 密码算法中性化修正。关闭门禁按 `tasks/TASK-TEMPLATE.md` 四条件执行（`spec_sync=dirty` 不得关闭，现已满足并关闭）。
  - **执行顺序（2026-08-08 第三轮修正并已执行完毕）**：① 用户批准 v1.1.4 → 生成**独立批准锚点** `f537296`（不得复用 `f64b6de`）；② **先**由 TASK-SRS-001 执行 SRS impact review 并将其 `spec_sync` 转 clean（`d166992`）；③ **然后**本任务 `spec_sync` 由 dirty 转 clean，补齐 `verified_commit`/验证结果/关闭结论后**关闭**（本任务关闭提交）。
  - **不构成本任务关闭条件（已验证）**：SRS 自身获得 `approved` 不构成本任务关闭条件——TASK-DM-002 关闭当时 SRS 仍为 review（现已于 26ae844 approved），本任务已关闭即证明二者解耦。
- **TASK-SRS-001**：**已关闭（Closed，2026-08-08）**——SRS v1.0 生成 + impact review（domain_model 1.1.3→1.1.4 文字同步）+ 本次 SRS 批准收口。`approval_commit=26ae844`（SRS 批准单一用途锚点），`verified_commit=06798a2`（SRS 关闭快照）。`spec_sync=clean`；SRS 现已 approved。
- **TASK-UI-001**：**已关闭（Closed，2026-08-08）**——UI 线框 v1.0 产出（U1–U12 + A1–A8，与 SRS §3.1–§3.9 映射）；approval_commit=`38b102a`（UI v1.0 批准锚点）；verified_commit=`c0f5829`（UI 内容最终交付快照，含 TASK-UI-002/TASK-UI-003 修正）；spec_sync=clean。`baseline.ui_wireframe.status`=`approved`。
- **TASK-UI-IMPACT-001**：**已关闭（Closed，2026-08-08）**——UI 线框影响评审，结论=基本可沿用（SRS `26ae844` + 领域模型 1.1.4 与现有线框对齐；仅 A6 通知失败中心 `DeliveryStatus` 枚举轻微缺口）→ 内容缺口由 **TASK-UI-002** 承载；未批准 ui_wireframe、未改 baseline 状态、未推进架构。
- **TASK-UI-002**：**已关闭（Closed，2026-08-08）**——UI 线框内容修正（A6/A7 通知失败中心失败处理态 failed/retry_scheduled/dead_letter 补全 + 吸收 SRS v1.1 退信：退信记录 bounced_at/bounce_reason 展示、按通道与状态筛选、退信告警状态、手动重发新建 NotificationDelivery 尝试）。依据已批准 SRS v1.1 §6.2/§4.3/§3.8/§3.9；verified_commit=`266a773`；`baseline.ui_wireframe.status` 保持 pending，待用户评审实际线框后授权批准。
- **TASK-UI-003**：**已关闭（Closed，2026-08-08）**——UI 线框 8 处内容修正（消除误导实现表述，对齐 SRS v1.1）：A6 筛选拆分（投递态 failed/retry_scheduled/dead_letter / 退信 全部·是·否）、U9 两类通知分述（确认函→面试官注册邮箱 / 新事件→飞书+邮箱提醒候选人）、U3 周一–周日 7 独立列、红图例"已预约/不可约"、U3 交互冲突校验后直接弹 U7、U4 AUTH_EXPIRED 仅会话过期、U5 单次邮箱验证、文档顶部统一 SRS v1.1 并标注退信缺口闭合。依据已批准 SRS v1.1（§3.3/§3.4/§3.5/§3.8/§6.2/§8）；verified_commit=`c0f5829`；`baseline.ui_wireframe.status` 保持 pending，待用户评审实际线框后授权批准。
- **TASK-SRS-002**：**已关闭（Closed，2026-08-08）**——SRS 退信(Bounce) 行为缺陷修正（v1.0 → v1.1）；补充 PRD §4.6/R26 与 UC-21 已要求但 v1.0 遗漏的退信记录/展示筛选/告警/手动重发/不回滚预约；domain_model 无需改（bounce 字段已在 v1.1.4 §5）；approval_commit=`00e125c`（SRS v1.1 批准锚点）；verified_commit=`b38febd`（下游 UI 同步验证快照）；spec_sync=clean。SRS v1.1 现已 approved。
- **TASK-ARCH-001 / TASK-ARCH-002**：**已关闭（Closed，2026-08-09）**——architecture v0.2 内容快照=`3a18b7f`，approval_commit=`da3f6fc`，spec_sync=clean。
- **TASK-ARCH-003**：**已关闭（Closed，2026-08-09）**——承载用户明确批准后的单一用途状态推进与架构阶段收口。
- **TASK-SEC-001**：**已关闭（Closed，2026-08-10）**——security v0.1 impact-sync + 用户批准；approval_commit=`c2f08f2`，verified_commit=`010e3e1`，spec_sync=clean。
- **TASK-CONTENT-001**：**已关闭（Closed，2026-08-09）**——页面二两项目内容基线已完成；sleep202603-an 严格只读，证据按本地/模拟/未验证分级；verified_commit=`a09fa5d`。
- **TASK-SRS-003**：**已关闭（Closed，2026-08-10）**——SRS v1.2 错误语义收口并获用户批准，approval_commit=`ab4b94e`，verified_commit=`1c443eb`，spec_sync=clean。
- **TASK-API-001**：**已关闭（Closed，2026-08-10）**——SRS v1.2/security v0.1 impact review 完成，spec_sync=clean，approval_commit=`2c8cede`，verified_commit=`3e2b58b`。
- **TASK-TEST-001**：**已关闭（Closed，2026-08-10）**——上游 impact review 完成，spec_sync=clean，approval_commit=`60b56b2`，verified_commit=`ebe6c1a`；实际测试代码由下游测试任务实现。
- **TASK-ADR-001**：**已关闭（Closed，2026-08-10）**——ADR-IMPL-001 已由用户接受（`accepted`），唯一推荐栈开始约束 implementation TASK；verified_commit=`99678dc`；未安装依赖、未写代码。
- **TASK-READY-001**：**已关闭（Closed / PASS，2026-08-10）**——十项 baseline 工件均 approved，ADR-IMPL-001 已 accepted；WEB-001 实现任务与独立 REVIEW-WEB-001 已建立。
- **TASK-IMPL-WEB-001**：**Open**——首个实现任务，仅负责前端展示壳、页面一/二和静态导航；不含后端、鉴权、迁移、通知或基础设施。
- **TASK-REVIEW-WEB-001**：**Open**——独立审查 WEB-001 的越界、隐私、冻结 TC 和证据真实性。
- **TASK-BE-001**：**已关闭（Closed，2026-08-11）**——FastAPI 应用工厂、环境配置、结构化日志、API/Worker 独立入口与 Python 工程门禁已交付；verified_commit=`de91826`；无业务路由、数据库、鉴权、加密、通知或 LLM。
- **TASK-REVIEW-BE-001**：**已关闭（Closed，2026-08-11）**——首轮 Ruff/锁文件/API 入口测试阻塞已向前修正；最终 pytest 5 passed、Ruff/mypy/真实 API 与 Worker smoke 全通过，无 P0/P1 遗留。
- **TASK-DB-001**：**已关闭（Closed，2026-08-11）**——保留原实现快照 `da8dc7f`；最终验证快照 `2179821` 经独立审查无 P1/P2，PostgreSQL 17.6 一次性空库 TC-OPS-002 为 10 passed / 0 skipped，真实 `up/down/up`、schema/约束/重复升级与静态门禁全部通过；未执行生产迁移。
- **TASK-INFRA-LOCAL-001**：**已关闭（Closed，2026-08-11）**——本机临时 PostgreSQL 验收环境已停止并完全删除，进程/监听为 0，下载、解压、venv、口令和 data 均无残留。
- **TASK-AUTH-001 / TASK-AUTH-002**：**Closed（2026-08-11）**——登录、PostgreSQL 会话、CSRF/同源防护、Redis 登录限频、RBAC 核心及独立审查修正已收口；最终验证快照=`b8c7fc5`，注册验证/密码找回邮件未并入本任务。
- **TASK-AUTH-CONTRACT-001**：**Closed（2026-08-11）**——用户批准的 `INVALID_CREDENTIALS`（401）与 `INVALID_REQUEST`（422 Problem）已同步 SRS/OpenAPI/测试计划；approval/verified snapshot=`71d7861`，AUTH 实现阻塞已解除。
- **TASK-AUTH-003 / TASK-REVIEW-AUTH-002**：**Closed（2026-08-11）**——已批准认证错误契约实现于 `b8c7fc5`；独立审查 P0=0、P1=0，真实 PostgreSQL/Redis AUTH 15 passed / 0 skipped、全套 27 passed / 0 skipped。
- **TASK-REVIEW-AUTH-001**：**Closed（2026-08-11）**——AUTH-001 独立安全与实现审查已收口；原问题经 TASK-AUTH-002、TASK-AUTH-CONTRACT-001、TASK-AUTH-003 向前修正，审查角色未修改实现。
- **TASK-DB-002 / TASK-REVIEW-DB-002**：**Closed（2026-08-11）**——最终验证快照 `2fd1199`；五表/三 enum/approved 约束可逆迁移通过，真实 PostgreSQL migration 测试 22 passed / 0 skipped，独立审查 P0/P1/P2=0；未执行生产迁移。
- **TASK-TEST-MIGRATION-001**：**Closed（2026-08-11）**——获批的身份域表集合子集断言已兼容合法后续 migration，其余身份域精确 schema/约束断言保持冻结。
- **TASK-TEST-DB-002-CONSTRAINTS / TASK-TEST-DB-002-REFERENTIAL**：**Closed（2026-08-11）**——按预算拆分的 UNIQUE/CHECK 与 enum/FK 真实数据库拒绝路径全部通过，分别为 188/190 与 90/90 测试行。
- **TASK-DB-003 / TASK-REVIEW-DB-003**：**Closed（2026-08-11）**——最终验证快照 `4f3b74c`；两表/两 enum/approved 约束可逆迁移通过，同一真实 PostgreSQL 连续两遍 migration 测试均 26 passed / 0 skipped，独立审查 P0/P1/P2=0；未执行生产迁移。
- **TASK-BOOKING-001**：**Closed（2026-08-12）**——最终固定实现 `4d5381a`；真实 PostgreSQL/Redis 预约 14 passed、全套 57 passed / 0 skipped，独立空库 `up → down base → up` 通过；TC-APT-003 两 backend PID + 屏障连续 10 轮与 loser 完整回滚通过，严格 Base64URL key、端点 CSRF/RBAC、Redis fail closed 已冻结；Ruff/format/mypy/pip check/secret scan 全通过；DB/API/依赖不变。
- **TASK-REVIEW-BOOKING-001**：**Closed / PASS（2026-08-12）**——原审查 `ae651c5` 的 P1=2/P2=2 与第二轮计数 P2 均已向前修正；第三轮独立审查 `ce5b95f` 结论 P0=0 / P1=0 / P2=0。
- **TASK-BOOKING-FLOW-001**：**Closed（2026-08-12）**——登录→真实 14 天 Slot→连续三格→预览→原子创建的桌面端闭环已交付；最终实现快照=`ccd698b`，真实 PostgreSQL/Redis 53 passed、基础测试 5 passed、前端 1 passed + typecheck/build；一轮独立审查唯一 P1 已修复，无遗留 P0/P1。
- **TASK-TEST-BOOKING-001**：**Closed（2026-08-11）**——测试兼容性提交 `b8b241f` 仅显式清理无 FK 的 Outbox/Audit 测试数据，不改断言、10 轮并发、生产代码或 schema；真实 PostgreSQL/Redis 预约测试 8 passed / 0 skipped。
- **TASK-TEST-BOOKING-002**：**Closed（2026-08-12；证据修正待第三轮复核）**——测试增强 `90884af` 与最终固定实现 `4d5381a` 已补强 TC-APT-003 的真实事务重叠/backend PID/loser 完整回滚，以及两个预约 POST 的 CSRF/RBAC 与 Redis fail-closed 端点覆盖；第二轮真实复跑预约套件为 14 passed，修正 `b41b28c` 的 13 passed 计数笔误；冻结断言未放宽、无 skip/mock。
- **TASK-M1-APPOINTMENTS**：**Closed（2026-08-12 本机验证批处理通过，verified_commit=69d4cee）**——合并同域主线：我的预约列表 + 改期（原子换格/会议号原地改）+ 取消；后端三接口 `listMyAppointments`/`updateAppointment`/`cancelAppointment` + 真实 PG/Redis 测试 `test_management.py` + 前端 `my-appointments.tsx`；复用现有列、无新迁移、不单列 REVIEW 任务。提交：`6483ba0`（主体）+ `7da4fad`（list_my 收窄为 active 修复）。本机验证批处理：`pytest tests/appointments/test_management.py` 9 passed（WSL 真实 PostgreSQL/Redis，2026-08-12）；`verified_commit`=69d4cee（测试修正提交）。TASK 交付证据已回填，spec_sync=clean、规范影响 none。
- **TASK-M2-APPOINTMENTS**：**Closed（2026-08-12 本机验证批处理通过，verified_commit=69d4cee）**——SSE 实时刷新：新增 `GET /slots/events`（`streamSlotEvents`，interviewer 会话、无 CSRF）+ 前端 `InterviewView` 的 `EventSource` 订阅；复用 `slot_snapshot` 读路径每连接 1s 轮询派生变更，ownership 脱敏（none/self/other），同账号≤2 连接（超额 429 RATE_LIMITED），15s 心跳；无 Redis 中间件、无新迁移、不单列 REVIEW 任务。本机验证批处理：`pytest tests/appointments/test_sse.py` 2 passed（WSL，2026-08-12）；verified_commit=69d4cee（含 da93ca2 实现 + 7d583a1 测试 + 69d4cee 测试修正：is_disconnected async 桩 + 本周一种子）。
- **TASK-M3-APPOINTMENTS**：**Closed（2026-08-12，verified_commit=8391208）**——通知 Worker（Outbox 消费 + SMTP 发信）：新增 `apps/api/app/notifications/`（email.py 渲染+发送、worker.py 轮询 Outbox）+ 重写 `worker.py` 入口；复用 `notification_events`（无新迁移）、`FOR UPDATE SKIP LOCKED` 原子领取、status 状态机承载 at-least-once 重试；解密复用 `_decrypt_appointment`，收件人=预约归属人注册邮箱；SMTP 163 凭据仅运行时环境变量。**飞书通道与 `notification_deliveries` 尝试历史表延后**（无飞书凭据 / 降低未验证 schema 风险）。verified_commit=8391208（实现提交）；**未解决风险：Worker SMTP 发送路径 runtime-unverified——本环境无 SMTP，`test_worker.py` 未建，仅 ruff/mypy/py_compile 通过，待有 SMTP 凭据时补 `test_worker.py` 真实或 smtpd 桩验证**。
- **TASK-M4-APPOINTMENTS**：**Closed（2026-08-13 本机验证批处理通过，verified_commit=7c91a83）**——注册 / 邮箱验证 / 密码找回（auth 域补全），**严格对齐已批准 `docs/api/openapi.yaml` v0.2 的 4 个 operation**：`registerInterviewer`（`POST /auth/register`,202）/ `verifyEmail`（`POST /auth/verify-email`,204）/ `requestPasswordReset`（`POST /auth/password-reset/request`,202）/ `confirmPasswordReset`（`POST /auth/password-reset/confirm`,204）。安全不变量：令牌仅存 SHA-256 `token_hash`、一次性+过期、找回后 `revoke_all_sessions` 作废全部会话、ip 限频防枚举、注册/找回申请恒 202 不泄露存在性、邮件 best-effort（SMTP 未配 sink）、BCrypt 10–72 UTF-8 字节（`PasswordHasher`）；复用 Redis 限频、`notifications/email.py` 渲染+发送、`build_auth_runtime` 注入 `EmailSender`。复用 migration 0001 的 `email_verification_tokens` / `password_reset_tokens`（**无新迁移**）。**规范影响：OpenAPI=clean（实现已批准 4 operation，未改契约）；测试计划 TC-AUTH-REG/VERIFY/RESET 由 `tests/auth/test_account_lifecycle.py` 真实 PG/Redis 覆盖（4 passed）**。`resend-verification` 显式**非目标**（契约未签约，需 Change Request 补 operationId 方可实现）。SMTP 163 凭据仅运行时环境变量。本机验证批处理：`ruff check .` All checks passed + `mypy` 0 error（26 source files）+ `pytest tests/auth/test_account_lifecycle.py` 4 passed（2026-08-13）；`verified_commit=7c91a83`（含 b77931e 实现 + 7c91a83 测试令牌长度修正）。TASK 交付证据已回填，spec_sync=clean、规范影响 none。
- **TASK-GOV-007**：**Closed（2026-08-13，verified_commit=d51b9e0）**——ruff / mypy repo 级门禁绿化（M1–M4 跨域，追认登记先行提交 `665a067`/`b01acaf`）。收口：`d51b9e0`（ruff `--fix` 写回 + mypy 16 error 全清，4 文件）+ 本任务单。本机 base 解释器复核 `ruff check .` exit 0、`mypy` 0 error（26 source files，零 env 噪声）、全量 `pytest` 44 passed / 27 skipped / 2 failed（2 failed 经证为既有非回归，非本任务引入）。变更预算 max_files=12 未超；是否偏离 TASK=是（先行提交追认，历史不重写）。门禁 repo 级全绿达成。
- **TASK-M5-APPOINTMENTS**：**已关闭（Closed，2026-08-13 用户显式授权）**——管理后台（admin 操作域）7 operation 全部实现：`adminListAppointments`/`forceCancelAppointment`/`listAvailabilityOverrides`/`createAvailabilityOverride`/`updateAvailabilityOverride`/`deleteAvailabilityOverride`/`createCompanyBookingException`。安全不变：全部端点强制 `role=owner_admin` RBAC + 写操作落 `audit_logs`；GET 读仅会话（无 CSRF）、状态变更端点强制 CSRF+同源（安全拆分对齐 OpenAPI）；availability override 变更与受影响 Slot 物化同事务；force-cancel 占用 `owner_locked` 原子回滚；company exception 一次性 HMAC 去重 + 过期校验。**ruff/mypy repo 级双绿（29 source files）+ DB-free wiring smoke 通过 + 真实 PG/Redis 集成测试 6 passed in 10.78s**（用户 WSL，2026-08-13）；spec_sync=clean、verified_commit=cfb1854、关闭门禁三项全绿。详见任务单 `tasks/TASK-M5-APPOINTMENTS.md`。
- **TASK-M6-AI-QA**：**已关闭（Closed，2026-08-13 用户显式授权，含生产迁移执行批准）**——AI 问答域（RAG + 人格层/数字分身）**9 个 operation 全部实现并验证**。**首轮（无表子集）已实现**：`getPageContent` + `listRecommendedQuestions` + 匿名 `streamAnswer`（SSE：started→delta→citations→completed；基于静态页知识源 grounding、第一人称人格层、越界/无依据→offtopic 拒答、匿名不持久化、无效 cookie→401、匿名带 conversation_id→401、公开限频 429），落位 `apps/api/app/aiqa/` 10 模块（content/retrieval/persona/gateway/sse/service/router/rate_limit/models/runtime）+ `config.py` 可选 `JIANLI_LLM_*`（不设则 Stub 网关，无新运行时依赖，httpx 惰性导入）+ `factory.py` 常挂公开路由。**门禁（沙箱 DB-free）**：ruff All checks passed ✅ + mypy 0 error（40 source files）✅ + `pytest tests/aiqa/test_aiqa.py` 11 passed ✅ + DB-free 全量子集 34 passed / 14 skipped（9 ERROR 为 `test_management.py` 沙箱无 Docker 既有 env 阻塞）。**无新迁移/表/列/索引/枚举**。**账目偏差如实登记**：change_budget 预估 8 文件、实际 17（aiqa 包 10 + config/factory 2 + tests 2 + 治理/接手文档 3），超预算（预估偏差）不宣称未超。**会话持久化与知识库摄取（二/三轮）依赖 TASK-M6-DB 迁移批准**。**二轮（2026-08-13 已实现，commit `c9c5721`）**：基于已批准 0004 表实现 `listConversations`/`createConversation`/`listConversationMessages` + `streamAnswer` 落库（带有效会话+conversation_id 时持久化 user/assistant 消息、offtopic 标记、started 回显 conversation_id；匿名/无 conversation_id 恒不落库）；新增 `aiqa/repository.py`（原生 SQL），factory/runtime 注入 auth engine 共享池；会话归属 owner-only（他人 403、未知 404）。门禁：ruff ✅ + mypy 41 files ✅ + DB-free 14 passed ✅；**用户 WSL 真实 PG/Redis 集成测试 5 passed in 9.21s（2026-08-13），verified_commit=c9c5721**。**三轮（2026-08-13 已实现并验证，commit `851742a`）**：知识库摄取——md/txt 上传（202 语义 + 活跃 checksum 去重 + 10MB 上限 + pdf/docx failed 态）+ 本地磁盘对象存储 + pgvector 检索（迁移 0005：`CREATE EXTENSION vector` + `embedding vector(768)`；PG 镜像换 pgvector/pg16，均用户批准）+ embedding（OpenAI 兼容 /embeddings 优先 + 本地哈希降级）+ `listKnowledgeDocuments`/`uploadKnowledgeDocuments`/`deleteKnowledgeDocument`（owner_admin + 写强制 CSRF）+ `streamAnswer` 知识库优先检索；新增 `python-multipart` 运行时依赖（如实登记）。**9 个 operation 全部实现**；**用户 WSL 全套 14 passed in 14.84s（迁移 5 + 会话 5 + 知识库 4，2026-08-13）**，`verified_commit=851742a`（含 2acb6c4/0ac3dce 测试修复）；alembic.ini 加 path_separator + pytest filter 消除两条无害警告。接手文档见 `AGENTS.md` §10（恒读，含 12 模块地图/9 operation/安全不变量/测试命令/扩展点）。**M6 收口：主线已合入 `master` 分支**。详见任务单 `tasks/TASK-M6-AI-QA.md`。
- **TASK-M6-DB**：**已关闭（Closed，2026-08-13 用户显式授权，含生产迁移执行批准）**——AI 问答域迁移：0004（`conversations`/`conversation_messages`/`knowledge_documents`/`knowledge_index_versions` + 5 枚举 + 索引/约束）+ 0005（`CREATE EXTENSION vector` + `embedding vector(768)`，pgvector/pg16 镜像），**全部出自已批准领域模型 v1.1.5 §6.13/6.14**，可逆迁移（up→down→up 验证通过）。关键决策：`active_index_version_id` 循环 FK 后置补建；活跃文档 `content_checksum` 部分唯一索引（删除后可重传）；`RecommendedQuestionCache`（§6.16）用户确认不纳入。**用户 WSL 真实 PG 验证**：迁移测试 5 passed + M6 全套 14 passed（2026-08-13，pgvector/pg16）；`verified_commit=851742a`。**生产迁移执行已批准并完成**：dev 库 `jianli_dev` 2026-08-13 由用户 WSL 执行 `alembic upgrade head` → 0005，验证通过（alembic_version=0005、vector 扩展、embedding 列、4 张知识库表就位）。
- **TASK-FE-AIQA-001**：**已关闭（Closed，2026-08-13 用户验证通过并授权关闭）**——前端 AI 问答页：ChatPanel 真实化（`POST /answers:stream` SSE 流式回答、推荐问题、引用、grounded/offtopic 徽标、错误态、回答中禁用输入；resume 页 live，interview/mine 静态降级；vite proxy 补 AI 问答路径）。实现 `82d6c19` + 治理回填 `5aaeb21`；门禁 typecheck ✅ / vitest ✅ / build ✅；**用户 WSL 验证通过**（uvicorn 8000 + vite 5173；期间修复 vite8/rolldown native binding 缺失与 npmjs ECONNRESET，教训已固化）。详见任务单 `tasks/TASK-FE-AIQA-001.md`。
- **TASK-KB-PDF-001**：**已关闭（Closed，2026-08-13 用户验证通过并授权关闭）**——知识库 PDF 支持 + 前端管理页：`uploadKnowledgeDocuments` 支持 **pdf**（`pypdf` 提取文本 → `type=pdf, parse_mode=native` → 去重 → indexed；损坏/空文本 failed 带原因；md/txt 照旧、docx 仍 failed；pypdf 依赖已批准登记）+ 前端管理页（Page=admin：owner_admin 登录→PDF/md/txt 多文件上传→列表 status 徽标/删除）+ 页面一 PDF 简历展示（`<embed src="/resume.pdf">`，素材放 `apps/web/public/resume.pdf`）。实现 `cb4d16e` + 测试修复 `5525cb6`；后端门禁 ruff ✅ / mypy 43 ✅ / DB-free 14 passed ✅；**用户 WSL 验证**：test_knowledge **6 passed in 10.48s** + 前端 typecheck ✅ / vitest ✅ / build ✅，`verified_commit=5525cb6`。详见任务单 `tasks/TASK-KB-PDF-001.md`。
- **TASK-RAG-EVAL-001**：**Open（2026-08-14 已实现并验证，commit `b20f67d`，verified；待用户授权关闭）**——RAG 评测集（P0 面试工程）：`tests/aiqa/test_rag_eval.py` 14 条用例（4 篇中文语料走真实上传→chunk→混合检索→streamAnswer 全链路）。**命中型 8 条：HIT=8/8 (100%)**（grounded + citations 含期望 doc，门槛 ≥75%）；**拒答型 6 条：REJECT=0/6 XFAIL**（`offtopic=False grounded=True`——实测捕获 P1 缺陷：`search_chunks` 无相关性阈值、向量 top-10 硬召回，知识库有文档时任何问题都 grounded；评测把"拒答率 0%"变成可测量基线，P1 加阈值后删 xfail 转绿）。`verified_commit=b20f67d`；门禁 ruff ✅ + mypy 45 ✅ + DB-free 14 passed ✅。诚实标注：语料 4 篇 top-6 候选覆盖全，命中 100% 含覆盖效应，扩语料为后续项。详见任务单 `tasks/TASK-RAG-EVAL-001.md`。
- **TASK-FE-INTERVIEWER-001**：**已关闭（Closed，2026-08-14 用户显式授权）**——Interviewer 个人中心：DashboardView（默认页，统计卡+未来 7 天即将面试+快捷操作，未登录引导卡）+ 历史会话真实化（登录拉 `/conversations`，点击会话恢复至 ChatPanel（拉 messages + 发送带 conversation_id 持久化），新建对话清空回匿名）+ 登录首问自动创建会话闭环补丁（`d203182`）+ 管理入口按 role 隐藏（仅 owner_admin）。实现 `233828c`；用户 WSL 手动验证通过（uvicorn+vite，dashboard/历史/ChatPanel 正常）；`verified_commit=233828c`。已知限制：InterviewView 页内登录后 user state 不即时回填（刷新同步）；会话无重命名/删除。详见任务单 `tasks/TASK-FE-INTERVIEWER-001.md`。
- **TASK-KB-RAG-001**：**已关闭（Closed，2026-08-14 用户显式授权）**——RAG 检索质量工程：迁移 0006 `knowledge_chunks`（chunk 级 embedding，0005 doc.embedding 列弃用）+ `chunking.py`（500/50 切分边界优先）+ `bm25.py`（纯 Python Okapi + RRF 融合）+ 混合检索（向量 top10 + BM25 top10 → RRF top6 → citations `doc·chunk`）；契约不变。**用户 WSL 验证 12 passed in 13.67s**（迁移 5 + 知识库 7，含长文档中段埋词 chunk 级命中），`verified_commit=25a3fc3`。详见任务单 `tasks/TASK-KB-RAG-001.md`。
- **TASK-DEPLOY-001**：**已关闭（Closed，2026-08-14 用户显式授权）**——简历素材（真版 `14.pdf` 284KB）+ DeepSeek V4 Flash 支持（embedding 配置拆分独立 `JIANLI_LLM_EMBEDDING_*`，DeepSeek 无 /embeddings 端点）+ httpx utf-8 修复（`79e64d3`）+ 硅基流动 BGE-M3 dimensions 400 修复（`0aac1f8`）。**用户 WSL 验证**：env 齐全后启动正常、简历 PDF 显示、DeepSeek 问答通、BGE-M3 灌库成功。`verified_commit=fef6b26`。API key 由用户运行时 env 提供（不落文件）。详见任务单 `tasks/TASK-DEPLOY-001.md`。
- **TASK-ARCH-IMPACT-001**：**已完成（Review 收口，2026-08-10）**——architecture v0.2 正文已同步 SRS v1.2 的 approved 状态、based_on、AUTH_EXPIRED/RATE_LIMITED 和 Override 错误码；spec_sync=clean，未改变架构行为。
- **TASK-DM-003**：**已关闭（Closed，2026-08-08 末）**——领域模型 v1.1.4→v1.1.5 修订（多投递目的修复 + 单 owner 方案 A：`User.uq_active_owner_admin` + `OwnerContactConfig.candidate_feishu_open_id_ciphertext`）。执行顺序：① 用户批准 v1.1.5 → 独立批准锚点 `f412c7d`（baseline.domain_model review→approved）；② SRS impact review（`10fb2f2`：based_on→1.1.5、版本引用同步、行为不变、不复制物理索引）；③ architecture v0.2 sync（`f0d3264`：§6 纳入 delivery_purpose/幂等键/uq_delivery_attempt 5 列/单 owner 解析/飞书标识缺失处理，based_on 升 1.1.5）；④ spec_sync 转 clean 后关闭。关闭门禁四条件满足（测试=一致性校验通过 / 规范影响已处理 / spec_sync=clean / verified_commit=`f0d3264`）。不建 TASK-GOV-*；未进入下游阶段。架构待办 §13 两项后续修正（用户取消 Slot 重新物化 / created_at 租约区分未发送与结果未知）已于 2026-08-09 经 TASK-ARCH-002 三项修正执行并裁定（§4.6 重新物化 / §6.4 两类超时），非待执行；另 2026-08-09（续）两项并发竞态修正见 §12.3 条目 20/21。
- 具体版本与评审状态见 `docs/baseline.yml`。

---

## 本周阻塞

- 待确认项（PRD §8.2，不阻塞设计但阻塞上线）：SMTP / 域名 / 备案、飞书授权、人格素材、知识库文件。
- 网易 163 邮箱授权码等密钥**绝不写入任何文档 / 记忆 / 配置文件**，仅存运行时环境变量或 Secret Manager。

---

## 下一步（评审推荐顺序，仍编码前）

```
SRS v1.0 → UI 线框 → 架构与 ADR → 安全设计 → OpenAPI/SSE 合同 → 测试计划 → 开发准入评审 → 功能编码
```

> 注：当前门禁顺序（**2026-08-10 收口，设计门禁已完成，现进入首个实现任务**）——
> ① ✅ 用户批准 **domain_model v1.1.4** → baseline `domain_model.status: review→approved`，独立批准锚点 `f537296`（**不复用 `f64b6de`**）；
> ② ✅ **TASK-SRS-001 执行 SRS impact review**（`srs.based_on.domain_model`→1.1.4 + 修正 SRS §6.3 过期的 Argon2id 描述；结论 = "需文字同步、不改变用户可观察行为"，**非 none**）→ TASK-SRS-001 `spec_sync` 转 clean；
> ③ ✅ **TASK-DM-002 `spec_sync` 转 clean + 关闭**（verified_commit=`94bedb5`，approval_commit=`f537296` 即 domain_model v1.1.4 独立批准锚点；对齐 TASK-TEMPLATE 关闭门禁：`spec_sync=dirty` 不得关闭，故必须在 ② 之后）；
> ④ ✅ 用户独立评审批准 **SRS v1.0**（AI 不代签，独立批准锚点 `26ae844`，不复用 `173cf9b6`）→ 关闭 TASK-SRS-001（verified_commit 见 S3 回填）、用例规约冻结为历史输入、SRS 成为行为唯一源；
> ⑤ ✅ **UI 线框影响评审（TASK-UI-IMPACT-001）**：结论=基本可沿用（SRS `26ae844` + 领域模型 1.1.4 与现有线框对齐；仅 A6 通知失败中心状态枚举轻微缺口）→ 内容缺口由 **TASK-UI-002** 承载；`ui_wireframe.status` 仍 pending，待用户评审实际线框。
> ⑤b ✅ 用户批准 UI 线框 v1.0 → ⑥ ✅ 领域模型修订并批准 v1.1.5 → ⑦ ✅ architecture v0.2 → ⑧ ✅ SRS v1.2 / security v0.1 / OpenAPI-SSE v0.1 / test-plan v0.1 全部 approved → ⑨ ✅ ADR-IMPL-001 accepted + TASK-READY-001 PASS → **当前执行 TASK-IMPL-WEB-001**。
> ⑩ ✅ TASK-BE-001 + TASK-REVIEW-BE-001 关闭；下一后端主线为独立 DB/migration 任务，实际 SQL 须先经用户审批。
> `development_gate` 全 10 项 approved 前不得进入编码。

---

## 最后 verified commit（审计锚点）

> 按时间顺序列出治理验证锚点；**最新有效锚点 = 本文件末条**。历史锚点保留作审计回溯，不表示当前态。

- **历史治理锚点（保留，不表示当前态）**：`adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: `gov-sync-001-verified`）— 早期治理收尾 commit（含 TASK-GOV-SYNC-001 关闭证据 + 全部治理文件）。机器锚点首选真实 SHA，tag 仅作人类别名；解析见 `git rev-parse gov-sync-001-verified`。Review/Audit Mode（`AGENTS.md §9`）可 `git checkout gov-sync-001-verified` 复盘，但**不得再称其为"当前最后 verified commit"**。
- **领域模型完整验证快照**：`94bedb5be60b1678fb033c5d8735e38dae9a46a9`（`94bedb5`）— TASK-DM-002 关闭提交，含 domain_model v1.1.4 approved + SRS impact review（`d166992`）/ spec_sync=clean + TASK-DM-002 Closed 的完整验证态；为当前领域模型 v1.1.4 的可审计快照。
- **历史 SRS 验证锚点（保留作审计回溯，非当前最新）**：`06798a2815d60a50caebe3ce6582553531be8dea`（`06798a2`）— 本回合 SRS 收口提交（TASK-SRS-001 关闭），含 SRS approved + spec_sync=clean + TASK-SRS-001 Closed + 本 PROJECT_STATE 同步。
- **历史验证锚点（保留，非当前最新）**：`80e5bf3a014b33713f1d9bb78f1bbb9acbf0f535`（`80e5bf3`）— TASK-GOV-005 收口链（G1 快照 80e5bf3 + G2 证据回填 5f472a6），verified_commit=80e5bf3（被验证的交付物快照），含 TASK-GOV-004 锚点语义校正 + TASK-UI-002 文案收口 + 本 PROJECT_STATE 同步。
- **历史验证锚点（UI 阶段收口，保留作审计回溯，非当前最新）**：`38b102a91b3d8f0447de36791e67ae342be9e1f4`（`38b102a`）— UI 线框 v1.0 批准锚点（baseline.ui_wireframe version 0.0→1.0, status pending→approved）+ TASK-UI-001 关闭（verified_commit=c0f5829）；UI 阶段交付完成。
- **最新验证锚点（当前有效"最后 verified commit"）**：`f0d3264c5d91ec5d2a9c46ac3ed88c30e3643844`（`f0d3264`）— 领域模型 v1.1.5 批准 + 下游同步收口：domain_model v1.1.5 approved（批准锚点 `f412c7d`）+ SRS v1.1 impact review（`10fb2f2`，版本引用/based_on 同步、行为不变、不复制物理索引）+ architecture v0.2 同步（`f0d3264`，§6 纳入 delivery_purpose/幂等键/uq_delivery_attempt 5 列/单 owner 解析/飞书标识缺失处理、based_on 升 1.1.5）+ TASK-DM-003 关闭（spec_sync=clean，verified_commit=`f0d3264`）。领域模型阶段交付完成，下游进入架构 v0.2 评审（TASK-ARCH-002）。
- **架构 review 草案最新修订锚点（仍 review，非批准）**：`12dcd2d` — 2026-08-09（续）两项并发竞态修正：① 重写 §4.7 `AvailabilityOverride` 变更事务（先读旧范围 old_range∪new_range、统一锁范围内全部 Slot 含 booked、锁后复检冲突排除自身 id、无冲突才写、仅 appointment_id IS NULL 重新物化）；② 修正 `created_at` 语义（仅创建时间非领取时刻）+ §6.3.2 `Txn D` 仅领剩余租约充足 queued 行 + 新增 §6.4.1 `Txn W` 回执 CAS（命中 0 行=已被 Sweeper 回收、迟到 Worker 不覆盖 retry_scheduled/dead_letter），同步 §6.4/§6.7 与测试计划待覆盖风险。上一修订锚点 `1e0d9ed`（三项实现正确性修正）已并入本锚点。
- **架构 review 草案最新修订锚点（当前有效，仍 review，非批准）**：`3a18b7f` — 2026-08-09（续二）两项 Schema/并发收口：① §6.4.1 `Txn W` SQL 删除幻列 `NotificationDelivery.version`（逐字段核对领域模型 v1.1.5 §6.12 全 12 列）、`provider_message_id` 写独立列、`channel_metadata` 改 JSONB 合并不整体覆盖、`:meta` 通道白名单、`bounced_at`/`bounce_reason` 仍只由 §7 退信处理回写；② §4.0 新增 `L2.5 AvailabilityOverride` 锁层级（先于 L3）+ 强制规则 5，§4.7 补齐同一 override 的并发 UPDATE/DELETE（先 `SELECT ... FOR UPDATE` 锁自身行取真实 `old_range`，禁用前端传入旧值）与「CREATE/UPDATE 范围须命中现存 Slot 否则拒绝」，§4.5 并发矩阵增 3 行。新增开放项登记于 §11.2（`OVERRIDE_NOT_FOUND`/`OVERRIDE_RANGE_EMPTY` 为架构内部占位名，**非已批准 SRS §8 错误码**，码值留 OpenAPI 裁定，需新增须走 Change Request）。前两个修订锚点 `1e0d9ed` / `12dcd2d` 均已并入。供本轮评审，待用户独立批准 architecture v0.2。
- **架构批准锚点**：`da3f6fc` — 用户明确批准 architecture v0.2；被批准内容快照=`3a18b7f`，批准提交仅推进 baseline 状态。
- **架构阶段关闭验证锚点（当前有效）**：`d1043af` — architecture v0.2 approved + TASK-ARCH-001/002/003 Closed + PROJECT_STATE 同步。
- **最新验证锚点（security 阶段）**：`010e3e1` — security v0.1 approved + TASK-SEC-001 Closed + SRS v1.2 impact-sync，后续纯证据回填不改变该验证快照。
- **最新验证锚点（OpenAPI/SSE 阶段）**：`3e2b58b` — OpenAPI/SSE v0.1 approved + TASK-API-001 Closed + SRS/security impact-sync + Redocly 0 error / 0 warning。
- **最新验证锚点（测试计划阶段）**：`ebe6c1a` — test-plan v0.1 approved + TASK-TEST-001 Closed + 69 个冻结 TC / R1-R26 / 33 operationId 覆盖复核。
- **最新验证锚点（SRS v1.2 阶段）**：`1c443eb` — SRS v1.2 approved + TASK-SRS-003 Closed + SRS 正文状态同步 + 错误语义 impact review 收口。
- **最新验证锚点（实现栈阶段）**：`0a86a96` — ADR-IMPL-001 accepted；implementation 依赖边界已获用户接受，未安装依赖或写代码。
- **最新验证锚点（实现栈收口）**：`99678dc` — TASK-ADR-001 Closed + ADR-IMPL-001 accepted + 依赖边界验证。
- **最新验证锚点（开发准入）**：`fa57b64` — baseline 十项 approved、ADR accepted、TASK-IMPL-WEB-001 与 TASK-REVIEW-WEB-001 已纳入 Git，开发准入 PASS。
- **最新验证锚点（BE-001 后端骨架）**：`de9182638e7bbd609e562295887041c3ce548add`（`de91826`）— FastAPI/Worker 骨架最终实现；pytest 5 passed、Ruff/mypy/真实 API 与 Worker smoke 通过；TASK-BE-001 与独立审查以本快照为验证对象。
- **DB-001 历史实现快照**：`da8dc7f0e5c0be5ec81a23e114b9dcd6e915a234`（`da8dc7f`）— 身份域 6 表 Alembic migration 与锁文件的原始实现，历史保留未重写。
- **最新验证锚点（DB-001）**：`2179821` — 最终迁移实现与冻结验收对象；独立审查无 P1/P2，真实 PostgreSQL TC-OPS-002 10 passed / 0 skipped，`upgrade → downgrade → upgrade`、精确 schema/约束、重复升级与临时环境清理全部通过；TASK-DB-001 / TASK-INFRA-LOCAL-001 Closed。
- **最新验证锚点（AUTH 错误契约）**：`71d7861` — SRS v1.3 / OpenAPI v0.2 / test-plan v0.2 approved；新增 `INVALID_CREDENTIALS` 与 `INVALID_REQUEST`，不改变登录成功路径。
- **最新验证锚点（AUTH 最终实现）**：`b8c7fc5cda07a40fa96b079c63565df01f3f3a08`（`b8c7fc5`）— AUTH 已批准错误契约适配与最终安全验证快照；真实 PostgreSQL 16 + Redis 7 环境 AUTH 15 passed / 0 skipped、全套 27 passed / 0 skipped；独立审查 P0=0、P1=0。

- **最新验证锚点（DB-002）**：`2fd1199` ——预约域五表/三 enum/approved 约束最终迁移与回归快照；真实 PostgreSQL `up → down 0001 → up`、migration 22 passed / 0 skipped，独立审查 P0/P1/P2=0；未执行生产迁移。

- **最新验证锚点（DB-003）**：`4f3b74c` ——预约创建所需 NotificationEvent/AuditLog 最小迁移最终快照；真实 PostgreSQL `up → down 0002 → up` 与连续两遍 migration 26 passed / 0 skipped，独立审查 P0/P1/P2=0；未执行生产迁移。

- **最新验证锚点（BOOKING-001）**：`0e5f6602664f1fae3799f6ed67b4bcbef3fbebec`（`0e5f660`）——预约预览/创建、加密与并发事务实现完成；真实 PostgreSQL/Redis 预约 14 passed、全套 57 passed / 0 skipped，显式 migration `up → down → up` 通过，第三轮独立审查 P0/P1/P2=0。

- **最新验证锚点（M1/M2 预约+SSE 本机验证批处理）**：`69d4ceedf47e222e5a7e8eb69edae9d7f37d5ef9`（`69d4cee`）——M1 `test_management.py` 9 passed + M2 `test_sse.py` 2 passed（WSL 真实 PostgreSQL/Redis，2026-08-12）；测试修正提交（is_disconnected async 桩 + 本周一种子 + DUP_COMPANY 测试种子 + tests/__init__.py），生产代码未改；TASK-M1/M2 关闭。

- **M3 通知 Worker 验证锚点（部分验证）**：`8391208` ——M3 实现提交；Worker SMTP 发送路径 runtime-unverified（无 SMTP，test_worker.py 未建），待补测。

- **最新验证锚点（M4 账户自助）**：`7c91a83` ——M4 注册/邮箱验证/密码找回实现（`b77931e`）+ 测试令牌长度修正（`7c91a83`）；真实 PG/Redis `test_account_lifecycle.py` 4 passed；ruff/mypy repo 级全绿；TASK-M4 Closed。

- **最新验证锚点（门禁绿化 GOV-007）**：`d51b9e0` ——ruff/mypy 16 error 收口 + ruff `--fix` 写回（email.py / worker.py / appointments/service.py / auth/service.py）；repo 级双门禁 exit 0；TASK-GOV-007 Closed（先行提交 665a067/b01acaf 追认，历史不重写）。

- **M5 验证锚点（Closed，2026-08-13 用户授权关闭）**：`cfb1854` ——M5 管理后台 7 operation 实现（`admin/` 包 + `appointments/service.py` 扩展 8 方法 + `factory.py` 挂载 + `tests/admin/test_admin_actions.py`）+ 契约偏离修正（a201578 证据回填 / 24665fb 3 处失败修正 / cfb1854 UUID 导入回归修复）；ruff/mypy repo 级全绿（29 source files）+ DB-free wiring smoke 通过 + **真实 PG/Redis 集成测试 6 passed in 10.78s**（用户 WSL，2026-08-13）；spec_sync=clean、verified_commit=cfb1854、关闭门禁三项全绿。用户显式授权关闭，TASK-M5 Closed。

本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
