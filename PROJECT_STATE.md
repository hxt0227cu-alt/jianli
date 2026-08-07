# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（domain_model 升版 **v1.1.4 / approved**，由新任务 **TASK-DM-002** 已关闭（曾承载密码算法中性化）；TASK-DM-001 保持历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点；SRS 仍 review 且 **spec_sync=clean**（TASK-SRS-001 已完成 impact review）；UI 线框继续冻结、不得评审）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。

- **领域模型 v1.1.4 / status=approved**（经用户 2026-08-08 明确批准「我批准领域模型 v1.1.4 的内容」，独立批准锚点 `f537296`，不复用 `f64b6de`）。v1.1.3 已于 `f64b6de` **正式批准（历史事实保留，不予否认）**，但其后发现 P0 算法锁定缺陷；按"同一版本号不得对应批准前后两份不同内容"的治理原则，修正**不复用 1.1.3**，改由 **TASK-DM-002 升版 v1.1.4** 承载（密码算法中性化 + Security ADR 与 PRD §8.7 BCrypt 冲突须走规范影响/变更评审的条款）。TASK-DM-002 已关闭。
- **SRS v1.0 / status=review**（未 approved，不计入 precedence 裁决），`spec_sync=clean`。`baseline.srs.based_on.domain_model` 已更新至 **1.1.4**；TASK-SRS-001 已执行 impact review（更新 based_on→1.1.4 + 修正 SRS §6.3 中"领域模型 §6.1 记为 Argon2id"的过期描述；**结论 = 需文字同步、不改变用户可观察行为，非 none**），spec_sync 已由 dirty 转 clean。SRS 自身仍 review，批准权在用户，AI 不代签。
- **UI 线框（TASK-UI-001 / ui-wireframe.md）继续冻结**：基线无效、不得评审。

---

## 当前任务

- **TASK-DM-001**：历史**已关闭**（对应 domain_model v1.1.3，批准锚点 `f64b6de`）。不重开；其成果由 v1.1.4 取代。
- **TASK-DM-002**：**已关闭（Closed，2026-08-08）**——领域模型 v1.1.3→v1.1.4 密码算法中性化修正。关闭门禁按 `tasks/TASK-TEMPLATE.md` 四条件执行（`spec_sync=dirty` 不得关闭，现已满足并关闭）。
  - **执行顺序（2026-08-08 第三轮修正并已执行完毕）**：① 用户批准 v1.1.4 → 生成**独立批准锚点** `f537296`（不得复用 `f64b6de`）；② **先**由 TASK-SRS-001 执行 SRS impact review 并将其 `spec_sync` 转 clean（`d166992`）；③ **然后**本任务 `spec_sync` 由 dirty 转 clean，补齐 `verified_commit`/验证结果/关闭结论后**关闭**（本任务关闭提交）。
  - **不构成本任务关闭条件（已验证）**：SRS 自身获得 `approved`——SRS 仍 review，但本任务已关闭，证明二者解耦。
- **TASK-SRS-001**：开启中，`spec_sync=clean`（已执行 impact review：`d166992`），等待用户独立评审批准 SRS（baseline `srs.status: review→approved`）；SRS 批准权在用户，AI 不代签；批准后方可关闭本任务。
- **TASK-UI-001**：冻结，不得评审、不得推进。
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

> 注：当前门禁顺序（**2026-08-08 第三轮修正，①②③ 已完成，现处 ④**）——
> ① ✅ 用户批准 **domain_model v1.1.4** → baseline `domain_model.status: review→approved`，独立批准锚点 `f537296`（**不复用 `f64b6de`**）；
> ② ✅ **TASK-SRS-001 执行 SRS impact review**（`srs.based_on.domain_model`→1.1.4 + 修正 SRS §6.3 过期的 Argon2id 描述；结论 = "需文字同步、不改变用户可观察行为"，**非 none**）→ TASK-SRS-001 `spec_sync` 转 clean；
> ③ ✅ **TASK-DM-002 `spec_sync` 转 clean + 关闭**（verified_commit=`94bedb5`，approval_commit=`f537296` 即 domain_model v1.1.4 独立批准锚点；对齐 TASK-TEMPLATE 关闭门禁：`spec_sync=dirty` 不得关闭，故必须在 ② 之后）；
> ④ ⏳ 用户独立评审批准 **SRS**（AI 不代签）→ 关闭 TASK-SRS-001、用例规约冻结为历史输入或 SRS 附录；
> ⑤ ⏳ UI 线框重新 impact review 决定是否沿用 → 架构/ADR → 安全设计 → OpenAPI/SSE → 测试计划 → 开发准入评审 → 功能编码。
> `development_gate` 全 10 项 approved 前不得进入编码。

---

## 最后 verified commit（审计锚点）

> 按时间顺序列出治理验证锚点；**最新有效锚点 = 本文件末条**。历史锚点保留作审计回溯，不表示当前态。

- **历史治理锚点（保留，不表示当前态）**：`adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: `gov-sync-001-verified`）— 早期治理收尾 commit（含 TASK-GOV-SYNC-001 关闭证据 + 全部治理文件）。机器锚点首选真实 SHA，tag 仅作人类别名；解析见 `git rev-parse gov-sync-001-verified`。Review/Audit Mode（`AGENTS.md §9`）可 `git checkout gov-sync-001-verified` 复盘，但**不得再称其为"当前最后 verified commit"**。
- **领域模型完整验证快照**：`94bedb5be60b1678fb033c5d8735e38dae9a46a9`（`94bedb5`）— TASK-DM-002 关闭提交，含 domain_model v1.1.4 approved + SRS impact review（`d166992`）/ spec_sync=clean + TASK-DM-002 Closed 的完整验证态；为当前领域模型 v1.1.4 的可审计快照。
- **最新验证锚点（当前有效"最后 verified commit"）**：`65fc7a5f76f2e5a5baff62993bcbc56ec2bed4ba`（`65fc7a5`）— 本回合"证据校正"提交（TASK-GOV-002 关闭），含 TASK-GOV-001 计数口径校正 + 本 PROJECT_STATE 同步 + TASK-GOV-002 任务单。

本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
