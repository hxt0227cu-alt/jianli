# TASK-GOV-004 UI 影响评审治理账目校正

> 向前治理修正：校正 TASK-UI-IMPACT-001 的 change_budget 账目与 verified_commit 缺陷，并按 TASK-TEMPLATE 补全 TASK-UI-002；不重写历史、不批准 UI、不改 baseline、暂不修改 ui-wireframe.md。

## 任务类型
- governance

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.0（approved）/ AI 治理 1.0.1（取自 `docs/baseline.yml`）
- 基线 commit：26ae844（SRS v1.0 approved 锚点；TASK-SRS-001 verified_commit=06798a2）

## 授权范围（允许修改路径）
- tasks/TASK-UI-IMPACT-001.md   # 校正 change_budget 账目 + verified_commit 缺陷 + 退信待裁定注记
- tasks/TASK-UI-002.md          # 按 TASK-TEMPLATE 补全 + 删除 MP-1 手动重发状态限制 + 退信待裁定登记
- tasks/TASK-GOV-004.md         # 本任务单

## 禁止修改路径（越界即停）
- docs/baseline.yml             # 不改任何 status（ui_wireframe 保持 pending）
- docs/requirements/SRS.md / docs/design/domain-model.md  # 仅引用不改
- docs/design/ui-wireframe.md   # 本轮不修改（待用户复核）
- PROJECT_STATE.md              # 已在 TASK-UI-IMPACT-001 允许路径内，无需回退（step 6）
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
校正 TASK-UI-IMPACT-001 的两处治理缺陷（change_budget 无依据、verified_commit 指向占位/自指提交），并将 TASK-UI-002 补全为符合 TASK-TEMPLATE 的可执行（待授权）任务单。

## 非目标
- 不执行 TASK-UI-002（不修改 ui-wireframe.md）
- 不批准 ui_wireframe
- 不推进架构/安全/OpenAPI/测试计划/编码
- 不补"退信"需求（仅登记待裁定）

## 精确规范引用
- 已批准 SRS v1.0 §6.2（状态模型 / `DeliveryStatus` 枚举 / 手动重发=新建尝试记录）、§4.2（软件接口，手动重发幂等键）
- 领域模型 v1.1.4 §5（状态机规范，`DeliveryStatus` 枚举来源；`bounced_at`/`bounce_reason` 置于 `channel_metadata`）
- TASK-TEMPLATE.md（任务单骨架与关闭门禁）
- AGENTS.md §2（强制停止条件）、§9（规范影响评估）

## 需求来源
- UC-21（通知失败中心手动重发）→ R5、R21；SRS §6.2 / §4.2 为 DeliveryStatus 与手动重发行为依据
- UC-23（后台只读应急视图）→ R14a（退信待裁定登记非本任务范围）

## 修正内容（step 1–5）

### 1) TASK-UI-IMPACT-001 change_budget 账目校正（step 1）
- 原记录"变更预算实际值：实际 5 文件，未超预算" + "是否偏离 TASK：否" 无依据——该任务启动时**未声明 change_budget（无 max_files）**。
- 改为："变更预算实际值：未预设 change_budget（任务启动时未声明 max_files），无法判定是否超预算；实际改动 5 路径，但无预算基准，故不得宣称"未超预算""。
- "是否偏离 TASK"保留范围层面"否"（全部改动在授权 5 项路径内），但明确 change_budget 层面无法判定。
- **不得事后补 max_files=5 并宣称原任务未超预算**。

### 2) TASK-UI-IMPACT-001 verified_commit 校正（step 2）
- 原 verified_commit=`a2ea98d…`：该提交中 closing 证据（verified_commit 字段）本身是占位/自指，不能称为完整关闭提交；`da5fce7` 虽回填但仍将 verified_commit 指向 a2ea98d，未形成有效完整快照。
- 按防自引用流程：本任务 G1 提交即"完整验证快照"（含已校正 TASK-UI-IMPACT-001 全部 closing 证据 + TASK-UI-002 补全），G2 纯证据提交回填其 SHA 为 verified_commit。
- 历史保留：`a2ea98d` / `da5fce7` 提交保留于 Git 历史、不重写、不删除；仅 verified_commit 锚点改指向 G1。

### 3) TASK-UI-002 按 TASK-TEMPLATE 补全（step 3）
- 补齐：基线版本与 commit、精确规范引用、需求来源、功能/安全隐私/性能验收、回滚、强制停止条件、完整交付证据骨架与四条件关闭门禁；保持 ui_wireframe=pending。

### 4) 删除 MP-1 手动重发状态限制（step 4）
- TASK-UI-IMPACT-001 / TASK-UI-002 中"手动重发仅对 failed/dead_letter"限制删除。已批准 SRS §6.2 仅规定手动重发新建 NotificationDelivery 尝试、未限定可操作状态；UI 不得自行新增状态限制。

### 5) 退信(bounce) 单独登记待裁定（step 5）
- 领域模型将 `bounced_at`/`bounce_reason` 置于 `channel_metadata`；已批准 SRS 未明确失败中心的退信展示/筛选/重发行为。
- 待裁定：SRS 遗漏 or 明确不纳入。若需保留 UC-21 退信能力 → 必须先走 SRS 修正（Change Request）+ 影响评审，再开 UI 任务。本任务 / TASK-UI-002 均不直接补退信需求。

## 变更预算（change_budget）
- max_files：3（TASK-UI-IMPACT-001.md + TASK-UI-002.md + TASK-GOV-004.md）
- expected_prod_lines：~70（纯文档/任务单文案）
- expected_test_lines：0

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：56669828de6a7dc9ba9a4a93a273c221efee76a4（TASK-GOV-004 被验证的交付物快照 / 本任务 verified_commit；f2cfb88 为纯证据回填/关闭提交）
- 修改文件清单（按路径逐条计数）：
  1. tasks/TASK-GOV-004.md — 本任务单（新建）
  2. tasks/TASK-UI-IMPACT-001.md — change_budget 账目校正 + verified_commit 占位 + 退信待裁定注记
  3. tasks/TASK-UI-002.md — TASK-TEMPLATE 补全 + 删除 MP-1 限制 + 退信待裁定登记
- 测试命令及结果：Grep 复核 TASK-UI-IMPACT-001/TASK-UI-002 中无残留"未超预算"/"手动重发仅对 failed"；`a2ea98d`/`da5fce7` 仅作为历史保留注记出现
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：无（纯治理/文档校正）
- 变更预算实际值：max_files=3，实际 3 文件，未超预算
- 未解决风险：无（范围内已闭环）；退信待裁定为范围外开放项，不阻塞本治理任务
- 是否偏离 TASK：否（全部在授权 3 项内）
- 规范影响结论：none（纯治理/文档校正，不改规范）
- spec_sync：clean
- verified_commit：56669828de6a7dc9ba9a4a93a273c221efee76a4（TASK-GOV-004 被验证的交付物快照 / G1）

## 关闭结论
任务于校正完成后关闭。关闭门禁四条件复核：① 测试通过（Grep 复核无残留错误表述）；② 规范影响 none；③ spec_sync=clean；④ verified_commit=56669828de6a7dc9ba9a4a93a273c221efee76a4（被验证的交付物快照）。状态：Closed。

## 锚点语义（防混淆，校正于 TASK-GOV-005）
- `56669828de6a7dc9ba9a4a93a273c221efee76a4`（5666982）= **被验证的交付物快照**（G1）；**不是关闭提交**（f2cfb88 才是纯证据回填/关闭提交），不含"全部 closing 证据"表述。
- `f2cfb88…`（f2cfb88）= **纯证据回填 / 任务关闭提交**（G2）：仅将 verified_commit 回填为 5666982，不承载新交付物。
- 不得为闭合重新生成指向自身的循环锚点；5666982 与 f2cfb88 各司其职、保留历史。

## 关联
- 上游：TASK-UI-IMPACT-001（被校正对象）/ TASK-UI-002（被补全对象）
- 下游：用户复核 TASK-UI-002 → 授权执行 → 批准 ui_wireframe → 架构/ADR
