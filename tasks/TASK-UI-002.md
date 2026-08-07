# TASK-UI-002 UI 线框内容修正（承载 TASK-UI-IMPACT-001 的 MP-1）

> 仅修正 UI 线框中经影响评审确认的内容缺口；不扩需求、不批准 ui_wireframe、不推进下游。按 TASK-TEMPLATE 补全（TASK-GOV-004 校正）。本任务**未执行、未关闭**，待用户评审实际线框后授权。

## 任务类型
- design_correction

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.0（approved）/ AI 治理 1.0.1（取自 `docs/baseline.yml`）
- 基线 commit：26ae844（SRS v1.0 approved 锚点）+ 06798a2（TASK-SRS-001 关闭快照 / verified_commit）；领域模型 v1.1.4 批准锚点 f537296

## 精确规范引用（AI 只读取这些章节）
- SRS v1.0 §6.2（状态模型，`DeliveryStatus` 枚举：`queued`/`sending`/`succeeded`/`failed`/`retry_scheduled`/`dead_letter`；手动重发=新建尝试记录）
- SRS v1.0 §4.2（软件接口，手动重发幂等键含新 `event_version`）
- 领域模型 v1.1.4 §5（状态机规范，`DeliveryStatus` 枚举来源）
- TASK-UI-IMPACT-001（MP-1 精确修改点来源）

## 需求来源
- UC-21（通知失败中心手动重发）→ R5（管理后台能力）、R21（飞书同步失败告警/通知失败）；SRS §6.2 / §4.2 为 DeliveryStatus 与手动重发行为依据
- UC-23（后台只读应急视图）→ R14a（A7 应急视图来源）

## 目标
修正 A6/A7 通知失败中心状态枚举，使其与 SRS §6.2 / 领域模型 §5 的 `DeliveryStatus`（queued/sending/succeeded/failed/retry_scheduled/dead_letter）一致。

## 非目标（明确排除）
- 不新增页面/组件、不改语义色、不改限频阈值、不扩需求
- 不批准 ui_wireframe（baseline status 仍 pending）
- 不补"退信(bounce)"需求（仅登记待裁定，见「待裁定项」）

## 授权范围（允许修改路径）
- docs/design/ui-wireframe.md       # 仅 A6/A7 通知失败中心状态列补全（MP-1）
- tasks/TASK-UI-002.md              # 本任务单
- tasks/TASK-UI-001.md              # 修正完成后回填交付证据 / 标注内容缺口已闭合

## 禁止修改路径（越界即停）
- docs/baseline.yml                 # 不改 ui_wireframe.status（保持 pending，待用户评审实际线框）
- docs/requirements/SRS.md / 领域模型 # 仅引用不改
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 已批准的 DB / API / 依赖变更
- 无（纯线框文案修正，无 schema / API / 依赖变更）

## 规范影响评估（spec impact）
- behavior_change：false（仅补全状态列文案，不改变用户可观察行为；手动重发行为以 SRS §6.2 / §4.2 为唯一依据，UI 不新增状态限制）
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：纯 UI 线框文案补全，与已批准 SRS §6.2 / 领域模型 §5 完全一致，不改变行为；退信(bounce) 不在本任务（见待裁定项）
- 分类：文案补全（行为未变）→ 不需改 SRS；更新交付证据即可

## 精确修改点（来自 TASK-UI-IMPACT-001 / MP-1）
- **MP-1**：A6 通知失败中心列表"状态"列由单列"failed"扩展为区分 `failed`（可重试）与 `dead_letter`（终态死信，人工介入）并呈现 `retry_scheduled`（重试中）。手动重发行为以 SRS §6.2 / §4.2 为准：点击创建新 NotificationDelivery 尝试记录（SRS 未限定可操作状态，UI 不得自新增状态限制）。A7 只读应急视图"通知失败列"同理涵盖 dead_letter 标红。
  - 范围限定：仅 A6/A7 状态列文案与列定义；不新增页面、不改语义色、不改限频阈值、不扩需求。

## 功能验收
- 前置条件：ui-wireframe.md 处于可编辑态（status=pending，待用户评审）
- 成功：A6 状态列呈现 `failed` / `dead_letter` / `retry_scheduled` 三态，文案与 SRS §6.2 枚举一致；A7"通知失败列"含 dead_letter 标红
- 异常路径：手动重发按钮点击后创建新通知投递尝试记录（不限定当前状态；UI 不拦截任何状态）

## 安全与隐私验收
- 通知内容含面试官/候选人隐私字段时遵循 R9/R16 遮挡；失败中心不暴露未授权隐私字段

## 性能验收
- A6 列表渲染：N≤200 条失败记录时无明显卡顿（静态线框文案，无量化硬指标；以可读为准）

## 变更预算（change_budget）
- max_files：3（ui-wireframe.md + TASK-UI-002.md + TASK-UI-001.md 回填）
- expected_prod_lines：~15（线框文案新增/修改行）
- expected_test_lines：0（无代码）

## 必须运行的测试命令
- 全仓 Grep 复核 A6/A7 状态列含 dead_letter / retry_scheduled，且与 SRS §6.2 枚举一致；复核无残留"手动重发仅对 failed/dead_letter"限制表述

## 回滚方法
- `git revert <本任务提交>` 或还原 ui-wireframe.md A6/A7 状态列文案至修改前；不影响 baseline 状态

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「已批准的 DB / API / 依赖变更」中列明，而不是看变更类型本身。**
- 可继续：变更已在「允许修改路径」列明，且依据工件（SRS §6.2 / 领域模型 §5）在 baseline 为 approved
- 必须立即停止并报告（不得自行决定）：出现任何未列明变化，包括但不限于
  - 新增/修改页面、组件、语义色、限频阈值
  - 新增退信(bounce) 展示/筛选/重发 UI（属「待裁定项」，须先走 SRS 修正 + 影响评审，不得在本任务补）
  - 现有线框与领域模型 `DeliveryStatus` 不一致
- 其余硬停：超出 change_budget（max_files=3）→ 拆任务

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<回填>
- 修改文件清单：<回填，与「允许修改路径」对照>
- 测试命令及结果：<命令> → <pass/fail；Grep 复核 A6/A7 含 dead_letter/retry_scheduled>
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：<截图/线框片段，敏感字段脱敏>
- 变更预算实际值：<max_files 实际 / 行数，与预算对照>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否>
- 规范影响结论：none（纯设计修正，不改行为）
- spec_sync：clean
- verified_commit：<回填>

## 关闭门禁（四条件全满足方可关闭）
① 测试通过（Grep 复核 A6/A7 枚举一致）；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录真实 sha。任一不满足→不得关闭。

## 待裁定项（不得在本任务补需求）
- **退信(bounce)**：领域模型将 `bounced_at` / `bounce_reason` 置于 `channel_metadata`；已批准 SRS 未明确失败中心的退信展示 / 筛选 / 重发行为。
- 待裁定：SRS 遗漏 or 明确不纳入。
- 若需保留 UC-21 退信能力 → **必须先走 SRS 修正（Change Request）+ 影响评审**，再开 UI 任务；本任务及 TASK-UI-IMPACT-001 均不直接补退信需求。

## 关联
- 上游：TASK-UI-IMPACT-001（影响评审，MP-1 来源）
- 下游：用户评审实际线框 → 授权 baseline.ui_wireframe.status→approved → 架构/ADR
