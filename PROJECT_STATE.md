# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（**SRS v1.1 / approved**（v1.0 于 `26ae844` 批准、v1.1 退信(Bounce) 缺陷修正于 `00e125c` 批准；TASK-SRS-002 已关闭、TASK-UI-002 已同步退信并关闭、SRS 现为行为唯一源）；domain_model **v1.1.5 / approved**（TASK-DM-003 已关闭、下游 SRS/架构已同步）；TASK-DM-001 历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点、v1.1.4 批准锚点 `f537296` 保留为历史；**UI 线框 v1.0 / approved**（经用户 2026-08-08 独立评审批准，approval_commit=`38b102a`；TASK-UI-002/TASK-UI-003 均已闭合、TASK-UI-001 已关闭）；现进入架构/ADR 阶段）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。

- **领域模型 v1.1.5 / status=approved**（TASK-DM-003 已关闭，2026-08-08 末用户批准，独立批准锚点 `f412c7d`）：修复 `NotificationDelivery` 无法表达「同一业务事件、同一通道、多种投递目的」的实现阻塞——新增 `delivery_purpose` 列（candidate_notification / interviewer_confirmation / interviewer_cancellation）+ 唯一约束由 `(event_id, channel, event_version, attempt_no)` 调整为 `(event_id, delivery_purpose, channel, event_version, attempt_no)`；并新增 `OwnerContactConfig.candidate_feishu_open_id_ciphertext`（AES 密文）+ `User.uq_active_owner_admin` 部分唯一索引（单 owner 方案 A）。事件类型继续表达业务事实，投递目的表达投递意图，不重新引入 confirm_mail 业务事件类型。**v1.1.4 已于 `f537296` 正式批准（历史事实保留，不予否认）**，其内容由本 v1.1.5 取代。下游影响评审已执行：SRS v1.1 仅同步版本引用与 based_on（行为不变、不复制物理索引）、UI v1.0 impact=none、architecture v0.2 §6 已纳入 delivery_purpose 同步（仍 review 待批准）。密码哈希冲突升级条款沿用 v1.1.4，未改。TASK-DM-003 已关闭（`verified_commit=f0d3264`）。
- **SRS v1.1 / status=approved**（v1.0 于 `26ae844` 批准；v1.1 退信(Bounce) 缺陷修正经用户 2026-08-08 独立评审批准，独立批准锚点 `00e125c`，不复用 review 草案 `1c21d7d`；v1.0 approved 快照冻结于 `26ae844` 不重写），`spec_sync=clean`。`baseline.srs.based_on` = prd 2.3.3 / use_cases 1.7.2 / domain_model 1.1.5（上游均已 approved 且对齐，domain_model 已随 v1.1.5 批准同步）；TASK-SRS-001 已完成 impact review 并关闭；**SRS 现为行为唯一源**（precedence 高于 PRD/用例规约），用例规约冻结为历史输入；**v1.1 缺陷修正（TASK-SRS-002）已关闭**：补充退信记录/展示筛选/告警/手动重发/不回滚预约，v1.0 遗漏项已补。
- **UI 线框 v1.0（TASK-UI-001 / ui-wireframe.md）**：UI 线框 v1.0 经用户 2026-08-08 独立评审批准（approval_commit=`38b102a`，baseline.status=`approved`）；影响评审（TASK-UI-IMPACT-001）结论=基本可沿用 + 1 处缺口；内容缺口由 TASK-UI-002 执行并闭合（A6/A7 失败三态 + 退信），8 项后续内容修正由 **TASK-UI-003** 一次性修正并闭合（对齐 SRS v1.1、消除误导实现表述）；TASK-UI-001 已关闭。下游进入架构/ADR 阶段。
- **架构设计（TASK-ARCH-001 产出 v0.1 → TASK-ARCH-002 升版 v0.2）**：v0.1（快照锚点 `2f73982`，TASK-ARCH-001 产出）已被 **TASK-ARCH-002** 升版为 **v0.2（review 草案）**，并经 **domain_model v1.1.5 批准后下游同步**（TASK-DM-003 关闭后，architecture v0.2 §6 已纳入 delivery_purpose：投递创建/幂等键/重试驱动/uq_delivery_attempt 5 列、单活跃 owner 收件人解析 `uq_active_owner_admin`、飞书接收标识缺失处理；based_on 升领域模型 1.1.5）——修正 SSE 可靠传播（撤回 Redis Pub/Sub 作事件源、改 commit-derived 轮询消除双写窗口）、统一事务锁顺序（L0 Company→L1 Appointment→L2 CompanyBookingException→L3 AppointmentSlot 按 start_at 升序）、补全 Outbox Worker（`FOR UPDATE SKIP LOCKED` + 隐式租约 + 至少一次语义）、退信入口标为公网不可信（幂等回写/未知拒绝/不改预约状态）、四项核心 ADR 给唯一推荐。两份任务均 `review`，**不代签 approved**；v0.1 缺陷登记见 TASK-ARCH-001 末段；密码哈希留《安全设计》；`AUTH_EXPIRED` 冲突 + 取消释放目标状态登记为开放项。

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
- **TASK-ARCH-001**：**进行中（review 草案，2026-08-08；内容已被 TASK-ARCH-002 升版取代）**——架构设计 review 草案（architecture.md v0.1，快照锚点 `2f73982`）；覆盖 8 项目标 + ADR 清单；based_on SRS v1.1/领域模型 1.1.4/UI 线框 1.0；baseline.architecture=`review`；**不代签 approved**；v0.1 缺陷登记见本任务末段，已由 TASK-ARCH-002 在 review 态内升版 v0.2 修正。待用户独立评审批准 architecture v0.2。
- **TASK-ARCH-002**：**进行中（review 草案升版，2026-08-08；2026-08-09 补充三项实现正确性修正 + 两项并发竞态修正）**——架构内容修正（architecture.md v0.1→v0.2）：SSE 可靠传播 / 预约事务统一锁顺序 / Outbox Worker 补全 / 退信入口边界 / 四项核心 ADR 推荐；2026-08-09 补充：§6.3.2 投递级原子领取（queued→sending，短事务 RETURNING、提交后才调外部）+ 澄清 `uq_delivery_attempt` 只防重复建行不防同一行重复发送、§4.6/§4.7 Slot 释放统一按 `AvailabilityOverride` 与日历规则重新物化（不再无条件 available）、§6.4 区分 `queued`（未发送）/ `sending`（结果未知）两类超时与不同 `last_error`、删除 §13 待办（原 §11.2 开放项已裁定并入 §4.6）；2026-08-09（续）两项并发竞态修正：重写 §4.7 `AvailabilityOverride` 变更事务（先读旧范围、统一锁全部 Slot 含 booked、锁后复检冲突排除自身 id、无冲突才写、仅对 appointment_id IS NULL 重新物化）、修正 `created_at` 语义（仅创建时间非领取时刻）+ §6.3.2 `Txn D` 仅领剩余租约充足 queued 行 + 新增 §6.4.1 `Txn W` 回执 CAS（命中 0 行=已被 Sweeper 回收、迟到 Worker 不覆盖 retry_scheduled/dead_letter）；同步 §6.4/§6.7 与测试计划待覆盖风险；2026-08-09（续二）两项 Schema/并发收口：§6.4.1 `Txn W` SQL 删除幻列 `NotificationDelivery.version`（领域模型 v1.1.5 §6.12 无该列）、`provider_message_id` 写独立列、`channel_metadata` 改 `COALESCE(...,'{}'::jsonb) || :meta` JSONB 合并、新增全 12 列逐字段核对表、`:meta` 通道白名单、bounce 键仍只由 §7 回写；§4.0 新增锁层级 `L2.5 AvailabilityOverride`（按 id，先于 L3）+ 强制规则 5，§4.7 重写为 8 步（UPDATE/DELETE 先 `SELECT ... FOR UPDATE` 锁自身行取真实 `old_range`、CREATE/UPDATE 范围须命中现存 Slot 否则 ROLLBACK、再锁全部 Slot 含 booked、锁后复检排除自身 id、无冲突才写、仅物化 `appointment_id IS NULL`）、§4.5 矩阵增 3 行、§11.2 登记「对外错误码命名留 OpenAPI 裁定」开放项。baseline.architecture=`review`（version 0.2）；**不批准架构**；不扩模型；不建 TASK-GOV-*；不进入安全/OpenAPI/测试计划/编码。commit `1e0d9ed`（三项修正）+ `12dcd2d`（两项并发竞态修正）+ `3a18b7f`（两项 Schema/并发收口，均 review 不批准），待用户独立评审批准 architecture v0.2 后闭环。change_budget max_files=5（architecture.md / TASK-ARCH-002.md / TASK-ARCH-001.md / baseline.yml / PROJECT_STATE.md）。
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

> 注：当前门禁顺序（**2026-08-08 第三轮修正 + 本回合 SRS 收口，①②③④ 已完成，现处 ⑤**）——
> ① ✅ 用户批准 **domain_model v1.1.4** → baseline `domain_model.status: review→approved`，独立批准锚点 `f537296`（**不复用 `f64b6de`**）；
> ② ✅ **TASK-SRS-001 执行 SRS impact review**（`srs.based_on.domain_model`→1.1.4 + 修正 SRS §6.3 过期的 Argon2id 描述；结论 = "需文字同步、不改变用户可观察行为"，**非 none**）→ TASK-SRS-001 `spec_sync` 转 clean；
> ③ ✅ **TASK-DM-002 `spec_sync` 转 clean + 关闭**（verified_commit=`94bedb5`，approval_commit=`f537296` 即 domain_model v1.1.4 独立批准锚点；对齐 TASK-TEMPLATE 关闭门禁：`spec_sync=dirty` 不得关闭，故必须在 ② 之后）；
> ④ ✅ 用户独立评审批准 **SRS v1.0**（AI 不代签，独立批准锚点 `26ae844`，不复用 `173cf9b6`）→ 关闭 TASK-SRS-001（verified_commit 见 S3 回填）、用例规约冻结为历史输入、SRS 成为行为唯一源；
> ⑤ ✅ **UI 线框影响评审（TASK-UI-IMPACT-001）**：结论=基本可沿用（SRS `26ae844` + 领域模型 1.1.4 与现有线框对齐；仅 A6 通知失败中心状态枚举轻微缺口）→ 内容缺口由 **TASK-UI-002** 承载；`ui_wireframe.status` 仍 pending，待用户评审实际线框。
> ⑤b ✅ 用户独立评审批准 **UI 线框 v1.0**（approval_commit=`38b102a`，baseline status→approved，TASK-UI-001 已关闭）→ ⑥ ✅ **领域模型修订（TASK-DM-003 升版 v1.1.4→v1.1.5）**：修复 NotificationDelivery 多投递目的阻塞（新增 `delivery_purpose` + 调整 `uq_delivery_attempt` 唯一约束 + `OwnerContactConfig.candidate_feishu_open_id_ciphertext` + `User.uq_active_owner_admin` 单 owner 方案 A）；下游影响评审已执行（SRS v1.1 仅同步版本引用与 based_on、行为不变、不复制物理索引；UI v1.0 impact=none；architecture v0.2 §6 已纳入 delivery_purpose 同步，仍 review）→ ⑥b ✅ **用户批准领域模型 v1.1.5**（独立批准锚点 `f412c7d`，TASK-DM-003 已关闭）→ ⑦ ⏳ **用户独立评审批准 architecture v0.2**（已同步 domain_model v1.1.5，待评审）→ 安全设计 → OpenAPI/SSE → 测试计划 → 开发准入评审 → 功能编码。
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

本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
