# TASK-UI-002 UI 线框内容修正（承载 TASK-UI-IMPACT-001 的 MP-1）

> 仅修正 UI 线框中经影响评审确认的内容缺口；不扩需求、不批准 ui_wireframe、不推进下游。

## 任务类型
- design_correction

## 授权范围（允许修改路径）
- docs/design/ui-wireframe.md       # 仅 A6/A7 通知失败中心状态列补全（MP-1）
- tasks/TASK-UI-002.md              # 本任务单
- tasks/TASK-UI-001.md              # 修正完成后回填交付证据 / 标注内容缺口已闭合

## 禁止修改路径（越界即停）
- docs/baseline.yml                 # 不改 ui_wireframe.status（保持 pending，待用户评审实际线框）
- docs/requirements/SRS.md / 领域模型 # 仅引用不改
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
修正 A6/A7 通知失败中心状态枚举，使其与 SRS §6.2 / 领域模型 §5 的 `DeliveryStatus`（queued/sending/succeeded/failed/retry_scheduled/dead_letter）一致。

## 非目标
- 不新增页面/组件、不改语义色、不改限频阈值、不扩需求
- 不批准 ui_wireframe（baseline status 仍 pending）

## 精确修改点（来自 TASK-UI-IMPACT-001 / MP-1）
- **MP-1**：A6 通知失败中心列表"状态"列由单列"failed"扩展为区分 `failed`（可重试）与 `dead_letter`（终态死信，人工介入）并呈现 `retry_scheduled`（重试中）；手动重发仅对 failed/dead_letter 创建新尝试记录。A7 只读应急视图"通知失败列"同理涵盖 dead_letter 标红。

## 变更预算（change_budget）
- max_files：3（ui-wireframe.md + TASK-UI-002.md + TASK-UI-001.md 回填）

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：<回填>
- 修改文件清单：<回填，与「允许修改路径」对照>
- 测试命令及结果：全仓 Grep 复核 A6/A7 状态列含 dead_letter/retry_scheduled，与 SRS §6.2 枚举一致
- 变更预算实际值：<回填>
- 未解决风险：<或「无」>
- 是否偏离 TASK：<否>
- 规范影响结论：none（纯设计修正，不改行为）
- spec_sync：clean
- verified_commit：<回填>

## 关闭结论
四条件复核，状态 Closed。**注意：关闭本任务 ≠ 批准 ui_wireframe**——`baseline.ui_wireframe.status` 仍 pending，待用户评审实际线框后授权。

## 关联
- 上游：TASK-UI-IMPACT-001（影响评审，MP-1 来源）
- 下游：用户评审实际线框 → 授权 baseline.ui_wireframe.status→approved → 架构/ADR
