# TASK-DM-003 领域模型修订：NotificationDelivery 多投递目的（delivery_purpose）支持

> 领域模型修订 review 草案，承载 domain_model **v1.1.4 → v1.1.5**。本任务**只修一个实现阻塞**：`NotificationDelivery` 无法表达「同一业务事件、同一通道、多种投递目的」。
> **不批准领域模型**：`baseline.domain_model.status` 保持 `review`；**不修改下游工件**（SRS v1.1 / UI v1.0 / architecture v0.2），仅完成影响分析，待用户先批准 v1.1.5 后再同步下游。
> **不建 TASK-GOV-\***；不处理历史措辞；不进入安全设计 / OpenAPI / 测试计划 / 编码。

## 任务类型
- design         # 领域模型修订 review 草案（不代签 approved）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / SRS 1.1（approved，行为唯一源）/ UI 线框 1.0（approved）/ 架构 v0.2（review，TASK-ARCH-002）/ AI 治理 1.0.1（均取自 `docs/baseline.yml`）
- 基线 commit：8ae70bb（TASK-ARCH-002 证据回填；domain_model 当时为 1.1.4 approved，锚点 `f537296`）

## 精确规范引用（AI 只读取这些章节）
- 领域模型 v1.1.4：§1（存储策略）/ §2.3（类图 NotificationDelivery）/ §5（状态机·DeliveryStatus·NotificationEvent 生命周期）/ §6.11（NotificationEvent）/ §6.12（NotificationDelivery·uq_delivery_attempt）
- PRD v2.3.3：§4.5.1（确认函投递至面试官注册邮箱）/ §8.10.3（DeliveryStatus 枚举）/ P0-4（owner 取消发注册邮箱取消告知函）
- SRS v1.1：§3.5（预约创建·候选人通知+面试官确认函）/ §3.6（改期·候选人+面试官告知）/ §3.7（owner 强制取消）/ §3.8（通知可靠性·双通道）/ §4.3（SSE·通知可靠性）/ §6.2（状态模型·DeliveryStatus）
- UI 线框 v1.0：A6/A7（通知与同步失败中心：投递状态与退信筛选）
- 架构 v0.2：§6（Outbox·uq_delivery_attempt 与幂等键）/ §13（后续修正待办，本任务登记）

## 需求来源
- 实现阻塞：当前 `NotificationDelivery` 唯一约束 `(event_id, channel, event_version, attempt_no)` 无法在同一 `event_id`+`email` 下并存「给候选人的通知」与「给面试官的确认函」两行——二者收件人与意图不同却共享同一 (event_id, channel, event_version) 键，冲突。
- 关联需求：PRD §4.5.1 / P0-4、SRS §3.5/§3.6/§3.7（同一预约须分别通知候选人与面试官）。

## 目标
将 `docs/design/domain-model.md` 由 v1.1.4 修订为 v1.1.5（仍为 review 草案），完成六项（用户指令）：

1. **修复多投递目的表达**：`NotificationDelivery` 增加 `delivery_purpose`，使同一业务事件、同一通道、不同投递目的可并存多行。
2. **最小必要字段 + 三目的区分**：`delivery_purpose` 枚举至少含 `candidate_notification` / `interviewer_confirmation` / `interviewer_cancellation`；事件类型继续表达业务事实，投递目的表达投递意图；**不得重新引入 `confirm_mail` 业务事件类型**。
3. **唯一约束调整**：`(event_id, delivery_purpose, channel, event_version, attempt_no)`，使不同目的可独立记录尝试、状态、退信、重试和手动重发。
4. **每目的合法通道与收件人来源**：明确三类目的的 channel 与 recipient 来源；**不新增冗余明文收件人字段**，收件人由业务实体 + 目的确定。
5. **升版并置 review + 影响分析**：升 domain_model 至 v1.1.5（review）；完成对 SRS v1.1 / UI v1.0 / architecture v0.2 的影响分析；**不得同步修改这些下游工件**，等待用户先批准领域模型修订。
6. 架构保持 review、不批准、不进入安全设计（由 TASK-ARCH-002 持有）。
- 同时在架构待办中登记两项后续修正（不另建治理任务）：① 用户取消后 Slot 不得无条件 `available`，须按 AvailabilityOverride 与日历规则重新物化（owner 强制取消仍 `owner_locked`）；② `created_at` 隐式租约须限定 Worker 只创建可立即处理的尝试、`queued→sending` 立即发生、外部超时远小于 5 分钟，并区分 `queued` 超时（未发送）与 `sending` 超时（结果未知）。

## 非目标（明确排除）
- **不批准领域模型**（不得把 `baseline.domain_model.status` 改为 approved）。
- **不修改 SRS v1.1 / UI v1.0 / architecture v0.2 正文**（仅记录影响分析；下游同步待用户批准 v1.1.5 后由相应任务执行）。
- **不重新引入 `confirm_mail` 业务事件类型**：投递目的用 `delivery_purpose` 表达，事件类型保持业务事实语义。
- 不新增冗余明文收件人字段；候选人收件人沿用 `OwnerContactConfig.candidate_phone_ciphertext` / `OwnerContactConfig.candidate_feishu_open_id_ciphertext`（AES 密文）+ `owner_admin` 的 `User.email`，面试官收件人沿用 `Appointment.user_id → User.email`，发送时按访问控制解密。
- **不修改密码哈希冲突升级条款**（沿用 v1.1.4）。
- 不建 TASK-GOV-*；不处理历史措辞；不写代码/迁移脚本；不进入安全设计 / OpenAPI / 测试计划 / 编码。

## 允许修改路径
- docs/design/domain-model.md        # 主交付物：v1.1.4 → v1.1.5（新增 delivery_purpose + 调整唯一约束 + 目的映射）
- tasks/TASK-DM-003.md               # 本任务单自身（含证据回填）
- docs/baseline.yml                  # domain_model.version 1.1.4→1.1.5；status approved→review
- PROJECT_STATE.md                   # 同步领域模型阶段态与门禁顺序
- docs/design/architecture.md        # 仅追加 §13 后续修正待办（两项），不改 v0.2 技术内容、不推进 based_on

## 禁止修改路径
- docs/requirements/SRS.md / PRD.md / use-cases.md（除影响分析登记，不改动正文）
- docs/design/ui-wireframe.md
- 其他 tasks/TASK-*.md（除 ARCH-001/ARCH-002/DM-003）
- 任何代码文件、数据库迁移脚本、OpenAPI / SSE 契约文件
- 安全设计 / 测试计划 工件

## 已批准的 DB / API / 依赖变更
- **本任务即领域模型修订本身**：在领域模型 v1.1.4 已批准范围内，含两类变更：
  1. **`NotificationDelivery.delivery_purpose`**：新增字段 `enum[candidate_notification, interviewer_confirmation, interviewer_cancellation]`；**调整唯一索引** `uq_delivery_attempt` 由 `(event_id, channel, event_version, attempt_no)` 改为 `(event_id, delivery_purpose, channel, event_version, attempt_no)`。
  2. **`OwnerContactConfig.candidate_feishu_open_id_ciphertext`**：新增 AES 密文字段（候选人飞书接收标识，原无领域字段），由用户补正指令 item 3 显式授权「如需新增持久化字段，先作为领域模型变更明确列出」。
  3. **`User` 部分唯一索引 `uq_active_owner_admin`**：`CREATE UNIQUE INDEX uq_active_owner_admin ON "User"(role) WHERE role='owner_admin' AND deleted_at IS NULL`（由用户 2026-08-08 末次裁定方案 A 授权；MVP 单候选人个人站点、不引入 SiteConfig）。强制至多一个未删除的 owner_admin，确立三条运行不变量（恰一活跃 owner_admin / 缺失时 `candidate_notification` 失败告警不得任选 / `OwnerContactConfig.user_id` 必指该 owner_admin），并固定 `candidate_notification` 收件人解析链路（活跃 owner_admin User → User.email → 同 user_id OwnerContactConfig → candidate_phone_ciphertext / candidate_feishu_open_id_ciphertext）。
- 上述三项均为领域模型自身修订，由用户指令授权；**未新增任何实体 / 表 / 外部依赖**（索引属既有 `User` 表的约束，非新结构）。
- **不触发越界硬停**：变更范围由用户指令界定（delivery_purpose + uq_delivery_attempt + 新增一处 owner 联系密文字段 + 一处部分唯一索引），未越界到 SRS/UI/架构正文、未引入新实体或外部依赖；`candidate_feishu_open_id_ciphertext` 与 `uq_active_owner_admin` 均为显式列明的领域模型变更，不构成「未列明的新字段/约束」。

## 规范影响评估（spec impact）
- behavior_change：**false**（对最终用户可观察行为无变化：同一预约仍分别通知候选人与面试官，渠道/收件人/模板与 PRD/SRS 既有规定一致；仅为数据模型可正确表达既已要求的多目的投递）。
- affected_specs：
  - srs：impact = **需文字同步级更新**（非 none）。SRS v1.1 §3.5/§3.6/§3.7/§3.8/§6.2 已规定候选人通知 + 面试官确认函/取消告知函双线投递，意图与三目的映射一致；但 SRS 未显式出现 `delivery_purpose` 概念与新的唯一约束表述，待 v1.1.5 批准后补 `delivery_purpose` 术语与目的→通道映射说明。**不改变用户可观察行为**。
  - ui_wireframe：impact = **none（强制）**。UI v1.0 A6/A7 失败中心按 `DeliveryStatus` + 退信筛选，新增 `delivery_purpose` 仅为附加维度；UI 不强制改动即可继续工作，可选未来增强（按目的分组/筛选）。本任务不修改 UI。
  - architecture：impact = **需同步更新**（待批准后）。architecture v0.2 §6 引用 `uq_delivery_attempt(event_id, channel, event_version, attempt_no)` 与幂等键 `H(idempotency_key:channel:event_version)`，须在 v1.1.5 批准后于 §6.3/§6.5/§6.7 纳入 `delivery_purpose`；§4.3/§4.4 投递创建须置 `delivery_purpose`。本任务仅登记 §13 待办，不改 v0.2 技术内容。
  - domain_model：本任务即其修订。
  - openapi / security / test_plan：none（尚未产出或由下游任务覆盖）。
- reason：仅领域模型内部可正确表达既已规定的多目的投递，下游按既有意图对齐，无新增用户行为。

## 功能验收
- **字段/枚举**：`NotificationDelivery` 含 `delivery_purpose enum[candidate_notification, interviewer_confirmation, interviewer_cancellation]`；类图（§2.3）与字段表（§6.12）一致。
- **唯一约束**：`uq_delivery_attempt` = `(event_id, delivery_purpose, channel, event_version, attempt_no)`；手动重发保持 `delivery_purpose` 不变、`attempt_no`+1。
- **目的映射**：§6.12 表明确三类目的的合法 channel 与收件人来源；收件人不新增明文字段。
- **事件/目的解耦**：§5 / §6.11 明确事件类型表达业务事实、`delivery_purpose` 表达投递意图；无 `confirm_mail` 业务事件类型。
- **影响分析**：TASK-DM-003 含 SRS v1.1 / UI v1.0 / architecture v0.2 三份影响分析段落；下游工件正文未被修改（待批准后同步）。
- **不批准**：`docs/baseline.yml` 中 `domain_model.status` 仍为 `review`。
- **架构待办**：architecture.md §13 已登记两项后续修正（Slot 重新物化 / 租约区分未发送与结果未知）。

## 安全与隐私验收
- 候选人收件人沿用 `OwnerContactConfig.candidate_phone_ciphertext` / `OwnerContactConfig.candidate_feishu_open_id_ciphertext`（AES 密文）+ `owner_admin` 的 `User.email`；面试官收件人沿用 `User.email`（经 `Appointment.user_id` 关联）；不新增明文收件人列。
- 密码哈希冲突升级条款沿用 v1.1.4，未改动。

## 性能验收
- 唯一约束宽度 +1 列，对索引体积与写入成本影响可忽略；与既有 `event_version` / `attempt_no` 同序，范围扫描（按 event_id）仍高效。

## 变更预算（change_budget）
- max_files：**5**
  1. docs/design/domain-model.md
  2. tasks/TASK-DM-003.md
  3. docs/baseline.yml
  4. PROJECT_STATE.md
  5. docs/design/architecture.md（仅 §13 待办登记）
- expected_prod_lines：0（设计任务，无生产代码）
- expected_test_lines：0

## 必须运行的测试命令
- 无自动化测试（设计任务）。交付前一致性校验：
  1. `grep "delivery_purpose"` domain-model.md → 类图、§6.12、§5 均出现，且与枚举值一致；
  2. `grep "uq_delivery_attempt"` domain-model.md → 唯一约束含 `delivery_purpose` 且位于 `event_id` 之后、`channel` 之前；
  3. 比对 §6.12 目的映射与 PRD §4.5.1 / P0-4、SRS §3.5/§3.7 的收件人/通道规定，确认一致；
  4. 确认 `docs/baseline.yml` 中 `domain_model.status` 仍为 `review`；
  5. 确认 SRS/UI/architecture 正文未被本任务修改（仅 architecture.md §13 待办登记、下游影响分析在 TASK 单内）。

## 回滚方法
- `git revert` 本任务提交；本任务不产生迁移、不产生代码。

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「允许修改路径」与「已批准的 DB / API / 依赖变更」列明，而不是看变更类型本身。**
- **可继续**：变更已列明且为领域模型修订性质，依据工件（PRD/SRS/用例规约/UI/架构）在 `docs/baseline.yml` 状态已知。
- **必须立即停止并报告**：出现任何未列明的变化，包括——新增/修改其他领域实体、字段、索引或外部依赖（超出 delivery_purpose 列 + uq_delivery_attempt 调整）；重新引入 `confirm_mail` 业务事件类型；新增明文收件人列；修改 SRS/UI/架构正文（除 architecture.md §13 待办登记）；把 `domain_model.status` 改为 `approved`；改动密码哈希冲突升级条款。
- **其余硬停条件**：超出 `change_budget.max_files`（5）→ 拆任务。

## 影响分析（SRS v1.1 / UI v1.0 / architecture v0.2，仅分析不修改下游）

### A. SRS v1.1 影响
- **行为一致性**：SRS §3.5（预约创建→候选人通知 + 面试官确认函）、§3.6（改期→候选人+面试官告知）、§3.7（owner 强制取消→面试官取消告知函）、§3.8（双通道）、§6.2（DeliveryStatus）已规定多目的双线投递，与 `delivery_purpose` 三目的语义**完全一致**，无用户行为冲突。
- **需同步更新的表述（待批准后）**：
  - §6.2 / §4.3 引入 `delivery_purpose` 概念与枚举（candidate_notification / interviewer_confirmation / interviewer_cancellation）；
  - 明确 `NotificationDelivery` 唯一约束含 `delivery_purpose`；
  - 将「面试官确认函/取消告知函」映射为 `interviewer_confirmation` / `interviewer_cancellation` 目的，候选人通知为 `candidate_notification`。
- **结论**：仅文字同步级更新，**不改变用户可观察行为**。

### B. UI 线框 v1.0 影响
- **行为一致性**：A6/A7 失败中心按 `DeliveryStatus` + 退信筛选，`delivery_purpose` 为附加维度，UI 不强制改动即可继续工作。
- **可选增强（非必须）**：未来可在失败中心按 `delivery_purpose` 分组/筛选（如分别展示候选人通知与面试官确认函的失败项）；不在本任务范围，不修改 UI。
- **结论**：impact = none（强制），UI 无需改动。

### C. architecture v0.2 影响
- **需同步更新的技术内容（待批准后，由 TASK-ARCH-002 后续修正或新任务执行）**：
  - §6.3 / §6.5：幂等键由 `H(idempotency_key : channel : event_version)` 调整为含 `delivery_purpose` → `H(idempotency_key : delivery_purpose : channel : event_version)`（稳定幂等键仍**不含 attempt_no**）；
  - §6.7：唯一约束引用由 `(event_id, channel, event_version, attempt_no)` 更新为 `(event_id, delivery_purpose, channel, event_version, attempt_no)`；
  - §4.3 / §4.4：投递创建必须置 `delivery_purpose`（候选人通知 / 面试官确认函 / 面试官取消告知），与事件类型解耦；
  - §13 已登记两项后续修正（Slot 重新物化 / 租约区分未发送与结果未知），待 v1.1.5 批准后执行。
- **结论**：需同步更新，但本任务**不修改** architecture v0.2 技术内容（仅 §13 待办登记）。

## 交付证据（review 草案，**不关闭**）
- commit / PR：448bcac4b4b615a441256bcc79a5f9da97a7577c（G1 快照）
- 修改文件清单：docs/design/domain-model.md / tasks/TASK-DM-003.md / docs/baseline.yml / PROJECT_STATE.md / docs/design/architecture.md（5 个路径，与「允许修改路径」逐一对照一致）
- 测试命令及结果：
  1. `grep "delivery_purpose" domain-model.md` → 类图(200)/§5(412)/§6.12(524,533,535,541,542)/版本注(9)/脚注(645) 均出现，枚举值 `candidate_notification/interviewer_confirmation/interviewer_cancellation` 一致（pass）；
  2. `grep "uq_delivery_attempt" domain-model.md` → 唯一约束 `ON NotificationDelivery(event_id, delivery_purpose, channel, event_version, attempt_no)`，`delivery_purpose` 位于 `event_id` 之后、`channel` 之前（pass）；
  3. §6.12 目的映射表与 PRD §4.5.1/P0-4、SRS §3.5/§3.7 的收件人/通道规定一致（pass）；
  4. `grep "domain_model:" baseline.yml` → `version: "1.1.5", status: review`，未变为 approved（pass）；
  5. `grep "delivery_purpose" SRS.md / ui-wireframe.md` → 无结果（下游正文未被改，符合不修改下游）（pass）。
- lint / typecheck：不适用（设计任务）
- DB 迁移验证：无
- 验收证据：domain-model.md v1.1.5（§1/§2.3/§5/§6.11/§6.12/脚注）：新增 `NotificationDelivery.delivery_purpose` 列 + 唯一约束调整 + 三目的合法 channel/收件人来源映射（收件人不新增明文字段）；§5/§6.11 明确事件类型与投递目的解耦、不重新引入 `confirm_mail`；architecture.md §13 登记两项后续修正待办。baseline.domain_model=1.1.5/review；PROJECT_STATE 同步阶段态与门禁顺序。
- 变更预算实际值：max_files=5，实际 5 文件（domain-model.md / TASK-DM-003.md / baseline.yml / PROJECT_STATE.md / architecture.md 仅 §13），未超预算。
- 未解决风险：
  1. **下游影响待同步（spec_sync=dirty，预期触发 needs impact check，符合意图）**：SRS v1.1 需文字同步级更新（显式 `delivery_purpose` 概念与目的映射 + `uq_active_owner_admin` 约束与单 owner 不变量，不改变用户行为）；architecture v0.2 §6 须纳入 `delivery_purpose`（唯一约束 + 幂等键 + 投递创建置目的）；均待用户批准 v1.1.5 后由相应任务执行。
  2. **面试官改期/会议号更新/主动取消告知均属 MVP（已修正，非未来扩展）**：`appointment_rescheduled → interviewer_confirmation`、`appointment_details_updated → interviewer_confirmation`（会议号更新函）、`appointment_cancelled → interviewer_cancellation`（面试官主动取消告知）均已被三目的既有覆盖范围接纳，属 approved SRS v1.1 MVP 行为，不再列为可后续增补目的枚举。
  3. **单 owner 唯一性（已裁定，方案 A，已收口）**：用户末次裁定 MVP=单候选人个人站点、不引入 `SiteConfig`，采用方案 A——`User.uq_active_owner_admin` 部分唯一索引（`WHERE role='owner_admin' AND deleted_at IS NULL`）+ 三条运行不变量 + `candidate_notification` 收件人解析固定链路（见领域模型 §6.1）。**原 Stop & Report 阻塞已解除**，本草案严格按用户裁定落地、未假设。
- 是否偏离 TASK：否（仅做方案 A 主线修正 + 安全表述修正；未批准领域模型、未修改 SRS/UI 正文、未重新引入 `confirm_mail`、未新增明文收件人、未触动密码哈希冲突升级条款、未进入下游阶段）。
- 规范影响结论：srs=需文字同步级更新（非 none，不改变用户行为）；ui=none；architecture=需同步更新（待批准后）
- spec_sync：dirty（domain_model 升 1.1.5，下游 SRS/UI/architecture 的 based_on/引用仍为 1.1.4，**预期触发 needs impact check**；按用户指令暂不修改下游，待批准后同步）
- verified_commit：4c895e9f0900854d55cabff1958bdd4446b324b5（G5 最终内容评审包，非自指；G1=448bcac、G3=e41c0a1 为前置快照）
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响已处理（下游 impact review 已执行并同步）；③ spec_sync = clean；④ verified_commit 已记录真实 sha。
  **本任务保持 review，待用户独立评审批准 domain_model v1.1.5 后方可关闭。AI 不得代签 approved。**

## 补正记录（v1.1.5 补正内容评审包，2026-08-08，指令：修实质实体/字段错误）
- 触发：用户对 v1.1.5 审查后指出会误导实现的实体/字段错误；指令只修实质问题、不建 TASK-GOV、不追修提交描述、不改下游工件、不批准、不进安全设计。
- 本次修正（均落在 domain-model.md v1.1.5 review 草案内，未动下游）：
  1. **面试官收件人来源修正**：删除虚构的 `Appointment.interview_id → Interview.interviewer_id → InterviewerProfile.registered_email`；改为既有 `Appointment.user_id → User.id → User.email`（`InterviewerProfile` 仅有 `display_name`、无 `registered_email`；`Interview` 实体不存在）。
  2. **候选人收件人来源（已固定）**：手机=`OwnerContactConfig.candidate_phone_ciphertext`（沿用）；邮箱=`owner_admin` 的 `User.email`；解析链路固定为「活跃 owner_admin User（由 `uq_active_owner_admin` 唯一确定）→ User.email → 同 user_id 的 OwnerContactConfig → candidate_phone_ciphertext / candidate_feishu_open_id_ciphertext」。`User.email` 为既有账号邮箱字段、非 AES 密文、由访问控制保护（不再称"密文存取"）。
  3. **候选人飞书接收标识（原无领域字段）**：新增 `OwnerContactConfig.candidate_feishu_open_id_ciphertext`（AES 密文），作为**显式领域模型变更**列出（指令 item 3 授权）。
  4. **完整事件→目的映射**：`candidate_notification`=created/rescheduled/cancelled/reminder_due；`interviewer_confirmation`=created/rescheduled/details_updated；`interviewer_cancellation`=cancelled。
  5. **同事件多目的并发投递**：`appointment_cancelled` 必须同时产生 候选人 `candidate_notification`（email+feishu）+ 面试官 `interviewer_cancellation`（email）；面试官改期确认函/会议号更新函/主动取消告知函均属 SRS v1.1 MVP 行为，非未来扩展。
- **单 owner 决议（已裁定方案 A）**：用户末次指令裁定 MVP=单候选人个人站点、不引入 SiteConfig，采用方案 A——`User` 上加 `uq_active_owner_admin` 部分唯一索引（`WHERE role='owner_admin' AND deleted_at IS NULL`），确立三条运行不变量，`candidate_notification` 收件人解析链路完全确定。**原 Stop & Report 阻塞已解除**，本草案严格按用户裁定落地、未假设。
- 补正提交（G3）：e41c0a12dfd5b67b668b418c3cdd39def708c79f
- 修改文件清单（补正包）：docs/design/domain-model.md / tasks/TASK-DM-003.md（2 个路径，均在「允许修改路径」内，未超 change_budget max_files=5）
- 是否偏离 TASK：否（补正在用户本指令授权范围内；domain_model 仍 review、未批准、未动下游、未进安全设计；新增字段/索引已由指令显式授权，不触发越界硬停）
- verified_commit（补正包）：e41c0a12dfd5b67b668b418c3cdd39def708c79f
- **最终内容评审包（方案 A 收口，待提交）**：将把 `uq_active_owner_admin` 索引 + 三条运行不变量 + `User.email` 安全表述修正纳入 v1.1.5 review 草案，并关闭 Stop & Report 阻塞记录；domain_model 仍 review、未批准、未动下游、未进安全设计。

## 关联
- 上游任务：TASK-DM-002（v1.1.4 approved，锚点 `f537296`；本任务 v1.1.5 取代其正文，v1.1.4 批准事实保留为历史）
- 下游同步（待用户批准 v1.1.5 后）：SRS v1.1 impact review（TASK-SRS-*）、UI v1.0（如需）、architecture v0.2 修正（TASK-ARCH-002 后续或新任务）
- Change Request：无（密码哈希冲突升级条款沿用 v1.1.4，未触动；delivery_purpose 为最小必要领域模型修订，由本指令授权）
- 测试任务：无（设计）
