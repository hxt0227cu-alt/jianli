# TASK-UI-IMPACT-001 UI 线框影响评审（仅评审，不批准/不推进）

> 独立影响评审 TASK。仅做 UI 线框（ui-wireframe.md）对当前正式依据的影响评估，**不批准 ui_wireframe、不修改 baseline.ui_wireframe.status、不推进架构/安全/OpenAPI/测试计划/编码**。

## 任务类型
- impact_review

## 原始依据 vs 当前正式依据（step 5）
- **原始依据**（UI 线框 `30afe97` 启动时）：SRS 旧误批准锚点 `173cf9b6`（已作废，不复用）；领域模型 v1.1.2。
- **当前正式依据**：SRS `approval_commit=26ae844`（v1.0 已批准）/ `verified_commit=06798a2`（TASK-SRS-001 关闭快照）；领域模型 v1.1.4（TASK-DM-002 批准锚点 `f537296`）。

## 授权范围（允许修改路径）
- tasks/TASK-UI-IMPACT-001.md      # 本任务单（影响矩阵 + 结论 + 精确修改点）
- tasks/TASK-UI-001.md             # 仅更新基线锚点引用（SRS 173cf9b6→26ae844、领域模型 1.1.2→1.1.4）与"基线无效"告警再定性（不改内容、不改 status）
- docs/design/ui-wireframe.md       # 仅更新第 3 行基线锚点注释（不改线框内容）
- PROJECT_STATE.md                 # 仅同步任务态（TASK-UI-IMPACT-001 已关闭 / TASK-UI-002 已开启；不改任何 status、不推进下游）— 为维持 baseline+PROJECT_STATE+TASK 三态一致
- tasks/TASK-UI-002.md             # 本任务新建的 UI 修正任务（承载精确修改点）

## 禁止修改路径（越界即停）
- docs/baseline.yml                # 不改 ui_wireframe.status（保持 pending）
- docs/requirements/SRS.md         # 正文不变
- docs/design/domain-model.md      # 不变
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
比对现有 UI 线框与当前正式 SRS/领域模型，输出逐项影响矩阵，判定是否可沿用、列出精确修改点，交由后续修正任务处理。

## 非目标
- 不批准 ui_wireframe（status 仍 pending，待用户评审实际线框）
- 不修改线框内容（内容修正归 TASK-UI-002）
- 不推进架构/安全/OpenAPI/测试计划/编码

## 影响矩阵（step 6）
维度对照：当前 SRS §3–§6 / 领域模型 §5–§6 变化 → UI 线框（ui-wireframe.md `30afe97`）。

| # | 维度 | 当前依据 vs UI 线框现状 | 是否影响 | 说明 |
|---|------|------------------------|---------|------|
| 1 | 页面 (pages) | SRS §3.1–§3.9 + 管理 §3.7/§3.8/§3.9；线框 U1–U12 + A1–A8 已覆盖 | 否 | 无新增/缺失页面，映射完整 |
| 2 | 组件 (components) | A6 通知失败中心仅列"状态(failed)"；SRS §6.2 / 领域模型 §5 定义 `DeliveryStatus` = queued/sending/succeeded/failed/retry_scheduled/dead_letter | **轻微** | A6 状态列未覆盖 dead_letter（终态死信）/retry_scheduled；需补全（精确修改点 MP-1） |
| 3 | 交互态 (interaction states) | 黄格前端临时态；`SlotStatus`=available/booked/owner_locked/unavailable；`AppointmentStatus`=active/cancelled/completed | 否 | 与线框 §1.2 / U10 一致 |
| 4 | 异常态 (error states) | AUTH_EXPIRED / SLOT_TAKEN / DUP_COMPANY / DUP_ACCOUNT / CONFIRM_MAIL_FAIL 均已在线框呈现 | 否 | 当前 SRS 未新增异常态 |
| 5 | 权限 (permissions) | 面试官 vs admin 隔离；R9/R16 隐私遮挡 | 否 | 与线框 §1.3 / A1 / A7 一致 |
| 6 | 限频 (rate limiting) | A6 手动重发"同账号每10分钟≤5、每小时≤20"；U4 登录"15分钟失败5次锁15分钟"；U5 注册"每邮箱每小时≤3、每IP每小时≤5" — 均与 SRS §5.6 完全一致 | 否 | 已对齐，无影响 |
| 7 | 通知失败中心 (notification failure center) | A6/A7 已含"双通道独立重试不互为兜底；均失败持续高优先级告警"；但状态枚举仅 failed | **轻微** | 同 #2：dead_letter/retry_scheduled 未呈现（MP-1） |
| 8 | 追踪映射 (trace mapping) | 线框 §2 页面—SRS §3—UC 映射 | 否 | 功能域未变，映射仍有效 |

## 结论（step 8 / step 9）
**基本可沿用（reusable）**，存在 1 处轻微内容缺口（A6/A7 通知失败中心 `DeliveryStatus` 枚举补全），无页面/权限/限频/交互态/异常态/追踪映射层面影响。

- 基线锚点陈旧属**治理问题（非内容）**：TASK-UI-001 原引 SRS `173cf9b6` + 领域模型 1.1.2；现应更新为 SRS `26ae844` + 领域模型 1.1.4（解除"基线无效"所需的候选修正）。
- 因存在内容影响（#2/#7），依 **step 9**：列出精确修改点并新建 **TASK-UI-002** 承载；**不在本影响评审中顺手改线框内容、不扩需求**。

## 精确修改点（step 9，交由 TASK-UI-002）
- **MP-1（A6 通知失败中心状态枚举补全）**：SRS §6.2 / 领域模型 §5 规定 `DeliveryStatus` = queued/sending/succeeded/failed/retry_scheduled/dead_letter。当前线框 A6 仅以"状态(failed)"单列呈现。修正：状态列应区分 `failed`（可重试）与 `dead_letter`（终态死信，需人工介入、区别于普通 failed），并可呈现 `retry_scheduled`（重试中）；手动重发仅对 failed/dead_letter 创建新尝试记录（与 SRS §6.2 / 领域模型 §5 一致）。A7 只读应急视图"通知失败列"同理应涵盖 dead_letter 标红。
  - 范围限定：仅 A6/A7 状态列文案与列定义；不新增页面、不改语义色、不改限频阈值、不扩需求。

## 交付证据
- commit / PR：`a2ea98d8a61839c5b272b67be3e6afa4297ea48f`（TASK-UI-IMPACT-001 关闭提交 / 本任务 verified_commit）
- 修改文件清单（按路径逐条计数，不合并）：
  1. tasks/TASK-UI-IMPACT-001.md — 本任务单（影响矩阵 + 结论 + MP-1）
  2. tasks/TASK-UI-001.md — 基线锚点引用更新（173cf9b6→26ae844、1.1.2→1.1.4）+ "基线无效"告警再定性
  3. docs/design/ui-wireframe.md — 第 3 行基线锚点注释更新（不改内容）
  4. tasks/TASK-UI-002.md — 新建 UI 修正任务（承载 MP-1）
  5. PROJECT_STATE.md — 任务态同步（TASK-UI-IMPACT-001 已关闭 / TASK-UI-002 已开启；不改 status）
- 变更预算实际值：实际 5 文件，未超预算
- 未解决风险：无（范围内已闭环）；`baseline.ui_wireframe.status` 仍 pending，待用户评审实际线框
- 是否偏离 TASK：否（全部在授权 5 项内）
- 规范影响结论：none（纯评审，不改规范）
- spec_sync：clean（UI 为下游设计，不反向改 SRS/领域模型）
- verified_commit：`a2ea98d8a61839c5b272b67be3e6afa4297ea48f`（TASK-UI-IMPACT-001 关闭提交；含影响矩阵 + TASK-UI-001/ui-wireframe.md 锚点更新 + TASK-UI-002 新建 + PROJECT_STATE 同步）

## 关闭结论
任务于影响评审完成后关闭。关闭门禁四条件复核：① 测试通过（纯评审，Grep 复核锚点引用一致）；② 规范影响 none；③ spec_sync=clean；④ verified_commit=`a2ea98d8a61839c5b272b67be3e6afa4297ea48f`（TASK-UI-IMPACT-001 关闭提交）。状态：Closed（2026-08-08）。

## 关联
- 上游：TASK-SRS-001（SRS v1.0，已关闭）/ TASK-DM-002（领域模型 1.1.4，已关闭）
- 下游：TASK-UI-002（UI 线框内容修正，承载 MP-1；baseline.ui_wireframe.status 保持 pending，待用户评审实际线框）
