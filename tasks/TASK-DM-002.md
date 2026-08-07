# TASK-DM-002 领域模型密码算法中性化修正与升版（v1.1.3 → v1.1.4）

> 本任务单为 AI **仓库变更**的唯一范围约束。无任务单不得写入仓库，包括文档、设计、测试和代码变更。
> 本任务源于 2026-08-08 用户评审：领域模型 **v1.1.3 已在 `f64b6de` 获得正式批准**，其后 `236d302` 又修改了该版本的规范正文（5 处密码算法指向中性化）。**同一版本号不得对应批准前后两份不同内容**，也不得以"避免 SRS based_on 连锁变更"为由复用 1.1.3。故新开本独立任务，将该修正正式承载为 **v1.1.4**，1.1.3 保留为历史已批准版本（批准锚点 `f64b6de` 有效，其内容以该 commit 快照为准）。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3（approved）/ 用例规约 1.7.2（approved）/ 领域模型 1.1.3（历史已批准，锚点 `f64b6de`；升版目标 1.1.4）/ SRS 1.0（review）/ AI 治理 1.0.1（approved）——取自 `docs/baseline.yml`
- 基线 commit：`f64b6de852f99007a0073636c834d31c81ae1864`（domain_model v1.1.3 的正式批准锚点，本任务以该已批准内容为升版起点）
- 相关既有 commit：`236d302`（算法中性化正文改动，已落地但当时错误地仍挂 1.1.3 版本号；本任务将其正式归入 1.1.4 并补齐版本号/整改记录/页脚一致性）

## 精确规范引用（AI 只读取这些章节）
- 领域模型 v1.1.3：§1 范围与边界（存储策略）/ §2.3 类图 User / §4 ER 图 USER / §6.1 User 实体字段语义
- baseline.yml：artifacts / precedence / development_gate
- PRD v2.3.3：§8.7（密码哈希记为 BCrypt）
- SRS v1.0（review）：§6.3（加密与留存，含"领域模型 §6.1 记为 Argon2id"的过期描述——**本任务不修改 SRS**，由下游 TASK-SRS-001 在 impact review 中处理）

## 需求来源
- 用户 2026-08-08 评审指令第 2–4 步：新建独立 TASK-DM-002 承载密码算法中性化修正；领域模型升版 1.1.4（标题/整改记录/页脚/baseline 一致，status=review）；明确"领域模型只规定存密码哈希、不存明文，具体算法待 Security ADR"，并规定 Security ADR 与 PRD §8.7 BCrypt 不一致时**必须触发规范影响/变更评审，不得直接实现**。
- 缺陷事实（P0）：v1.1.3 正文 5 处仍将实现指向 Argon2id（§1 存储策略、§2.3 类图、§4 ER 图、§6.1 字段表、顶部整改记录），与"领域模型不预选算法"的边界声明自相矛盾。

## 目标
将 `docs/design/domain-model.md` 由 v1.1.3 升版至 **v1.1.4**，正式承载密码算法中性化修正：
1. **算法中性**：领域模型仅规定 `password_hash` 存储密码哈希（不存明文），**不预选任何具体哈希算法**；算法裁定权归《安全设计》ADR。涉及 §1 存储策略、§2.3 类图 User、§4 ER 图 USER、§6.1 字段表共 4 处规范正文 + 顶部整改记录。
2. **冲突升级条款**：若《安全设计》ADR 的裁定结果与 **PRD §8.7 记载的 BCrypt 不一致**，必须触发**规范影响评审 / 变更请求（Change Request）**，由评审决定更新 PRD 或采纳 ADR，**不得跳过评审直接按 ADR 实现**。
3. **版本一致性**：标题、顶部整改记录、页脚三处版本号一致为 v1.1.4；`docs/baseline.yml` 的 `domain_model` 同步为 `version: "1.1.4" / status: review`。
4. **历史批准不否认**：v1.1.3 的批准事实与锚点 `f64b6de` 予以保留，整改记录中如实标注"1.1.3 后续发现算法锁定缺陷，已由 v1.1.4 取代"。

## 非目标（明确排除）
- 不修改领域实体、属性、关系、状态机、业务不变式、并发约束（仅密码算法表述中性化）
- **不预选密码哈希算法**（Argon2id / BCrypt / 其他之裁定留《安全设计》ADR）
- 不修改 PRD §8.7 的 BCrypt 记载（其与 ADR 的冲突走变更评审，不在本任务处理）
- 不修改 SRS 正文（含 §6.3 过期描述）——归下游 TASK-SRS-001 的 impact review
- 不更新 `baseline.srs.based_on.domain_model`（须保留 1.1.3 以使机器门禁正确报 needs impact check）
- 不做 UI 线框 / 架构 / OpenAPI / 测试计划 / 编码
- **不得代签 `domain_model.status: approved`**

## 允许修改路径
- docs/design/domain-model.md   # 升版 v1.1.3→v1.1.4（标题 / 整改记录 / 页脚）+ 算法中性化正文 + 冲突升级条款
- docs/baseline.yml              # 仅 `domain_model: version "1.1.3"→"1.1.4"、status: review`；**不得改 srs.based_on**
- tasks/TASK-DM-002.md          # 本任务单自身回填交付证据

## 禁止修改路径
- docs/requirements/PRD.md / use-cases.md / SRS.md（仅引用，不改）
- tasks/TASK-SRS-001.md 的业务范围（其 spec_sync 状态由本轮治理修正单独说明，不改其任务范围）
- docs/design/ui-wireframe.md / tasks/TASK-UI-001.md（继续冻结）
- docs/experiments/deferred/l2-persona-training.md
- docs/references/agent-engineering-frameworks.md
- 任何代码文件、数据库迁移、OpenAPI / SSE 契约

## 已批准的 DB / API / 依赖变更
- 无（纯文档升版，无 schema / API / 依赖变更）

## 功能验收
- domain-model.md 升版至 v1.1.4，标题 / 顶部整改记录 / 页脚三处版本号一致
- baseline.yml `domain_model.version` = "1.1.4"、`status` = review（**未代签 approved**）
- domain-model.md 规范正文中**不存在任何指向具体密码哈希算法的实现描述**（Grep：`Argon2id` 仅出现在"不预选 Argon2id/BCrypt"这类否定性边界表述与历史整改记录中，不作为实现指向）
- §1 存储策略含冲突升级条款：Security ADR 与 PRD §8.7 BCrypt 不一致 → 触发规范影响/变更评审，不得直接实现
- v1.1.3 历史批准事实与锚点 `f64b6de` 在整改记录中保留，未被描述为"从未发生"
- `baseline.srs.based_on.domain_model` 仍为 "1.1.3"（机器门禁应报 needs impact check）

## 安全与隐私验收
- 不引入新敏感字段；不降格既有加密/密钥/鉴权策略
- 密码存储边界只增强不削弱：明确"仅存哈希、不存明文"；算法裁定权上移至《安全设计》ADR 并附冲突升级要求

## 性能验收
- 不适用（纯文档）

## 变更预算（change_budget）
- max_files：3（domain-model.md / baseline.yml / 本任务单）
- expected_prod_lines：小幅（版本号 3 处 + 整改记录段 + 冲突升级条款，约 10–15 行）
- expected_test_lines：0

## 必须运行的测试命令
- 无（文档任务）；交付前执行一致性 Grep 校验（版本号三处一致 / 算法指向清零 / based_on 保留 1.1.3）

## 回滚方法
- 使用 git revert / git restore；本任务不产生迁移；**不重写 Git 历史**

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「允许修改路径」列明，而不是看变更类型本身。**
- **可继续**：变更已在「允许修改路径」列明且为文档升版/评审性质。
- **必须立即停止并报告**：出现任何未在「允许修改路径」列明的变化，包括但不限于——修改 PRD/SRS/UI 正文、更新 `srs.based_on`、预选密码算法、改动实体或不变量、把 `domain_model.status` 置 approved。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
> 以下为**候选交付证据**（用户批准 v1.1.4 前不得据此关闭任务）。`verified_commit` 留空，待用户批准后由独立批准锚点回填。

- commit / PR：<回填 — 本轮升版提交 SHA>
- 修改文件清单：docs/design/domain-model.md（v1.1.3→v1.1.4 标题/整改记录/页脚 + 算法中性化 4 处正文 + §1 冲突升级条款）、docs/baseline.yml（domain_model 1.1.3→1.1.4、status=review）、tasks/TASK-DM-002.md（本任务单）
- 测试命令及结果：一致性 Grep 校验（结论见下「一致性检查结果」）；非执行测试
- lint / typecheck：不适用
- DB 迁移验证：不适用
- 验收证据：① 版本号三处一致为 1.1.4；② baseline domain_model=1.1.4/review；③ 规范正文无具体算法实现指向；④ §1 含冲突升级条款；⑤ srs.based_on.domain_model 仍 1.1.3（门禁报 needs impact check）；⑥ v1.1.3 批准锚点 f64b6de 保留于整改记录
- 变更预算实际值：max_files=3，实际 3 文件；prod 行数小幅（版本号 3 处 + 整改记录段 + 冲突升级条款）；test_lines=0；未超预算
- 一致性检查结果（Grep 校验，2026-08-08）：<回填>
- 未解决风险：`domain_model` 1.1.4 处于 review，**待用户独立评审批准**；下游 SRS 的 based_on 仍指向 1.1.3，需 TASK-SRS-001 在 1.1.4 批准后执行 impact review（结论不得记为 none，至少为"需文字同步、不改变用户可观察行为"）
- 是否偏离 TASK：否
- 规范影响结论：**downstream_pending** — 对 SRS 有**文字同步级**影响（SRS §6.3 现称"领域模型 §6.1 记为 Argon2id"，1.1.4 后该描述过期），**不改变用户可观察行为**；处理归 TASK-SRS-001
- spec_sync：dirty（v1.1.4 未获批准；下游 SRS based_on 未同步，impact review 未执行）
- verified_commit：<回填 — 待用户批准 domain_model v1.1.4 后生成独立批准锚点；不得复用 f64b6de（该锚点属旧版 1.1.3）>

## 关闭条件（明确，无循环）
本任务关闭前提仅为以下两项同时满足：
1. `domain_model` v1.1.4 经**用户明确批准**（由用户修改 `docs/baseline.yml` 的 `domain_model.status` 为 approved）；
2. 独立批准锚点（新 `verified_commit`，**不得复用 f64b6de**）与上述交付证据补全。

**SRS 的 `based_on` 同步与 impact review 由下游 TASK-SRS-001 独立负责，不构成本任务关闭条件。**

## 阶段性证据
- 缺陷定位（P0，用户 2026-08-08 评审）：v1.1.3 正文 5 处仍锁定 Argon2id —— 顶部整改记录、§1 存储策略、§2.3 类图 `password_hash string "Argon2id"`、§4 ER 图 `string password_hash "Argon2id"`、§6.1 字段表"当前按 Argon2id 设计"。
- 版本治理判定：v1.1.3 已于 `f64b6de` 正式批准，`236d302` 事后修改其规范正文 → 同一版本号出现批准前后两份内容，属版本完整性破坏。修正方式 = **升版 1.1.4 承载修改**，而非复用 1.1.3；1.1.3 及其锚点作为历史事实保留。
- 中性化落点（归入 1.1.4）：① §1 —— "`password_hash` 存储密码哈希（不存明文），具体哈希算法待《安全设计》ADR 裁定" + 冲突升级条款；② §2.3 类图 / §4 ER 图 —— 注释改 `algorithm pending Security ADR`；③ §6.1 字段表 —— "算法待《安全设计》ADR 裁定（不预选 Argon2id/BCrypt）"。
- 下游标记：`baseline.srs.based_on.domain_model` **有意保留 1.1.3**，使机器门禁（based_on ≠ current）正确报 needs impact check；TASK-SRS-001 `spec_sync` 置 dirty。

## 关联
- Change Request：无（但已写入"Security ADR 与 PRD §8.7 冲突须走 Change Request"的前置条款）
- 前序任务：TASK-DM-001（v1.1.2→v1.1.3，已关闭；批准锚点 `f64b6de`；其成果因 P0 算法锁定缺陷由本任务取代）
- 下游影响：TASK-SRS-001（v1.1.4 批准后执行 SRS impact review：更新 `srs.based_on.domain_model`→1.1.4 + 修正 SRS §6.3 过期描述）
- 冻结任务：TASK-UI-001 / ui-wireframe.md（继续冻结，基线无效、不得评审）
- 测试任务：无（文档）
