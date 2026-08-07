# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（**SRS v1.0 / approved**（用户独立评审批准，独立批准锚点 `26ae844`；TASK-SRS-001 已关闭、用例规约冻结为历史输入、SRS 现为行为唯一源）；domain_model **v1.1.4 / approved**（TASK-DM-002 已关闭）；TASK-DM-001 历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点；UI 线框影响评审完成（TASK-UI-IMPACT-001，基本可沿用+1 处缺口待 TASK-UI-002），`ui_wireframe.status` 仍 pending 待用户评审实际线框）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。

- **领域模型 v1.1.4 / status=approved**（经用户 2026-08-08 明确批准「我批准领域模型 v1.1.4 的内容」，独立批准锚点 `f537296`，不复用 `f64b6de`）。v1.1.3 已于 `f64b6de` **正式批准（历史事实保留，不予否认）**，但其后发现 P0 算法锁定缺陷；按"同一版本号不得对应批准前后两份不同内容"的治理原则，修正**不复用 1.1.3**，改由 **TASK-DM-002 升版 v1.1.4** 承载（密码算法中性化 + Security ADR 与 PRD §8.7 BCrypt 冲突须走规范影响/变更评审的条款）。TASK-DM-002 已关闭。
- **SRS v1.0 / status=approved**（用户 2026-08-08 独立评审批准，独立批准锚点 `26ae844`，不复用旧误批准锚点 `173cf9b6`），`spec_sync=clean`。`baseline.srs.based_on` = prd 2.3.3 / use_cases 1.7.2 / domain_model 1.1.4（上游均已 approved 且对齐）；TASK-SRS-001 已完成 impact review（based_on→1.1.4 + 修正 SRS §6.3 过期 Argon2id 描述；**结论 = 需文字同步、不改变用户可观察行为，非 none**）并已于本回合关闭。**SRS 现为行为唯一源**（precedence 高于 PRD/用例规约），用例规约冻结为历史输入；**v1.1 缺陷修正修订（TASK-SRS-002）review 中**：补充退信(Bounce) 行为，v1.0 approved 快照冻结于 `26ae844` 不变，v1.1 待用户批准。
- **UI 线框（TASK-UI-001 / ui-wireframe.md）**：UI 线框影响评审已完成（TASK-UI-IMPACT-001，结论=基本可沿用 + 1 处轻微内容缺口）；基线锚点已更新为 SRS `26ae844` / 领域模型 1.1.4（解除"基线无效"）；内容缺口由 TASK-UI-002 承载；`baseline.ui_wireframe.status` 仍 `pending`，待用户评审实际线框。

---

## 当前任务

- **TASK-DM-001**：历史**已关闭**（对应 domain_model v1.1.3，批准锚点 `f64b6de`）。不重开；其成果由 v1.1.4 取代。
- **TASK-DM-002**：**已关闭（Closed，2026-08-08）**——领域模型 v1.1.3→v1.1.4 密码算法中性化修正。关闭门禁按 `tasks/TASK-TEMPLATE.md` 四条件执行（`spec_sync=dirty` 不得关闭，现已满足并关闭）。
  - **执行顺序（2026-08-08 第三轮修正并已执行完毕）**：① 用户批准 v1.1.4 → 生成**独立批准锚点** `f537296`（不得复用 `f64b6de`）；② **先**由 TASK-SRS-001 执行 SRS impact review 并将其 `spec_sync` 转 clean（`d166992`）；③ **然后**本任务 `spec_sync` 由 dirty 转 clean，补齐 `verified_commit`/验证结果/关闭结论后**关闭**（本任务关闭提交）。
  - **不构成本任务关闭条件（已验证）**：SRS 自身获得 `approved` 不构成本任务关闭条件——TASK-DM-002 关闭当时 SRS 仍为 review（现已于 26ae844 approved），本任务已关闭即证明二者解耦。
- **TASK-SRS-001**：**已关闭（Closed，2026-08-08）**——SRS v1.0 生成 + impact review（domain_model 1.1.3→1.1.4 文字同步）+ 本次 SRS 批准收口。`approval_commit=26ae844`（SRS 批准单一用途锚点），`verified_commit=06798a2`（SRS 关闭快照）。`spec_sync=clean`；SRS 现已 approved。
- **TASK-UI-001**：冻结待评审（基线已恢复有效，内容缺口待 TASK-UI-002 修正）；`baseline.ui_wireframe.status` 仍 pending，未经用户评审不得置 approved。
- **TASK-UI-IMPACT-001**：**已关闭（Closed，2026-08-08）**——UI 线框影响评审，结论=基本可沿用（SRS `26ae844` + 领域模型 1.1.4 与现有线框对齐；仅 A6 通知失败中心 `DeliveryStatus` 枚举轻微缺口）→ 内容缺口由 **TASK-UI-002** 承载；未批准 ui_wireframe、未改 baseline 状态、未推进架构。
- **TASK-UI-002**：**开启**——UI 线框内容修正（A6/A7 通知失败中心失败处理态 failed/retry_scheduled/dead_letter 补全），依据 SRS §6.2 / §4.3 / 领域模型 §5；`baseline.ui_wireframe.status` 保持 pending，待用户评审实际线框后授权。**退信(bounce) 为 UI 批准前阻塞项**：已由 TASK-SRS-002 以 SRS v1.1 缺陷修正处理（review 草案完成），待用户批准 SRS v1.1 后解除阻塞并同步执行，裁定完成前不得批准 ui_wireframe。
- **TASK-SRS-002**：**开启（review 草案）**——SRS 退信(Bounce) 行为缺陷修正（v1.0 → v1.1，review）；补充 PRD §4.6/R26 与 UC-21 已要求但 v1.0 遗漏的退信记录/展示筛选/告警/手动重发/不回滚预约；domain_model 无需改（bounce 字段已在 v1.1.4 §5）；baseline.srs 进入 v1.1 review；**不代签批准**，待用户评审批准 v1.1 后由 TASK-UI-002 同步退信项 → 批准 ui_wireframe。
- 具体版本与评审状态见 `docs/baseline.yml`。

---

## 本周阻塞

- 待确认项（PRD §8.2，不阻塞设计但阻塞上线）：SMTP / 域名 / 备案、飞书授权、人格素材、知识库文件。
- 网易 163 邮箱授权码等密钥**绝不写入任何文档 / 记忆 / 配置文件**，仅存运行时环境变量或 Secret Manager。

---

## 下一步（评审推荐顺序，仍编码前）

```
SRS v1.0 → UI 线框 → 架构与 ADR → 安全设计 → OpenAPI/SSE 合同 → 测试计划 → 开发准入评审 → 功能编码
```

> 注：当前门禁顺序（**2026-08-08 第三轮修正 + 本回合 SRS 收口，①②③④ 已完成，现处 ⑤**）——
> ① ✅ 用户批准 **domain_model v1.1.4** → baseline `domain_model.status: review→approved`，独立批准锚点 `f537296`（**不复用 `f64b6de`**）；
> ② ✅ **TASK-SRS-001 执行 SRS impact review**（`srs.based_on.domain_model`→1.1.4 + 修正 SRS §6.3 过期的 Argon2id 描述；结论 = "需文字同步、不改变用户可观察行为"，**非 none**）→ TASK-SRS-001 `spec_sync` 转 clean；
> ③ ✅ **TASK-DM-002 `spec_sync` 转 clean + 关闭**（verified_commit=`94bedb5`，approval_commit=`f537296` 即 domain_model v1.1.4 独立批准锚点；对齐 TASK-TEMPLATE 关闭门禁：`spec_sync=dirty` 不得关闭，故必须在 ② 之后）；
> ④ ✅ 用户独立评审批准 **SRS v1.0**（AI 不代签，独立批准锚点 `26ae844`，不复用 `173cf9b6`）→ 关闭 TASK-SRS-001（verified_commit 见 S3 回填）、用例规约冻结为历史输入、SRS 成为行为唯一源；
> ⑤ ✅ **UI 线框影响评审（TASK-UI-IMPACT-001）**：结论=基本可沿用（SRS `26ae844` + 领域模型 1.1.4 与现有线框对齐；仅 A6 通知失败中心状态枚举轻微缺口）→ 内容缺口由 **TASK-UI-002** 承载；`ui_wireframe.status` 仍 pending，待用户评审实际线框。
> ⑤b ⏳ 用户评审实际线框 → 修正（TASK-UI-002）后批准 ui_wireframe（baseline status→approved）→ 架构/ADR → 安全设计 → OpenAPI/SSE → 测试计划 → 开发准入评审 → 功能编码。
> `development_gate` 全 10 项 approved 前不得进入编码。

---

## 最后 verified commit（审计锚点）

> 按时间顺序列出治理验证锚点；**最新有效锚点 = 本文件末条**。历史锚点保留作审计回溯，不表示当前态。

- **历史治理锚点（保留，不表示当前态）**：`adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: `gov-sync-001-verified`）— 早期治理收尾 commit（含 TASK-GOV-SYNC-001 关闭证据 + 全部治理文件）。机器锚点首选真实 SHA，tag 仅作人类别名；解析见 `git rev-parse gov-sync-001-verified`。Review/Audit Mode（`AGENTS.md §9`）可 `git checkout gov-sync-001-verified` 复盘，但**不得再称其为"当前最后 verified commit"**。
- **领域模型完整验证快照**：`94bedb5be60b1678fb033c5d8735e38dae9a46a9`（`94bedb5`）— TASK-DM-002 关闭提交，含 domain_model v1.1.4 approved + SRS impact review（`d166992`）/ spec_sync=clean + TASK-DM-002 Closed 的完整验证态；为当前领域模型 v1.1.4 的可审计快照。
- **历史 SRS 验证锚点（保留作审计回溯，非当前最新）**：`06798a2815d60a50caebe3ce6582553531be8dea`（`06798a2`）— 本回合 SRS 收口提交（TASK-SRS-001 关闭），含 SRS approved + spec_sync=clean + TASK-SRS-001 Closed + 本 PROJECT_STATE 同步。
- **最新验证锚点（当前有效"最后 verified commit"）**：`80e5bf3a014b33713f1d9bb78f1bbb9acbf0f535`（`80e5bf3`）— TASK-GOV-005 收口链（G1 快照 80e5bf3 + G2 证据回填 5f472a6），verified_commit=80e5bf3（被验证的交付物快照），含 TASK-GOV-004 锚点语义校正 + TASK-UI-002 文案收口 + 本 PROJECT_STATE 同步；为当前治理最后 verified commit。

本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
