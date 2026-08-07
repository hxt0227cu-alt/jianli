# PROJECT_STATE.md — 当前项目状态（AI 会话起点）

> 本文件**只记录任务态**：当前阶段 / 当前任务 / 本周阻塞 / 下一步 / 最后通过测试的 commit。
> **不重复维护任何版本号、评审状态、优先级或延后项**——那些只存在于 `docs/baseline.yml`（唯一规范源）。
> 每次会话先读 `AGENTS.md` → `docs/baseline.yml` → 本文件；仅在修改仓库时追加当前 TASK 文件。不依赖聊天记忆。
> 最后更新：2026-08-08（domain_model 升版 **v1.1.4 / review**，由新任务 **TASK-DM-002** 承载密码算法中性化；TASK-DM-001 保持历史已关闭、`f64b6de` 为旧版 1.1.3 真实批准锚点；SRS 仍 review 且 **spec_sync=dirty，待上游 1.1.4 获批后做 impact review**；UI 线框继续冻结、不得评审）

---

## 当前阶段

分析设计阶段。编码准入未开放，由 `docs/baseline.yml` 的 `development_gate` 决定。

- **领域模型 v1.1.4 / status=review**（不计入 precedence 裁决）。v1.1.3 已于 `f64b6de` **正式批准（历史事实保留，不予否认）**，但其后发现 P0 算法锁定缺陷；按"同一版本号不得对应批准前后两份不同内容"的治理原则，修正**不复用 1.1.3**，改由新任务 **TASK-DM-002 升版 v1.1.4** 承载（密码算法中性化 + Security ADR 与 PRD §8.7 BCrypt 冲突须走规范影响/变更评审的条款）。**待用户独立评审批准，AI 不代签 approved。**
- **SRS v1.0 / status=review**（未 approved，不计入 precedence 裁决），`spec_sync=dirty`。`baseline.srs.based_on.domain_model` **有意保留 1.1.3**，使机器门禁正确显示"上游已变更、需 impact review"。待 1.1.4 获批后由 TASK-SRS-001 执行 impact review（更新 based_on→1.1.4 + 修正 SRS §6.3 中"领域模型 §6.1 记为 Argon2id"的过期描述；**结论不得记为 none**，记为"需文字同步、不改变用户可观察行为"），完成后方可转 clean。
- **UI 线框（TASK-UI-001 / ui-wireframe.md）继续冻结**：基线无效、不得评审。

---

## 当前任务

- **TASK-DM-001**：历史**已关闭**（对应 domain_model v1.1.3，批准锚点 `f64b6de`）。不重开；其成果由 v1.1.4 取代。
- **TASK-DM-002**：**已开启**（本轮）——领域模型 v1.1.3→v1.1.4 密码算法中性化修正，候选交付证据已补全，`verified_commit` 留空。**阻塞点：等待用户批准 domain_model v1.1.4**（由用户修改 baseline `domain_model.status`）。批准后再生成独立批准锚点（**不得复用 `f64b6de`**）并关闭本任务。
- **TASK-SRS-001**：开启中，`spec_sync=dirty`，等待上游 v1.1.4 获批后执行 SRS impact review；SRS 批准权在用户，AI 不代签。
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

> 注：当前门禁顺序为 —— ① 用户批准 **domain_model v1.1.4**（baseline `domain_model.status: review→approved`）→ ② 生成独立批准锚点并关闭 **TASK-DM-002** → ③ TASK-SRS-001 执行 **SRS impact review**（based_on.domain_model→1.1.4 + 修正 SRS §6.3 过期的 Argon2id 描述；结论 = "需文字同步、不改变用户可观察行为"，**不得记为 none**）→ spec_sync 转 clean → ④ 用户独立评审批准 **SRS**（AI 不代签）→ 关闭 TASK-SRS-001、用例规约冻结为历史输入或 SRS 附录 → ⑤ UI 线框重新 impact review 决定是否沿用 → 架构/ADR → 安全设计 → OpenAPI/SSE → 测试计划 → 开发准入评审 → 功能编码。`development_gate` 全 10 项 approved 前不得进入编码。

---

## 最后 verified commit（审计锚点）

Git 已初始化；审计锚点 = verified commit `adc7c8d3df42f0ecfb6dd846317ce6de04760cc5`（tag: gov-sync-001-verified；即治理收尾最终 commit，含 TASK-GOV-SYNC-001 关闭证据 + 全部治理文件 + 本锚点更新；机器锚点首选真实 SHA，tag 仅作人类别名；解析见 `git rev-parse gov-sync-001-verified`）。
本标签为 Review/Audit Mode（`AGENTS.md §9`）checkout 的快照——复盘时 AI 先 `git checkout gov-sync-001-verified`，再看其对应 approved specs，而非"读当前目录猜实现"。
本锚点不重复任何版本号（版本只在 `docs/baseline.yml`）。
