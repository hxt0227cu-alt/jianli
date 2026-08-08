# TASK-UI-002 UI 线框内容修正（承载 TASK-UI-IMPACT-001 的 MP-1 + 吸收 SRS v1.1 退信要求）

> 修正 UI 线框中经影响评审确认的内容缺口，并吸收已批准 SRS v1.1 的退信(Bounce) 用户可观察行为；不扩需求、不批准 ui_wireframe、不推进下游。按 TASK-TEMPLATE 补全（TASK-GOV-004 校正；本回合更新依据为已批准 SRS v1.1）。本任务**已关闭（2026-08-08）**，待用户评审实际线框后授权批准 UI。

## 任务类型
- design_correction

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / **SRS 1.1（approved @ `00e125c`）** / AI 治理 1.0.1（取自 docs/baseline.yml）
- 基线 commit：00e125c（SRS v1.1 approved 锚点 / approval_commit；v1.0 approved 快照冻结于 26ae844）；领域模型 v1.1.4 批准锚点 f537296

## 精确规范引用（AI 只读取这些章节）
- SRS v1.1 §6.2（状态模型，DeliveryStatus 枚举：queued/sending/succeeded/failed/retry_scheduled/dead_letter；bounced 仅存 channel_metadata，不属本枚举；手动重发=新建尝试记录）
- SRS v1.1 §4.3（通信 / 通知接口行为，手动重发 = 新建 NotificationDelivery 尝试记录，幂等键含新 event_version；§4.2 仅为软件接口概述；退信(Bounce) 行为契约）
- SRS v1.1 §3.8（退信(Bounce) 处理：记录 channel_metadata.bounced_at/bounce_reason、飞书告警候选人 + 后台高优先级告警、不回滚预约、失败中心展示/筛选/手动重发）
- SRS v1.1 §3.9（管理后台失败中心含退信记录展示与按通道/状态筛选）
- 领域模型 v1.1.4 §5（状态机规范，DeliveryStatus 枚举来源；channel_metadata.bounced_at/bounce_reason 邮件分支）
- TASK-UI-IMPACT-001（MP-1 精确修改点来源）
- SRS v1.1 §5.3（隐私）/ §7（权限与角色矩阵，admin 后台只读应急视图权限）— 支撑安全与隐私验收

## 需求来源
- UC-21（通知失败中心手动重发 / 退信展示筛选）→ R5（管理后台能力）、R21（飞书同步失败告警/通知失败）、**R26（退信记录/告警/不回滚预约/手动重发）**；SRS §6.2 / §4.3 / §3.8 / §3.9 为 DeliveryStatus 与退信行为依据
- UC-23（后台只读应急视图）→ R14a（A7 应急视图来源）

## 目标
修正 A6/A7 通知失败中心状态列，补充失败处理相关状态 failed/retry_scheduled/dead_letter（与 SRS §6.2 枚举一致）；并吸收已批准 SRS v1.1 的退信(Bounce) 行为：A6 展示退信记录及 bounced_at/bounce_reason、支持按通道与状态筛选、显示退信告警状态、手动重发新建 NotificationDelivery 尝试；bounced 不加入 DeliveryStatus。queued/sending/succeeded 是否进入失败中心 SRS 未规定，本任务不裁定。

## 非目标（明确排除）
- 不新增页面/组件、不改语义色、不改限频阈值、不扩需求
- 不批准 ui_wireframe（baseline status 仍 pending）
- 不改动 SRS / 领域模型（仅引用已批准 v1.1）

## 授权范围（允许修改路径）
- docs/design/ui-wireframe.md       # A6/A7 通知失败中心状态列 + 退信(Bounce) 展示/筛选/告警/重发同步（MP-1 + SRS v1.1 吸收）
- tasks/TASK-UI-002.md              # 本任务单
- tasks/TASK-UI-001.md              # 修正完成后回填交付证据 / 标注内容缺口已闭合

## 禁止修改路径（越界即停）
- docs/baseline.yml                 # 不改 ui_wireframe.status（保持 pending，待用户评审实际线框）
- docs/requirements/SRS.md / 领域模型 # 仅引用不改
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 已批准的 DB / API / 依赖变更
- 无（纯线框文案修正，无 schema / API / 依赖变更）

## 规范影响评估（spec impact）
- behavior_change：false（UI 设计呈现发生修正，但不改变 approved SRS v1.1 定义的行为；属于下游设计纠偏以符合已批准规范，无需修改 SRS；手动重发与退信行为以 SRS §6.2 / §4.3 / §3.8 为唯一依据，UI 不新增状态限制）
- affected_specs：
  - srs：none（SRS v1.1 已含退信行为且 approved）
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：纯 UI 线框文案补全，与已批准 SRS v1.1 §6.2 / §4.3 / §3.8 / §3.9 / 领域模型 §5 完全一致，不改变行为
- 分类：文案补全（行为未变）→ 不需改 SRS；更新交付证据即可

## 精确修改点（来自 TASK-UI-IMPACT-001 / MP-1 + 已批准 SRS v1.1 退信要求）
- **MP-1（A6 通知失败中心）**：
  - 状态列由单列"failed"扩展为区分 failed（可重试）与 dead_letter（终态死信，人工介入）并呈现 retry_scheduled（重试中）；与 SRS §6.2 枚举一致。
  - **退信(Bounce) 吸收（SRS v1.1 §3.8/§3.9/§4.3）**：列表新增退信记录行，展示 `bounced_at` / `bounce_reason`（邮件通道，来自 channel_metadata，不混入 DeliveryStatus 枚举）；支持按通道（飞书/邮箱）与状态（含退信）筛选；退信行显示告警状态（飞书候选人告警 + 后台高优先级告警）；手动重发按钮对失败/退信记录点击后创建新 NotificationDelivery 尝试记录（`attempt_no`+1，幂等键含新 `event_version`，version+1）。
  - A7 只读应急视图"通知失败列"同理涵盖 dead_letter 标红，并可呈现退信告警状态。
  - 范围限定：仅 A6/A7 状态列与退信展示/筛选/告警/重发文案；不新增页面、不改语义色、不改限频阈值、不扩需求。

## 功能验收
- 前置条件：ui-wireframe.md 处于可编辑态（status=pending，待用户评审）
- 成功：
  - A6 状态列呈现 failed / dead_letter / retry_scheduled 三态，文案与 SRS §6.2 枚举一致；
  - A6 展示退信记录 `bounced_at` / `bounce_reason`，支持按通道与状态筛选，显示退信告警状态；
  - 手动重发（失败/退信）点击后创建新通知投递尝试记录（线框不定义手动重发资格，仅记录"手动重发会新建 NotificationDelivery 尝试"；可操作状态由后续获批规范/API 契约定义，UI 任务不得自行增加规则）；
  - A7"通知失败列"含 dead_letter 标红并可呈现退信告警状态。
- 异常路径：手动重发按钮点击后创建新通知投递尝试记录（线框不定义手动重发资格，仅记录"手动重发会新建 NotificationDelivery 尝试"；可操作状态由后续获批规范/API 契约定义，UI 任务不得自行增加规则）

## 安全与隐私验收
- 通知内容含面试官/候选人隐私字段时遵循 SRS §5.3 隐私约束（红格对他人不可见可识别信息；敏感操作入审计并脱敏）与 §7 权限矩阵（失败中心仅 admin 后台可见、不暴露未授权隐私字段）；R9/R16 为历史输入来源，不单独作为验收依据。

## 性能验收
- N/A（本任务为静态低保真线框文案修正，不产生新的运行时性能要求）

## 变更预算（change_budget）
- max_files：3（ui-wireframe.md + TASK-UI-002.md + TASK-UI-001.md 回填）
- expected_prod_lines：~25（线框文案新增/修改行，含退信展示/筛选/告警/重发）
- expected_test_lines：0（无代码）

## 必须运行的测试命令
- 全仓 Grep 复核 A6/A7 状态列含 dead_letter / retry_scheduled，且与 SRS §6.2 枚举一致；复核含退信记录 bounced_at/bounce_reason 展示、按通道与状态筛选、退信告警状态、手动重发新建 NotificationDelivery 尝试；复核无"bounced 属 DeliveryStatus"误述、无"UI 不拦截任何状态"、无"N≤200"

## 回滚方法
- `git revert <本任务提交>` 或还原 ui-wireframe.md A6/A7 状态列与退信文案至修改前；不影响 baseline 状态

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「已批准的 DB / API / 依赖变更」中列明，而不是看变更类型本身。**
- 可继续：变更已在「允许修改路径」列明，且依据工件（SRS v1.1 §6.2 / §4.3 / §3.8 / §3.9 / 领域模型 §5）在 baseline 为 approved
- 必须立即停止并报告（不得自行决定）：出现任何未列明变化，包括但不限于
  - 新增/修改页面、组件、语义色、限频阈值
  - 超出 MP-1 已列范围（A6/A7 仅 failed/retry_scheduled/dead_letter 三态 + 退信展示/筛选/告警/重发）的变更
  - 现有线框与领域模型 `DeliveryStatus` 不一致，且该不一致**超出 MP-1 已列范围**时停止；MP-1 范围内 A6/A7 不一致属本任务目标，不触发硬停
- 其余硬停：超出 change_budget（max_files=3）→ 拆任务

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：266a7733bee57861c4f678e763dd4889b134d799（ui-wireframe.md A6/A7 同步提交 / 本任务 verified_commit=G1）
- 修改文件清单（按路径逐条计数，与「允许修改路径」对照）：
  1. docs/design/ui-wireframe.md — A6/A7 失败状态三态 + 退信(Bounce) 展示/筛选/告警/重发同步（MP-1 + SRS v1.1 吸收）
  2. tasks/TASK-UI-002.md — 本任务单（范围更新 + 关闭证据）
  3. tasks/TASK-UI-001.md — 标注内容缺口已闭合
- 测试命令及结果：全仓 Grep 复核 A6/A7 含 `dead_letter`/`retry_scheduled`、`bounced_at`/`bounce_reason` 展示、按通道与状态筛选、退信告警状态、手动重发新建 NotificationDelivery 尝试 → **pass**（9 处匹配，见 ui-wireframe.md L6/L275/L276/L314/L318–L323）
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：ui-wireframe.md A6（状态列 failed/retry_scheduled/dead_letter + 退信行 bounced_at/bounce_reason + 按通道与状态筛选 + 退信告警 + 手动重发新建 NotificationDelivery 尝试）、A7（通知失败列含 dead_letter 标红 + 退信列显 bounced_at/bounce_reason 与告警状态）；语义色与 SRS §6.2 一致
- 变更预算实际值：max_files=3，实际 3 文件，未超预算
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none（纯设计修正，不改行为；SRS v1.1 已含退信且 approved）
- spec_sync：clean
- verified_commit：266a7733bee57861c4f678e763dd4889b134d799（UI 同步交付快照 G1；本任务关闭提交为 G2 纯证据回填，不循环指向自身）

## 关闭门禁（四条件全满足方可关闭）
① 测试通过（Grep 复核 A6/A7 枚举一致 + 退信展示/筛选/告警/重发）；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录真实 sha。任一不满足→不得关闭。

## 关联
- 上游：TASK-UI-IMPACT-001（影响评审，MP-1 来源）；SRS v1.1（已批准，退信行为来源）
- 下游：用户评审实际线框 → 授权 baseline.ui_wireframe.status→approved → 架构/ADR
