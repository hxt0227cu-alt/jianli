# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（**SRS v1.1 / approved**（v1.0 于 `26ae844` 批准、v1.1 退信(Bounce) 缺陷修正于 `00e125c` 批准；TASK-SRS-002 已关闭、TASK-UI-002 已同步退信并关闭、SRS 现为行为唯一源）；domain_model **v1.1.5 / approved**（TASK-DM-003 已关闭、下游 SRS/架构已同步）；TASK-DM-001 历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点、v1.1.4 批准锚点 `f537296` 保留为历史；**UI 线框 v1.0 / approved**（经用户 2026-08-08 独立评审批准，approval_commit=`38b102a`；TASK-UI-002/TASK-UI-003 均已闭合、TASK-UI-001 已关闭）；现进入架构/ADR 阶段）

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
- **TASK-DB-002 / TASK-REVIEW-DB-002**：**Awaiting Approval / Open（2026-08-11）**——预约域五张核心表迁移评审包与独立审查任务已建立；用户正式批准评审包前不写 migration、不执行数据库变更、不进入 BOOKING-001。
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

本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
