# TASK-SRS-002 SRS 退信(Bounce) 行为缺陷修正（v1.0 → v1.1）

> 向前治理修正：SRS v1.0 声称吸收 PRD/用例规约但**遗漏退信(Bounce) 用户可观察行为**——PRD §4.6 / R26（场景 18）与 UC-21 已明确要求记录退信、后台展示/筛选、告警、手动重发且不回滚预约。本任务将退信行为补入 SRS，升版 **v1.1（review）**；不修改已批准 v1.0 快照（26ae844）；完成下游影响评审，但**不代签批准 SRS**。

## 任务类型
- spec_correction（SRS 缺陷修正）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4 / SRS 1.0（approved @ `26ae844`）→ 本任务产出 SRS **1.1（review）** / AI 治理 1.0.1
- 基线 commit：26ae844（SRS v1.0 approved 锚点，不重写）；领域模型 v1.1.4 批准锚点 f537296

## 授权范围（允许修改路径）
- docs/requirements/SRS.md        # v1.0 → v1.1 缺陷修订（补充退信行为）
- docs/baseline.yml               # srs.version 1.0→1.1、status approved→review
- tasks/TASK-SRS-002.md           # 本任务单
- PROJECT_STATE.md                # 同步 TASK-SRS-002 与 srs=review

## 禁止修改路径（越界即停）
- docs/design/domain-model.md     # 退信字段已在 v1.1.4 §5 channel_metadata，不改
- docs/design/ui-wireframe.md     # 待 SRS v1.1 批准后由 TASK-UI-002 同步，本任务不改
- tasks/TASK-UI-002.md            # 退信阻塞项待 SRS 批准后解除，本任务不改
- 任何架构/安全/OpenAPI/测试计划/代码文件

## 目标
将 v1.0 遗漏的退信(Bounce) 用户可观察行为补入 SRS，使其忠实吸收 PRD §4.6/R26 与 UC-21 已规定、但 v1.0 未写入的：退信记录、后台展示/筛选、告警、手动重发、不回滚预约。升版 v1.1（review），不修改 v1.0 在 26ae844 的已批准快照。

## 非目标
- 不修改 v1.0 快照（26ae844 冻结，不重写历史）
- 不新增产品功能（仅补遗漏行为，非新需求；不重新解释为任意产品选择）
- 不批准 SRS（待用户独立评审批准 v1.1 后 baseline status→approved）
- 不改动 domain_model（bounce 字段已在 v1.1.4 §5）
- 不执行/修改 TASK-UI-002 与 ui-wireframe（待 SRS 批准后同步）

## 精确规范引用
- PRD v2.3.3 §4.6（候选人侧视图与提醒）/ R26（二次确认+确认函回执，含退信）/ §8.10.3（DeliveryStatus）/ §8.13（退信语义）
- 用例规约 v1.7.2 UC-21（通知失败中心，筛选失败/退信、手动重发）
- 已批准 SRS v1.0 §3.8 / §3.9 / §4.3 / §6.2 / §8（补充退信行为的位置）
- 领域模型 v1.1.4 §5（channel_metadata.bounced_at/bounce_reason，邮件分支）

## 需求来源
- R26（PRD §4.6 / 场景 18）：确认函退信记录 + 飞书告警候选人 + 后台高优先级告警 + 不回滚预约 + 可手动重发（version+1）
- UC-21：admin 后台查看失败/退信记录、按通道与状态筛选、手动重发

## 修正内容（SRS v1.0 → v1.1）

### 1) 文档头版本与状态
- 标题 v1.0 → v1.1；状态说明：v1.0 已于 26ae844 批准（approved 快照冻结），本 v1.1 为缺陷修正修订，经用户评审通过后方可置 approved。

### 2) §3.8 候选人侧视图与提醒：新增退信(Bounce) 处理
- SMTP 接受后被对方退回时，记录 `NotificationDelivery.channel_metadata.bounced_at` + `bounce_reason`（仅邮件通道有意义，不混入通用 DeliveryStatus）；
- 飞书告警候选人 + 后台高优先级告警；
- **不回滚预约**（与 `CONFIRM_MAIL_FAIL` 语义一致）；
- 通知失败中心（§3.9/UC-21）展示并支持按通道与状态**筛选退信记录**，可对其手动重发（新建 `NotificationDelivery` 尝试记录，`attempt_no`+1，幂等键含新 `event_version`，version+1）。

### 3) §3.9 管理后台：失败中心补退信展示/筛选/重发
- 行为：…→ 通知/同步失败中心（含退信记录展示与按通道/状态筛选）手动重发（UC-21）；
- 验收：admin 可登录/传知识库/看对话/只读应急视图/标不可约/编公告/**查看并筛选退信记录、手动重发**。

### 4) §4.3 通信/通知接口行为：退信行为契约
- 邮件通道 SMTP 接受后若被退回，于 `channel_metadata` 写入 `bounced_at`/`bounce_reason`；此属邮件通道专属元数据，不改变通用 `DeliveryStatus` 枚举（§6.2）；触发告警与失败中心呈现（见 §3.8/§3.9）；不回滚业务预约。

### 5) §6.2 状态模型：退信非 DeliveryStatus 枚举
- 退信(Bounce) 不属 `DeliveryStatus` 枚举，仅邮件通道于 `channel_metadata.bounced_at`/`bounce_reason` 记录（见 §3.8/§4.3；领域模型 v1.1.4 §5）。

### 6) §8 异常与错误处理：补充退信说明（不新增错误码）
- `CONFIRM_MAIL_FAIL` 已涵盖"不回滚预约 + 告警 + 可手动重发"；退信为该失败路径的邮件通道专属元数据记录，不引入新错误码。

### 7) §9 验收标准：新增退信处理行
- 退信处理（R26）：SMTP 接受后 bounce → 记 bounced_at/bounce_reason + 飞书告警候选人 + 后台高优先级告警 + 不回滚预约 + 失败中心展示/筛选/手动重发（version+1）。

### 8) §10 可追溯性：R26/UC-21 增补退信节映射
- R26 主要 SRS 节增列 §3.8 / §4.3；UC-21 主要 SRS 节增列 §3.8 / §3.9（退信展示筛选）。

## 变更预算（change_budget）
- max_files：4（SRS.md + baseline.yml + TASK-SRS-002.md + PROJECT_STATE.md）
- expected_prod_lines：~50（纯文档/规范文案）
- expected_test_lines：0

## 规范影响评估（spec impact）
- behavior_change：true（补 v1.0 遗漏的退信用户可观察行为；该行为已由 PRD §4.6/R26 与 UC-21 规定，不属新增产品选择）
- affected_specs：
  - srs：self（本任务修正对象）
  - domain_model：none（bounce 字段已在 v1.1.4 §5 channel_metadata，无需改）
  - openapi：pending（尚未产出，spec_sync 标 dirty 待其产出时吸收；不阻塞）
  - security：pending（退信记录含候选人邮箱，沿用 §5.2/§5.3 加密与隐私约束；不新增）
  - test_plan：pending（退信验收用例由《测试计划》补全，本任务仅列 SRS §9 验收行）
  - ui_wireframe：pending（TASK-UI-002 的"退信 UI 批准前阻塞项"将在 SRS v1.1 approved 后解除并由该任务同步执行；本任务不改 UI）
- reason：v1.0 声称吸收上游但遗漏退信行为，属缺陷修正；行为增量由 PRD/UC 规定，不重新解释为任意产品选择。

## 下游影响评审（downstream impact review，本任务完成）
- **domain_model v1.1.4**：退信字段 `bounced_at`/`bounce_reason` 已在 §5 `channel_metadata` 定义，无需变更；影响 none。
- **TASK-UI-002 / ui-wireframe**：其「待裁定项（UI 批准前阻塞项）」中退信阻塞在 SRS v1.1 approved 后解除；当前 TASK-UI-002 与 ui_wireframe 维持 pending，本任务不修改，待用户批准 SRS v1.1 后由 TASK-UI-002 同步执行（含退信展示/筛选/重发线框）。
- **openapi / architecture / security / test_plan**：均 pending（0.0），无现有下游工件需即时同步；spec_sync 标 dirty 以待其产出时吸收退信行为，但不阻塞本缺陷修正（无已存在工件被破坏）。
- **结论**：SRS v1.1 为缺陷修正，行为增量已由 PRD/UC 规定；无需触发新的 Change Request（PRD/UC 已含退信要求，SRS 仅补写）。下游 UI 同步待 SRS 批准后由 TASK-UI-002 执行。

## 必须运行的测试命令
- 全仓 Grep 复核 SRS v1.1 含"退信/Bounce"行为节（§3.8/§3.9/§4.3/§6.2/§9）且与 PRD §4.6/R26、UC-21 一致；复核未新增与领域模型 v1.1.4 §5 冲突的 DeliveryStatus 枚举。

## 回滚方法
- `git revert <本任务提交>` 或还原 SRS.md 至 v1.0 内容（26ae844 快照）；baseline.srs 回 review→（不回退至 approved v1.0 除非用户决定）。不影响 domain_model/UI。

## 强制停止条件（与 AGENTS.md §2 一致）
- 可继续：变更在「允许修改路径」列明，且依据工件（PRD §4.6/R26、UC-21、domain_model v1.1.4 §5）为 approved。
- 必须停止：新增与 PRD/UC/域模型冲突的退信行为或新 DeliveryStatus 枚举；或误改 domain_model/ui-wireframe/TASK-UI-002。

## 交付证据
- commit / PR：1c21d7dcae4c3c1c413697d251a4c7e7f136696a（TASK-SRS-002 SRS v1.1 review 草案锚点 / 本任务 verified_commit=G1）
- 修改文件清单（按路径逐条计数）：
  1. docs/requirements/SRS.md — v1.0→v1.1 缺陷修订（退信行为 §3.8/§3.9/§4.3/§6.2/§9/§10 + 修订说明）
  2. docs/baseline.yml — srs.version 1.0→1.1、status approved→review
  3. tasks/TASK-SRS-002.md — 本任务单（新建）
  4. PROJECT_STATE.md — TASK-SRS-002 条目 + srs review 状态同步
- 测试命令及结果：<命令> → <pass/fail>
- lint / typecheck：无（纯文档）
- DB 迁移验证：无
- 验收证据：SRS v1.1 与 PRD §4.6/R26、UC-21 逐条对照（退信记录/展示筛选/告警/手动重发/不回滚预约均覆盖）；domain_model v1.1.4 §5 channel_metadata 已含 bounce 字段，无冲突
- 变更预算实际值：max_files=4，实际 4 文件，未超预算
- 未解决风险：下游 UI 同步待 SRS 批准后执行（非本任务范围）
- 是否偏离 TASK：否
- 规范影响结论：behavior_change=true（补遗漏行为），domain_model none，下游待批准后同步
- spec_sync：dirty（openapi/security/test_plan 待产出时吸收；无现有工件破坏）
- verified_commit：1c21d7dcae4c3c1c413697d251a4c7e7f136696a（TASK-SRS-002 SRS v1.1 review 草案锚点 / G1；G2 为纯证据回填，不得循环指向自身）

## 关闭门禁
- 本任务**不等同于批准 SRS**。SRS 批准由用户独立操作 `docs/baseline.yml`（status→approved）。
- 本任务完成判据：① SRS v1.1 review 草案完成（含退信行为）；② 下游影响评审完成；③ spec_sync 已标注（dirty 待下游吸收）；④ 未偏离授权路径。
- 用户批准 SRS v1.1（baseline status→approved）后，TASK-UI-002 退信阻塞解除、可同步执行；本 SRS 缺陷修正视为落地。AI 不代签批准。

## 关联
- 上游：SRS v1.0（26ae844，approved，遗漏退信）/ PRD §4.6/R26 / UC-21
- 下游：用户评审批准 SRS v1.1 → TASK-UI-002 同步退信项 → 批准 ui_wireframe → 架构/ADR
