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
1. **密码算法裁定边界**：`password_hash` 当前按 Argon2id 设计、最终算法待《安全设计》ADR 裁定（PRD §8.7 BCrypt 冲突以安全设计为准），本阶段不预选、不冻结算法——边界清晰且符合"安全/架构 ADR 未出前不锁死算法"的工程判断。
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
- baseline.yml `domain_model.version` = "1.1.3"、status = approved
- 密码算法裁定边界、门禁引用、字段清理 3 类修改经本任务评审，均确认不改动领域实体/不变量
- 全仓 Grep 无 `purge_before` 残留、无"仅接口契约+测试计划通过即开放编码"误述

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
- commit / PR：<回填>
- 修改文件清单：<回填>
- 测试命令及结果：全仓一致性 Grep 校验（无 `purge_before` 残留 / 无门禁误述）；非执行测试
- lint / typecheck：不适用
- DB 迁移验证：不适用
- 验收证据：① 升版号三处一致（标题/整改段/页脚）；② baseline domain_model=1.1.3；③ 3 类修改评审结论（见「阶段性证据」）；④ Grep 无残留
- 变更预算实际值：<回填>
- 未解决风险：SRS 仍 status=review，待 TASK-SRS-001 完成 based_on 更新 + impact review + 用户批准
- 是否偏离 TASK：否（本任务即用户指令第 3 步的"独立领域模型修正任务"，追认 8794aea 越界改动属授权范围）
- 规范影响结论：deferred-to-srs（本任务升版触发 SRS based_on 更新与 impact review，不直接影响其他规范；impact 待 TASK-SRS-001 评估）
- spec_sync：clean（本任务仅升版 domain-model，不直接修改 SRS；SRS 的 based_on 同步与 impact review 由 TASK-SRS-001 在其开启态下处理）
- verified_commit：<回填真实 commit sha>

## 关闭结论
- 待用户/独立评审通过后填写（status 保持 Open 直至 SRS 经独立评审批准链路完成）。

## 阶段性证据
- 越界追认：8794aea 在 TASK-SRS-001 内修改 domain-model.md（§1/§6.1 密码裁定边界、§10 门禁引用、§9 purge 字段清理），已确认改动内容正确，于本任务下升版 v1.1.3 追认。
- 3 类修改评审结论：
  1. 密码算法裁定边界（§1 存储策略 + §6.1）：`password_hash` 当前按 Argon2id 设计、最终算法待《安全设计》ADR 裁定，PRD §8.7(BCrypt) 冲突以安全设计为准；本阶段不预选——边界符合"ADR 未出前不锁死算法"原则，无越权。
  2. 门禁引用（§10）：改引用 baseline `development_gate` 全 10 项，纠正"仅接口契约+测试计划通过即开放编码"误述——与 baseline 门禁一致。
  3. 字段清理（§9）：`purge_before→purge_after` 改名痕迹已清除，术语统一。

## 关联
- Change Request：无
- 上游越界来源：TASK-SRS-001（commit 8794aea）
- 下游影响：TASK-SRS-001（SRS based_on 更新至 domain_model 1.1.3 + impact review）
- 测试任务：无（文档）
