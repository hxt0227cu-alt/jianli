# TASK-GOV-005 TASK-GOV-004 锚点语义校正 + TASK-UI-002 文案收口

> 向前治理修正：校正 TASK-GOV-004 第 89 行 verified_commit 残留占位并明确锚点语义；将 TASK-UI-002 手动重发依据由 SRS §4.2 改为 §4.3，统一 MP-1 口径（仅失败处理态、不宣称六态枚举），删除"UI 不拦截任何状态"与 N≤200 性能阈值，退信登记为 UI 批准前阻塞项；不重写历史、不批准 UI、不改 baseline、不修改 ui-wireframe.md。

## 任务类型
- governance

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.0（approved）/ AI 治理 1.0.1（取自 docs/baseline.yml）
- 基线 commit：26ae844（SRS v1.0 approved 锚点）；领域模型 v1.1.4 批准锚点 f537296；TASK-GOV-004 快照 5666982 / 关闭提交 f2cfb88

## 授权范围（允许修改路径）
- tasks/TASK-GOV-004.md   # 校正第 89 行 verified_commit + 锚点语义注记
- tasks/TASK-UI-002.md    # §4.2→§4.3、MP-1 口径统一、删除拦截态与 N≤200、退信阻塞项
- tasks/TASK-GOV-005.md   # 本任务单
- PROJECT_STATE.md        # 同步退信为 UI 批准前阻塞项（step 6）

## 禁止修改路径（越界即停）
- docs/baseline.yml             # 不改任何 status（ui_wireframe 保持 pending）
- docs/requirements/SRS.md / docs/design/domain-model.md  # 仅引用不改
- docs/design/ui-wireframe.md   # 本轮不修改（待用户复核）
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
校正 TASK-GOV-004 的锚点账目缺陷（verified_commit 占位残留 + 锚点语义混淆），并将 TASK-UI-002 收口为与已批准 SRS 精确一致的静态线框文案修正任务单（手动重发依据 §4.3、MP-1 仅失败处理态、删除越界表述与性能阈值、退信为 UI 批准前阻塞项）。

## 非目标
- 不执行 TASK-UI-002（不修改 ui-wireframe.md）
- 不批准 ui_wireframe
- 不推进架构/安全/OpenAPI/测试计划/编码
- 不补"退信"需求（仅登记为 UI 批准前阻塞项 + 建议 SRS Change Request）

## 精确规范引用
- 已批准 SRS v1.0 §6.2（状态模型，DeliveryStatus 枚举，手动重发=新建尝试记录）、§4.3（通信/通知接口行为，手动重发幂等键含新 event_version；§4.2 仅为软件接口概述）
- 领域模型 v1.1.4 §5（状态机规范，DeliveryStatus 枚举来源）
- TASK-TEMPLATE.md（任务单骨架与关闭门禁）

## 需求来源
- UC-21（通知失败中心手动重发）→ R5、R21；SRS §6.2 / §4.3 为 DeliveryStatus 与手动重发行为依据
- UC-23（后台只读应急视图）→ R14a

## 修正内容（step 1–6）

### 1) TASK-GOV-004 第 89 行 verified_commit 校正 + 锚点语义（step 1）
- 第 89 行残留 `verified_commit=<回填>` → 改为 `56669828de6a7dc9ba9a4a93a273c221efee76a4`（5666982）。
- 明确锚点语义（写入 TASK-GOV-004）：
  - 5666982 = **被验证的交付物快照**（G1），含 TASK-UI-IMPACT-001 校正 + TASK-UI-002 补全 + 本任务单全部 closing 证据；**不是关闭提交**。
  - f2cfb88 = **纯证据回填 / 任务关闭提交**（G2），仅将 verified_commit 回填为 5666982，不承载新交付物。
  - 不得为闭合重新生成指向自身的循环锚点；二者各司其职、保留历史。

### 2) TASK-UI-002 手动重发依据 §4.2 → §4.3（step 2）
- TASK-UI-002 中全部"手动重发依据 SRS §4.2"改为 §4.3；§4.2 仅为软件接口概述（SRS §4.2 标题"软件接口（行为契约，不含 URL/Schema）"，手动重发幂等键实际在 §4.3 第 193 行）。
- 涉及：精确规范引用、需求来源、规范影响评估、MP-1 共 4 处 §4.2 → §4.3。

### 3) MP-1 口径统一（step 3）
- 目标由"与 SRS §6.2 / 领域模型 §5 的六态枚举一致"改为"补充失败处理相关状态 failed/retry_scheduled/dead_letter（与 SRS §6.2 一致）；queued/sending/succeeded 是否进入失败中心 SRS 未规定，本任务不裁定"。
- 不宣称"补全完整六态枚举"；A6/A7 仅呈现失败处理三态 failed/dead_letter/retry_scheduled（功能验收已对齐）。

### 4) 删除"UI 不拦截任何状态"（step 4）
- 功能验收异常路径由"不限定当前状态；UI 不拦截任何状态"改为："线框不定义手动重发资格，仅记录'手动重发会新建 NotificationDelivery 尝试'；可操作状态由后续获批规范/API 契约定义，UI 任务不得自行增加规则"。

### 5) 删除 N≤200 性能阈值（step 5）
- 性能验收由"N≤200 条失败记录时无明显卡顿"改为 `N/A（本任务为静态低保真线框文案修正，不产生新的运行时性能要求）`。

### 6) 退信登记为 UI 批准前阻塞项（step 6）
- TASK-UI-002 待裁定项标题改为"待裁定项（UI 批准前阻塞项）"，明确：建议先建立 SRS Change Request 裁定是否恢复 PRD/UC-21 退信展示/筛选/重发；裁定完成前不得批准 ui_wireframe（status 维持 pending）。
- 关联下游补充：ui_wireframe 批准须待退信裁定完成。
- PROJECT_STATE 同步：TASK-UI-002 行补"退信为 UI 批准前阻塞项"注记。

## 变更预算（change_budget）
- max_files：4（TASK-GOV-004.md + TASK-UI-002.md + TASK-GOV-005.md + PROJECT_STATE.md）
- expected_prod_lines：~40（纯文档/任务单文案）
- expected_test_lines：0

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<回填>
- 修改文件清单（按路径逐条计数）：
  1. tasks/TASK-GOV-004.md — 第 89 行 verified_commit 校正 + 锚点语义注记
  2. tasks/TASK-UI-002.md — §4.2→§4.3、MP-1 口径、删除拦截态与 N≤200、退信阻塞项
  3. tasks/TASK-GOV-005.md — 本任务单（新建）
  4. PROJECT_STATE.md — 退信为 UI 批准前阻塞项同步注记
- 测试命令及结果：Grep 复核 TASK-UI-002 无残留"§4.2"手动重发依据、无"UI 不拦截任何状态"、无"N≤200"；TASK-GOV-004 第 89 行 verified_commit=5666982
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：无（纯治理/文档校正）
- 变更预算实际值：max_files=4，实际 4 文件，未超预算
- 未解决风险：无（范围内已闭环）；退信待裁定为范围外开放项，不阻塞本治理任务，但阻塞 ui_wireframe 批准
- 是否偏离 TASK：否（全部在授权 4 项内）
- 规范影响结论：none（纯治理/文档校正，不改规范）
- spec_sync：clean
- verified_commit：<回填，= G1 快照提交 SHA；G2 为纯证据回填/关闭提交，不得循环指向自身>

## 关闭门禁（四条件全满足方可关闭）
① 测试通过（Grep 复核无残留错误表述）；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录真实 sha（= G1 快照，非关闭提交）。任一不满足→不得关闭。

## 关联
- 上游：TASK-GOV-004（被校正锚点）/ TASK-UI-002（被收口）
- 下游：用户复核 TASK-UI-002（含退信阻塞项）→ 退信 SRS Change Request 裁定 → 授权执行 → 批准 ui_wireframe → 架构/ADR
