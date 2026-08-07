# 项目长期记忆 — 个人 AI 问答网站 + 面试预约系统

## 治理纪律（高优先级，跨会话恒成立）

1. **状态推进由用户显式操作 baseline，AI 不得自批准。**
   - `docs/baseline.yml` 是版本/状态/门禁唯一规范源。`review → approved` 等状态推进必须由用户修改 baseline 完成。
   - **关键陷阱（2026-08-07 真实教训）**：用户说"完成后 X 可以批准"是**展望性许可，不等于"现在批准"**。AI 不得基于"最有利解读"把展望当授权，直接置 approved 并启动下游阶段。读授权须保守；边界模糊时保持当前状态、向用户确认。

2. **单一任务单一工件。**
   - 跨工件修改（如 SRS 任务内改 domain-model）必须建独立任务追认，不得混改。越界改动须记录并新建任务评审（见 TASK-DM-001 追认 8794aea 模式）。

3. **三者一致性检查。**
   - 每次产物状态推进，必须检查 `baseline + PROJECT_STATE + current TASK` 三者一致性，而非只看新文件写完（用户明确要求）。

4. **向前修正，不重写 Git 历史。**
   - 误提交用新 commit 逆转状态（revert 语义），不得 `git reset`/`rebase` 删除已提交历史。

5. **版本完整性：已批准工件不得原地改内容（2026-08-08 真实教训）。**
   - 批准是**版本级事实**。一旦某版本被批准（有批准锚点 commit），其规范正文即冻结。要改 → **必须升新版本号**承载。
   - **禁止**把已批准版本从 approved 回退成 review 再改内容——那等于让同一版本号对应批准前后两份内容，也等于把已发生的批准描述成从未发生。
   - **禁止**以"避免下游 based_on 连锁变更"为由复用已批准版本号。连锁成本不是版本完整性的豁免理由。
   - 历史批准锚点必须保留，并如实标注"已被 vX 取代"（见 TASK-DM-001 / f64b6de / v1.1.3 → TASK-DM-002 / v1.1.4 模式）。

6. **上游升版后，下游 based_on 应有意滞后。**
   - 让 `based_on ≠ current` 使机器门禁自然报 `needs impact check`，下游 TASK 的 `spec_sync` 置 dirty；**不要抢先同步 based_on**。
   - impact review 若涉及下游文字过期（如 SRS §6.3 记 Argon2id），**结论不得记 none**，应记"需文字同步、不改变用户可观察行为"。

7. **任务单必须如实登记实际改动范围（2026-08-08 教训）。**
   - 授权 ≠ 登记。即使改动来自用户明确授权，只要「允许修改路径」与 `change_budget.max_files` 未列明，就构成**任务范围账目偏差**，「是否偏离 TASK」不得写"否"。
   - 收尾前须核对四处一致：允许修改路径 / `change_budget.max_files` / 修改文件清单 / 变更预算实际值，且与 `git show <sha> --stat` 的文件数吻合。
   - 治理文件（其他 TASK 单、`PROJECT_STATE.md`）的修改同样要列明并注明授权来源（用户第几步指令）。

8. **冲突升级条款不得允许规范并存冲突。**
   - 正确写法：ADR 拟选方案与已批规范（如 PRD §8.7 BCrypt）不一致 → **先经 Change Request 更新并批准所有受影响规范，规范同步完成并获批准前不得实现**。
   - 错误写法：「由评审决定更新 PRD 或采纳 ADR」——这允许 ADR 与规范长期冲突并存。

9. **不得把后续版本成果反写进历史版本。**
   - 批准时点快照有什么缺陷就如实记什么。历史评审结论可被限定为"不完整/事后被证伪"，但不得追认为"当时已完成"。
   - 例：v1.1.3 在 `f64b6de` 批准时仍含 5 处 Argon2id 实现指向 → 算法彻底中性化只能计入 v1.1.4 / TASK-DM-002。

## 当前阶段（2026-08-08 版本完整性修正后）
- baseline：`domain_model=1.1.4 / approved`（用户 2026-08-08 明确批准，独立锚点 `f537296`，不复用 `f64b6de`；v1.1.3 已于 `f64b6de` 正式批准并保留为历史，因 P0 算法锁定缺陷由 v1.1.4 取代）、`srs=1.0 / review`（`based_on.domain_model`=1.1.4，TASK-SRS-001 `spec_sync=clean` 已完成 impact review）、`ui_wireframe=pending`（冻结、不得评审）。
- 任务态：TASK-DM-001 历史已关闭（不重开，已追记"历史结论不完整"限定）；**TASK-DM-002 已关闭（Closed，2026-08-08）**（v1.1.4 算法中性化，账目已对齐 6 文件、`change_budget.max_files=6`、「是否偏离 TASK」=是（账目层面）、`verified_commit`=`f537296` 独立批准锚点不复用 f64b6de）；TASK-SRS-001 开启（spec_sync=clean，impact review 已完成，待用户独立批准 SRS 后关闭）；TASK-UI-001 冻结。
- 提交链（2026-08-08）：`ac1745a` → `e31ad11` → `8135257`（关闭门禁修正）→ `deb3692`/`a9eb262`（证据回填）→ `82d0ab2`（门禁+顺序修正）→ `f537296`（v1.1.4 批准锚点）→ `d166992`（SRS impact review）→ `94bedb5`（TASK-DM-002 关闭收口）。
- 待办顺序：用户批准 v1.1.4 ✅（锚点 f537296）+ 关 TASK-DM-002 ✅ → SRS impact review ✅（based_on→1.1.4 + 修 SRS §6.3 过期 Argon2id 描述，spec_sync=clean）→ 用户批准 SRS ⏳ → 关 TASK-SRS-001 → UI 重新 impact review → 架构/ADR → 安全设计 → OpenAPI/SSE → 测试计划。
- 密码哈希算法裁定留《安全设计》ADR；**若 ADR 与 PRD §8.7（BCrypt）不一致，必须触发规范影响/变更评审，不得直接实现**（已写入 domain-model §1 冲突升级条款）。
- 不得继续架构/API/测试计划/编码阶段，直到 development_gate 全 10 项 approved。
