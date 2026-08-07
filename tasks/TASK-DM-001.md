# TASK-DM-001 领域模型独立修正与升版（v1.1.2 → v1.1.3）

> 本任务单为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。
> 本任务源于 2026-08-07 用户纠偏：上轮 `8794aea` 在 TASK-SRS-001 小范围收口内**越界修改了 `docs/design/domain-model.md`**（TASK-SRS-001 禁止修改领域模型），现于独立任务下追认、升版并评审，恢复"单一任务单一工件"的治理约束。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.2（升版目标 1.1.3）/ SRS 1.0（review）/ AI 治理 1.0.1（取自 `docs/baseline.yml`）
- 基线 commit：`e7489c6aeab98f346b971f7015926365065ce9de`（误批准回退后 HEAD；本任务基于该快照启动）

## 精确规范引用（AI 只读取这些章节）
- 领域模型 v1.1.2：§1 范围与边界（存储策略）/ §6.1 实体字段语义与并发约束 / §9 数据留存与清理 / §10 编码准入说明
- baseline.yml：development_gate / mvp_hard_rules / precedence
- PRD v2.3.3：§8.7（密码哈希 BCrypt 记录）
- SRS v1.0：§6.3（加密/留存/删除，待安全设计裁定表述）

## 需求来源
- 用户 2026-08-07 纠偏指令第 3 步：新建独立领域模型修正文档任务；领域模型升版，评审其密码算法裁定边界、门禁引用和字段清理。
- 越界事实：`8794aea` 已在 domain-model.md 落地 4 处修改（密码算法裁定边界 §1/§6.1、门禁引用 §10、purge 字段清理 §9），但不在 TASK-SRS-001 允许路径内；本任务将其追认为 v1.1.3 正式修正并评审。

## 目标
对 `docs/design/domain-model.md` 升版至 v1.1.3，将 `8794aea` 已落地的 4 处修改作为独立任务的正式修正进行评审与留痕；确认：
1. **密码算法裁定边界**：`password_hash` 仅规定存储密码哈希（不存明文），具体哈希算法待《安全设计》ADR 裁定，领域模型不预选 Argon2id/BCrypt——边界清晰且符合"安全/架构 ADR 未出前不锁死算法"的工程判断。
2. **门禁引用**：§10 编码准入说明改引用 baseline `development_gate` 全 10 项门禁，纠正原"仅接口契约+测试计划通过即开放编码"误述。
3. **字段清理**：§9 遗留 `purge_before→purge_after` 改名痕迹已清除，术语一致。
并同步更新 `docs/baseline.yml` 的 `domain_model.version` 至 1.1.3，作为 SRS impact review 的升版锚点。

## 非目标（明确排除）
- 不修改领域实体、属性、关系、状态机、业务不变式、并发约束（仅评审既有 4 处修改的边界正确性）
- 不预选密码哈希算法（Argon2id / BCrypt 之裁定留《安全设计》ADR）
- 不修改 PRD / 用例规约 / SRS 业务内容（SRS based_on 更新与 impact review 由 TASK-SRS-001 承载）
- 不做 UI 线框 / 架构 / OpenAPI / 测试计划 / 编码

## 允许修改路径
- docs/design/domain-model.md        # 升版号 v1.1.3 + 整改说明段（追认 8794aea 的 4 处修改，仅评审留痕，不改业务逻辑）
- docs/baseline.yml                   # 仅 `domain_model.version: "1.1.2"→"1.1.3"`
- tasks/TASK-DM-001.md               # 本任务单自身回填交付证据

## 禁止修改路径
- PRD / 用例规约 / SRS 业务内容（仅引用，不改）
- UI 线框 / 架构 / OpenAPI / 测试计划
- docs/experiments/deferred/l2-persona-training.md
- docs/references/agent-engineering-frameworks.md
- 任何代码文件、数据库迁移、OpenAPI / SSE 契约

## 已批准的 DB / API / 依赖变更
- 无（纯文档升版，无 schema / API / 依赖变更）

## 功能验收
- domain-model.md 升版至 v1.1.3（标题 + 整改说明段 + 页脚版本号一致）
- baseline.yml `domain_model.version` = "1.1.3"、status = review（2026-08-08 经用户批准后发现 P0 算法锁定缺陷，重新开启修正；待用户重新评审批准）
- 密码算法裁定边界、门禁引用、字段清理 3 类修改经本任务评审，均确认不改动领域实体/不变量
- 活动规范正文（domain-model.md）无 `purge_before` 残留字段、无"仅接口契约+测试计划通过即开放编码"误述（任务文件中的 purge_before 为历史清理记录引用，非活动残留）

## 安全与隐私验收
- 不引入新敏感字段；密码算法维持"待安全设计裁定"边界，不降格

## 性能验收
- 不适用（纯文档）

## 变更预算（change_budget）
- max_files：3（domain-model.md / baseline.yml / 本任务单）
- expected_prod_lines：小幅（升版号 + 整改说明段）
- expected_test_lines：0

## 必须运行的测试命令
- 无（文档任务）；交付前执行全仓一致性 Grep 校验

## 回滚方法
- 使用 git revert / git restore；本任务不产生迁移

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「允许修改路径」列明，而不是看变更类型本身。**
- **可继续**：变更已在「允许修改路径」列明且为文档升版/评审性质。
- **必须立即停止并报告**：出现任何未在「允许修改路径」列明的变化（含修改 PRD/SRS/UI、新增依赖、改动实体不变量等）。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：b8eba4db35d1c4b02d16a5f6d431406cb7d6ef6b（b8eba4d，TASK-DM-001 升版与评审提交；领域模型 1.1.3 当前 status=review，待用户批准）
- 修改文件清单：docs/design/domain-model.md（升版号 v1.1.3 标题/整改说明段/页脚 + 追认 8794aea 的 4 处修改评审留痕）、docs/baseline.yml（domain_model.version 1.1.2→1.1.3）、tasks/TASK-DM-001.md（本任务单）
- 测试命令及结果：全仓一致性 Grep 校验（结论见下「一致性检查结果」）；非执行测试
- lint / typecheck：不适用
- DB 迁移验证：不适用
- 验收证据：① 升版号三处一致（标题/整改段/页脚）；② baseline domain_model=1.1.3；③ 3 类修改评审结论（见「阶段性证据」）；④ Grep 无残留
- 变更预算实际值：max_files=3、实际 3 文件（domain-model.md / baseline.yml / TASK-DM-001.md）；prod 行数小幅（升版号 3 处 + 整改说明段约 6 行，共约 9 行）；test_lines=0；未超出 TASK-DM-001 change_budget
- 一致性检查结果（Grep 校验，2026-08-07 首轮 + 2026-08-08 P0 修正轮）：① 活动规范正文（domain-model.md）无 `purge_before` 残留字段（已清除为 purge_after，§9）；任务文件中的 `purge_before` 为历史清理记录引用，非活动残留；② domain-model §10 门禁引用已改引用 baseline `development_gate` 全 10 项，无"仅接口契约+测试计划通过即开放编码"误述；③ domain-model 版本号三处（标题/整改说明段/页脚）一致为 1.1.3；④ baseline `domain_model.status` = review（P0 修正后重新开启，未代签 approved）；⑤ SRS based_on 已正式同步至 1.1.3（baseline 第 20 行）、TASK-SRS-001 spec_sync=clean（impact=none）；⑥ TASK-UI-001 / ui-wireframe.md 顶部标记"基线无效/不得评审"。
- 未解决风险：domain_model 1.1.3 因 P0 算法锁定缺陷重新开启（status=review），待用户重新评审批准；SRS 仍 status=review，待用户独立评审批准
- 是否偏离 TASK：否（本任务即用户指令第 3 步的"独立领域模型修正任务"，追认 8794aea 越界改动属授权范围）
- 规范影响结论：none（领域模型升版 3 类修改均不改实体/不变量/状态机，对 PRD/用例/SRS 行为无规范影响；SRS based_on 同步属 provenance，impact review 结论=none，无 normative 影响）
- spec_sync：clean（domain_model 1.1.3 已获用户明确批准；下游 SRS 的 based_on 同步与 impact review 由本轮 TASK-SRS-001 执行且结论=none，无 pending downstream）
- verified_commit：f64b6de852f99007a0073636c834d31c81ae1864（domain_model 1.1.3 批准锚点，本任务正式关闭；非 tag 占位）

## 关闭结论（2026-08-08 首次填写 — 因 P0 算法锁定缺陷已作废，本任务重新开启）

> **关闭条件（修订，消除循环）**：本任务关闭前提仅为——domain_model 1.1.3 经用户明确批准 + 批准锚点（verified_commit）与交付证据补全。**SRS 的 based_on 同步与 impact review 由下游 TASK-SRS-001 独立负责，不构成本任务关闭条件。**

（下方为首次关闭门禁复核记录；状态已回退为重新开启，待用户重新评审批准 domain_model 1.1.3 后据本规则重新填写关闭结论。）

1. **测试通过**：纯文档/升版任务，无代码/测试；一致性 Grep 校验通过（活动规范正文无 `purge_before` 残留字段 / §10 门禁引用 development_gate 全 10 项 / 版本号三处一致 / 无"仅接口契约+测试计划通过即开放编码"误述）。
2. **规范影响已处理**：规范影响结论 = none（3 类修改均不改实体/不变量/状态机，对 PRD/用例/SRS 行为无规范影响；SRS based_on 同步属 provenance，impact review 结论=none，无 normative 影响）。
3. **spec_sync = clean**：domain_model 1.1.3 已获用户明确批准；下游 SRS 的 based_on 同步与 impact review 由本轮 TASK-SRS-001 执行且结论=none，无 pending downstream。
4. **真实 verified_commit**：`f64b6de852f99007a0073636c834d31c81ae1864`（domain_model 1.1.3 首次批准锚点，因 P0 作废待重新生成）。

其他治理账目收正确认：
- 越界来源：8794aea 在 TASK-SRS-001 内改 domain-model.md（超出该任务允许路径）；本任务（TASK-DM-001）为独立追认载体，已获用户授权。
- 3 类修改评审结论（首次）：① 密码算法裁定边界——`password_hash` 待《安全设计》ADR 裁定，不预选算法，边界正确；② 门禁引用——§10 改引 baseline `development_gate` 全 10 项，与 baseline 一致；③ 字段清理——§9 `purge_before→purge_after` 改名痕迹已清除。
- 下游 SRS 同步：TASK-SRS-001 已于首轮将 `baseline.srs.based_on.domain_model` 由 1.1.2 同步至 1.1.3 并重做 impact review（结论=none，spec_sync 转 clean）。

状态：重新开启（Reopened — P0 算法仍锁定 Argon2id，待修正后重新评审批准）。

## 阶段性证据
- 越界追认：8794aea 在 TASK-SRS-001 内修改 domain-model.md（§1/§6.1 密码裁定边界、§10 门禁引用、§9 purge 字段清理），已确认改动内容正确，于本任务下升版 v1.1.3 追认。
- 3 类修改评审结论：
  1. 密码算法裁定边界（§1 存储策略 + §6.1）：`password_hash` 仅规定存储密码哈希（不存明文），具体哈希算法待《安全设计》ADR 裁定，领域模型不预选 Argon2id/BCrypt；PRD §8.7(BCrypt) 冲突以安全设计为准；本阶段不预选——边界符合"ADR 未出前不锁死算法"原则，无越权。
  2. 门禁引用（§10）：改引用 baseline `development_gate` 全 10 项，纠正"仅接口契约+测试计划通过即开放编码"误述——与 baseline 门禁一致。
  3. 字段清理（§9）：`purge_before→purge_after` 改名痕迹已清除，术语统一。

## 关联
- Change Request：无
- 上游越界来源：TASK-SRS-001（commit 8794aea）
- 下游影响：TASK-SRS-001（SRS based_on 更新至 domain_model 1.1.3 + impact review）
- 测试任务：无（文档）
