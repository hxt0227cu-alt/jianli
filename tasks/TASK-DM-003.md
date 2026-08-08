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
- 不新增冗余明文收件人字段；收件人沿用既有密文（`candidate_*` / `InterviewerProfile.registered_email`），发送时按访问控制解密。
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
- **本任务即领域模型修订本身**：在领域模型 v1.1.4 已批准范围内，**新增一个字段** `NotificationDelivery.delivery_purpose`（`enum[candidate_notification, interviewer_confirmation, interviewer_cancellation]`）并**调整一个唯一索引** `uq_delivery_attempt` 由 `(event_id, channel, event_version, attempt_no)` 改为 `(event_id, delivery_purpose, channel, event_version, attempt_no)`。
- 此为修复实现阻塞的**最小必要变更**，由用户本指令明确授权；**未新增**任何实体 / 表 / 其他字段 / 外部依赖。
- **不触发 Stop & Report**：变更范围完全由用户本指令界定（新增 delivery_purpose 列 + 唯一约束调整），属于领域模型自身修订，未越界到 SRS/UI/架构正文、未引入新实体或外部依赖。

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
- 收件人沿用既有密文字段（`candidate_*` / `InterviewerProfile.registered_email`），发送时按访问控制解密；不新增明文收件人列。
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
- commit / PR：<G1 待回填>
- 修改文件清单：docs/design/domain-model.md / tasks/TASK-DM-003.md / docs/baseline.yml / PROJECT_STATE.md / docs/design/architecture.md（5 个路径，与「允许修改路径」逐一对照一致）
- 测试命令及结果：<待回填>
- lint / typecheck：不适用（设计任务）
- DB 迁移验证：无
- 验收证据：<待回填>
- 变更预算实际值：<待回填>
- 未解决风险：<待回填>
- 是否偏离 TASK：<待回填>
- 规范影响结论：srs=需文字同步级更新（非 none，不改变用户行为）；ui=none；architecture=需同步更新（待批准后）
- spec_sync：dirty（domain_model 升 1.1.5，下游 SRS/UI/architecture 的 based_on/引用仍为 1.1.4，**预期触发 needs impact check**；按用户指令暂不修改下游，待批准后同步）
- verified_commit：<G1 待回填>
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响已处理（下游 impact review 已执行并同步）；③ spec_sync = clean；④ verified_commit 已记录真实 sha。
  **本任务保持 review，待用户独立评审批准 domain_model v1.1.5 后方可关闭。AI 不得代签 approved。**

## 关联
- 上游任务：TASK-DM-002（v1.1.4 approved，锚点 `f537296`；本任务 v1.1.5 取代其正文，v1.1.4 批准事实保留为历史）
- 下游同步（待用户批准 v1.1.5 后）：SRS v1.1 impact review（TASK-SRS-*）、UI v1.0（如需）、architecture v0.2 修正（TASK-ARCH-002 后续或新任务）
- Change Request：无（密码哈希冲突升级条款沿用 v1.1.4，未触动；delivery_purpose 为最小必要领域模型修订，由本指令授权）
- 测试任务：无（设计）
