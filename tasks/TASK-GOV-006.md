# TASK-GOV-006 现有账目收口（TASK-UI-002 硬停/规范影响/锚点语义/验证锚点/规范引用）

> 向前治理修正：收口 TASK-UI-002 与既有治理任务的账目表述；不重写历史、不批准 UI、不改 baseline（ui_wireframe 保持 pending）、不修改 ui-wireframe.md、不推进架构。

## 任务类型
- governance

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.0（approved）/ AI 治理 1.0.1
- 基线 commit：26ae844（SRS v1.0 approved）；领域模型 v1.1.4 批准锚点 f537296；TASK-GOV-004 快照 5666982 / 关闭提交 f2cfb88；TASK-GOV-005 快照 80e5bf3 / 关闭提交 5f472a6

## 授权范围（允许修改路径）
- tasks/TASK-UI-002.md          # 硬停条件 + 规范影响评估 + 精确规范引用补 §5.3/§7 + 安全隐私验收
- tasks/TASK-GOV-004.md         # 锚点语义校正（第 72/86/92 行）
- tasks/TASK-GOV-005.md         # 锚点语义校正（第 47 行）
- PROJECT_STATE.md              # 最新验证锚点补入 80e5bf3、06798a2 降为历史 SRS 锚点
- tasks/TASK-GOV-006.md         # 本任务单

## 禁止修改路径（越界即停）
- docs/baseline.yml             # 不改任何 status（ui_wireframe 保持 pending；SRS 由 TASK-SRS-002 独立处理）
- docs/requirements/SRS.md / docs/design/domain-model.md  # 仅引用不改
- docs/design/ui-wireframe.md   # 本轮不修改（待 TASK-UI-002 授权后）
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
收口现有治理账目：① TASK-UI-002 硬停条件不再因任务目标（A6/A7 已知不一致）自我硬停；② 规范影响评估改为"下游设计纠偏、不改 approved SRS 行为、无需改 SRS"，删除"不改变用户可观察行为"；③ 统一 TASK-GOV-004/TASK-GOV-005 锚点语义（5666982=被验证交付物快照、f2cfb88=证据回填/关闭提交）；④ PROJECT_STATE 最新验证锚点补入 80e5bf3；⑤ TASK-UI-002 精确规范引用补入 SRS §5.3/§7 以支撑安全隐私验收。

## 非目标
- 不执行 TASK-UI-002（不修改 ui-wireframe.md）
- 不批准 ui_wireframe
- 不推进架构/安全/OpenAPI/测试计划/编码
- 不处理退信规范遗漏（由独立 TASK-SRS-002 处理）

## 精确规范引用
- TASK-TEMPLATE.md（任务单骨架与关闭门禁）
- AGENTS.md §2（强制停止条件）、§9（规范影响评估）
- 已批准 SRS v1.0 §5.3（隐私）/ §7（权限矩阵）/ §6.2（状态模型）/ §4.3（通知接口行为）

## 修正内容（step 1–5）

### 1) TASK-UI-002 硬停条件校正（step 1）
- 原"必须立即停止"列含"现有线框与领域模型 `DeliveryStatus` 不一致"——该表述会使任务因已知的 A6/A7 不一致（恰为本任务目标）而启动即自我硬停。
- 改为："发现 MP-1 已列范围之外的 `DeliveryStatus` 不一致时停止"（MP-1 范围内 A6/A7 仅 failed/retry_scheduled/dead_letter 三态呈现属本任务目标，不触发硬停）。

### 2) TASK-UI-002 规范影响评估校正（step 2）
- behavior_change 描述改为："UI 设计呈现发生修正，但不改变 approved SRS 定义的行为；属于下游设计纠偏以符合既有规范，无需修改 SRS"；删除"不改变用户可观察行为"。

### 3) 锚点语义统一（step 3，TASK-GOV-004 第 72/86/92 行 + TASK-GOV-005 第 47 行）
- 5666982 = **被验证的交付物快照**（G1）；**不是关闭提交、不是关闭快照、不含全部 closing 证据**。
- f2cfb88 = **纯证据回填 / 任务关闭提交**（G2），仅回填 verified_commit、不承载新交付物。
- 删除上述行中"关闭提交/关闭快照/含…全部 closing 证据"等混淆表述。

### 4) PROJECT_STATE 最新验证锚点补入 80e5bf3（step 4）
- 按"末条为最新"声明，新增 80e5bf3 为最新验证锚点（TASK-GOV-005 收口链 verified_commit=80e5bf3）；06798a2 降为"历史 SRS 验证锚点"保留审计。

### 5) TASK-UI-002 精确规范引用补 §5.3/§7（step 5）
- 精确规范引用补入 SRS v1.0 §5.3（隐私）/ §7（权限矩阵），支撑安全与隐私验收；安全隐私验收由"遵循 R9/R16"改为"遵循 SRS §5.3 与 §7，R9/R16 仅为历史输入来源"。

## 变更预算（change_budget）
- max_files：5（TASK-UI-002.md + TASK-GOV-004.md + TASK-GOV-005.md + PROJECT_STATE.md + TASK-GOV-006.md）
- expected_prod_lines：~30（纯文档/任务单文案）
- expected_test_lines：0

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：80662b2a57238ce996d17cf8f6a57d2fc49b804d（TASK-GOV-006 快照 / 本任务 verified_commit=G1）
- 修改文件清单（按路径逐条计数）：
  1. tasks/TASK-UI-002.md — 硬停条件 + 规范影响评估 + 精确规范引用补 §5.3/§7 + 安全隐私验收
  2. tasks/TASK-GOV-004.md — 第 72/86/92 行锚点语义校正
  3. tasks/TASK-GOV-005.md — 第 47 行锚点语义校正
  4. PROJECT_STATE.md — 最新验证锚点补入 80e5bf3、06798a2 降历史
  5. tasks/TASK-GOV-006.md — 本任务单（新建）
- 测试命令及结果：Grep 复核 TASK-UI-002 无"不改变用户可观察行为"、无"现有线框与领域模型 DeliveryStatus 不一致"独立硬停表述；TASK-GOV-004/005 无"关闭提交/关闭快照/全部 closing 证据"混淆；PROJECT_STATE 含 80e5bf3 末条
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：无（纯治理/文档校正）
- 变更预算实际值：max_files=5，实际 5 文件，未超预算
- 未解决风险：无（范围内已闭环）
- 是否偏离 TASK：否（全部在授权 5 项内）
- 规范影响结论：none（纯治理/文档校正，不改规范）
- spec_sync：clean
- verified_commit：80662b2a57238ce996d17cf8f6a57d2fc49b804d（TASK-GOV-006 快照 / G1；G2 为纯证据回填/关闭提交，不得循环指向自身）

## 关闭门禁（四条件全满足方可关闭）
① 测试通过（Grep 复核无残留错误表述）；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录真实 sha（= G1 快照，非关闭提交）。任一不满足→不得关闭。

## 关闭结论
任务于校正完成后关闭。关闭门禁四条件复核：① 测试通过（Grep 复核）；② 规范影响 none；③ spec_sync=clean；④ verified_commit=80662b2a57238ce996d17cf8f6a57d2fc49b804d（被验证的交付物快照，非关闭提交）。状态：Closed。

## 锚点语义（防混淆）
- 5666982 = 被验证的交付物快照（G1）；f2cfb88 = 纯证据回填/关闭提交（G2）。二者各司其职，不循环。
- 80e5bf3 = TASK-GOV-005 收口链被验证交付物快照（G1）；5f472a6 = 纯证据回填/关闭提交（G2）。

## 关联
- 上游：TASK-GOV-004 / TASK-GOV-005（被校正锚点）/ TASK-UI-002（被收口）
- 下游：用户复核 TASK-SRS-002（退信缺陷修正）→ 批准 SRS v1.1 → 同步 TASK-UI-002 退信项 → 批准 ui_wireframe → 架构/ADR
