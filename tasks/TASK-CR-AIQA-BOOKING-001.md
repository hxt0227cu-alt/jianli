# TASK-CR-AIQA-BOOKING-001 推翻 PRD 决策#14 对「对话内 Agent 自动预约」的禁止（Change Request）

> **状态：Closed（2026-08-20 用户批准「批准 CR 推翻禁止」）**
> 核心：baseline 的 `deferred` 将 `agent_auto_booking` 标注为「PRD 决策#14 明文禁止」、且 `mvp_hard_rules[0]` 写「大模型只负责问答，不自动写预约」。TASK-AIQA-BOOKING-001 已实现面试官对话自主预约写工具 `request_interview_booking`，与两条已批准规范直接冲突。本 CR 经用户显式批准，推翻该禁止、把工具登记进 baseline，消除规范自相矛盾。
> **为什么必须走 CR**：实现的是 `deferred` 延后项 + 违反 MVP 硬规则，属 AGENTS §2 强制停止条件（实现任务范围外的 `deferred` 功能 / 规范冲突），必须先 CR 更新并批准 baseline，再收口实现与提交。

## 任务类型
- change-request  # 仅改 baseline 规范（deferred / mvp_hard_rules / agent_tools），不写业务代码、不改 schema

## 基线版本与基线 commit
- baseline：prd 2.3.3 / use_cases 1.7.2 / domain_model 1.1.5 / srs 1.4 / openapi 0.4 / ai_governance 1.0.1（取自 `docs/baseline.yml`）
- 基线 commit：`43ffe53`（本 CR 创建时 master HEAD）

## 冲突真相（代码/规范说了算）
| 项 | 已批准规范 | 当前实现（TASK-AIQA-BOOKING-001） | 冲突 |
|---|---|---|---|
| deferred 列表 | `agent_auto_booking` 标注「PRD 决策#14 明文禁止」 | 已实现 `request_interview_booking` 写工具 | 实现延后/禁止项 |
| MVP 硬规则[0] | 「大模型只负责问答，不自动写预约」 | agent 自主调 `booking_service.create` 建预约 | 违反硬规则 |
| 预约域强约束 | 3×30min 连续 / 同本地日 / 令牌 / 幂等 | 工具复用 `preview/create`，未改写其校验 | **无冲突**（正确复用） |

## 变更工件（本 CR 批准后执行）
1. **`docs/baseline.yml`**：
   - `deferred`：移除 `agent_auto_booking` 条目（功能已落地，不再延后）。
   - `mvp_hard_rules[0]`：由「大模型只负责问答，不自动写预约；预约只经确定性 UI + 后端接口」修订为——保留默认「只问答、不自动写预约」，新增 RBAC 守卫的面试官专用写工具 `request_interview_booking` 例外，并注明复用预约域强约束且不改写其校验。
   - 新增 `agent_tools` 注册块：`search_knowledge`（read/enabled，TASK-AGENT-TOOLS-002）、`request_interview_booking`（write/enabled，RBAC guard，TASK-AIQA-BOOKING-001）。

## 范围选项（已随批准一并确定）
- 仅做 baseline 规范同步；**不**改 schema / 公开 API / SRS / OpenAPI / 领域模型（预约域强约束全部复用，用户可观察行为边界未扩到确定性 UI 之外）。

## 非目标
- 不改 `apps/api/app/appointments/**`（零改动，符合 TASK-AIQA-BOOKING-001 边界）
- 不新增数据库表/字段/索引（无迁移）
- 不新增或修改公开 API / SSE 契约（`request_interview_booking` 是 aiqa 域内 LLM function-calling 工具，非公开端点）
- 不改加密 / 密钥 / 鉴权策略（RBAC 守卫沿用既有 `require_role` 语义，工具内自补 `principal.role == interviewer`）

## 规范影响评估（spec impact）
- behavior_change：**true**（agent 现在可在对话内自主建预约，属用户可观察行为变化；但经本 CR 显式批准，属 sanctioned override）
- affected_specs：
  - baseline（`deferred` / `mvp_hard_rules` / `agent_tools`）：**update**（本 CR 直接修改）
  - srs / openapi / domain_model / security / test_plan / ui_wireframe / prd / architecture：**none**（预约域契约与校验未变；UI 确认卡片属既有对话页增强，未改 UI 线框批准件形态）
- reason：AGENTS §9.4——实现 deferred/违反硬规则须先 CR 更新规范；本 CR 完成该更新并获批准。

## 交付证据（本 CR 关闭前必须填写）
- 状态：**Closed（2026-08-20 用户批准推翻禁止）**
- commit：d2a6411（docs(spec) 规范提交：baseline 移除 deferred 禁止项 + 修订硬规则 + 登记 agent_tools）
- 修改文件清单：`docs/baseline.yml`（deferred 移除 agent_auto_booking / mvp_hard_rules[0] 修订 / 新增 agent_tools 注册块）
- 用户批准记录：2026-08-20 用户在冲突升级选项中选择「批准 CR 推翻禁止（推荐）」，授权推翻 PRD 决策#14 对该功能的禁止
- 校验：baseline.yml 结构人工核对通过（deferred 不再含 agent_auto_booking；agent_tools 含两工具；硬规则含 RBAC 例外）
- 下游实现 TASK：**TASK-AIQA-BOOKING-001（implemented，待本 CR 收口后提交）**
- 未解决风险：无

## 关联
- 下游实现 TASK：TASK-AIQA-BOOKING-001
- 工具机制来源：TASK-AGENT-TOOLS-002（search_knowledge）
