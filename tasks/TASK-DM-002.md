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
- 用户 2026-08-08 评审指令第 2–4 步：新建独立 TASK-DM-002 承载密码算法中性化修正；领域模型升版 1.1.4（标题/整改记录/页脚/baseline 一致，status=review）；明确"领域模型只规定存密码哈希、不存明文，具体算法待 Security ADR"，并规定 Security ADR 拟选算法与 PRD §8.7 BCrypt 不一致时**必须先经 Change Request 更新并批准受影响规范，规范同步完成前不得实现**。
- 用户 2026-08-08 复核指令（第二轮）第 1–5 步：补列 3 个治理文件至允许修改路径、change_budget 改 6 并记录账目偏差、收紧冲突升级条款、修正 TASK-DM-001 历史结论、证据链记录三次提交。
- 缺陷事实（P0）：v1.1.3 正文 5 处仍将实现指向 Argon2id（§1 存储策略、§2.3 类图、§4 ER 图、§6.1 字段表、顶部整改记录），与"领域模型不预选算法"的边界声明自相矛盾。

## 目标
将 `docs/design/domain-model.md` 由 v1.1.3 升版至 **v1.1.4**，正式承载密码算法中性化修正：
1. **算法中性**：领域模型仅规定 `password_hash` 存储密码哈希（不存明文），**不预选任何具体哈希算法**；算法裁定权归《安全设计》ADR。涉及 §1 存储策略、§2.3 类图 User、§4 ER 图 USER、§6.1 字段表共 4 处规范正文 + 顶部整改记录。
2. **冲突升级条款**：若《安全设计》ADR **拟选择的算法与 PRD §8.7 记载的 BCrypt 不一致**，必须**先通过变更请求（Change Request）更新并批准所有受影响的规范**（至少含 PRD §8.7 与 SRS 相关条款）；**规范同步完成并获批准前，不得按该 ADR 实现**。不得写成"由评审决定更新 PRD 或采纳 ADR"——该表述允许规范继续冲突并存，已废弃。
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

> **账目更正（2026-08-08 用户复核）**：初版本任务单只列了下方前 3 条，但 `ac1745a` 实际修改了 6 个文件。遗漏列明的 3 个**治理文件**修改来自**用户 2026-08-08 十步纠偏指令的明确授权**（第 1 步恢复 TASK-DM-001 历史已关闭、第 5 步置 TASK-SRS-001 spec_sync=dirty、第 6 步修正 PROJECT_STATE），并非越权改动；但**初版任务单遗漏列明属任务范围账目偏差**，现如实补入，不得再声称"无偏离"或"实际仅 3 文件"。

- docs/design/domain-model.md   # 升版 v1.1.3→v1.1.4（标题 / 整改记录 / 页脚）+ 算法中性化正文 + 冲突升级条款
- docs/baseline.yml              # 仅 `domain_model: version "1.1.3"→"1.1.4"、status: review`；**不得改 srs.based_on**
- tasks/TASK-DM-002.md          # 本任务单自身回填交付证据
- tasks/TASK-DM-001.md          # 【补列，授权来源=用户指令第 1 步】恢复历史已关闭状态、保留 f64b6de 为 v1.1.3 真实批准锚点、追记版本取代声明与历史结论限定；**不改其 v1.1.3 时点的任务范围与目标**
- tasks/TASK-SRS-001.md         # 【补列，授权来源=用户指令第 5 步】仅将 `spec_sync` 由 clean 回退 dirty 并登记待办 impact review 口径；**不改其业务范围/验收/目标**
- PROJECT_STATE.md              # 【补列，授权来源=用户指令第 6 步】同步当前态：domain_model 1.1.4 review / TASK-DM-002 开启 / SRS 待下游 impact review / UI 继续冻结

## 禁止修改路径
- docs/requirements/PRD.md / use-cases.md / SRS.md（仅引用，不改）
- tasks/TASK-SRS-001.md 的**业务范围 / 目标 / 验收**（仅允许改 `spec_sync` 状态与 impact review 待办口径，见「允许修改路径」补列项）
- tasks/TASK-DM-001.md 的 **v1.1.3 时点任务范围 / 目标 / 验收判据**（仅允许恢复关闭状态与追记版本取代声明、历史结论限定）
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
- §1 存储策略含冲突升级条款：Security ADR 拟选算法与 PRD §8.7 BCrypt 不一致 → **先经 Change Request 更新并批准受影响规范（PRD/SRS），规范同步完成前不得按该 ADR 实现**（不得表述为"由评审决定更新 PRD 或采纳 ADR"）
- 「允许修改路径」如实覆盖本任务实际修改的全部 6 个文件；`change_budget.max_files` = 6；账目偏差已书面记录
- v1.1.3 历史批准事实与锚点 `f64b6de` 在整改记录中保留，未被描述为"从未发生"
- `baseline.srs.based_on.domain_model` 仍为 "1.1.3"（机器门禁应报 needs impact check）

## 安全与隐私验收
- 不引入新敏感字段；不降格既有加密/密钥/鉴权策略
- 密码存储边界只增强不削弱：明确"仅存哈希、不存明文"；算法裁定权上移至《安全设计》ADR 并附冲突升级要求

## 性能验收
- 不适用（纯文档）

## 变更预算（change_budget）
- max_files：**6**（修订自初版的 3；初版遗漏列明 3 个治理文件，属任务范围账目偏差，已在「允许修改路径」如实补入）
  1. docs/design/domain-model.md
  2. docs/baseline.yml
  3. tasks/TASK-DM-002.md
  4. tasks/TASK-DM-001.md
  5. tasks/TASK-SRS-001.md
  6. PROJECT_STATE.md
- expected_prod_lines：小幅（规范正文：版本号 3 处 + 整改记录段 + 冲突升级条款，约 10–15 行；治理文件：状态/证据字段调整，约 25–40 行）
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

- commit / PR（**完整证据链，3 次提交**）：
  1. `ac1745a` — 主修正：domain-model v1.1.3→v1.1.4 升版与算法中性化 + baseline 同步 + TASK-DM-001 恢复历史已关闭 + TASK-DM-002 新建 + TASK-SRS-001 spec_sync→dirty + PROJECT_STATE 同步（**实际改动 6 文件**）
  2. `e31ad11` — 候选交付证据首次回填（本任务单 7 项一致性 Grep 结论）
  3. `8135257` — 用户第二轮复核修正：允许路径补列 3 个治理文件、change_budget 3→6、账目偏差书面记录、冲突升级条款收紧、TASK-DM-001 历史结论限定（改动文件：domain-model.md / TASK-DM-002.md / TASK-DM-001.md，均在修订后允许路径内）
  4. `<本条目自身的证据回填提交>` — 仅回填上条 SHA 至本任务单，无规范正文改动
- 修改文件清单（**实际 6 个，与 `ac1745a --stat` 一致**）：
  1. docs/design/domain-model.md — v1.1.3→v1.1.4 标题/整改记录/页脚 + 算法中性化 4 处正文 + §1 冲突升级条款
  2. docs/baseline.yml — `domain_model` 1.1.3→1.1.4、status=review
  3. tasks/TASK-DM-002.md — 本任务单（新建 + 证据回填 + 本轮账目修正）
  4. tasks/TASK-DM-001.md — 恢复历史已关闭、保留 f64b6de 锚点、追记版本取代声明与历史结论限定
  5. tasks/TASK-SRS-001.md — 仅 `spec_sync` clean→dirty 与 impact review 待办口径
  6. PROJECT_STATE.md — 当前态同步
- 测试命令及结果：一致性 Grep 校验（结论见下「一致性检查结果」）；非执行测试
- lint / typecheck：不适用
- DB 迁移验证：不适用
- 验收证据：① 版本号三处一致为 1.1.4；② baseline domain_model=1.1.4/review；③ 规范正文无具体算法实现指向；④ §1 含冲突升级条款；⑤ srs.based_on.domain_model 仍 1.1.3（门禁报 needs impact check）；⑥ v1.1.3 批准锚点 f64b6de 保留于整改记录
- 变更预算实际值：**max_files=6（修订后），实际 6 文件**；prod 行数小幅（规范正文版本号 3 处 + 整改记录段 + 冲突升级条款；治理文件状态/证据字段调整）；test_lines=0；**未超修订后预算**。
  - **账目偏差记录（必读）**：初版本任务单的「允许修改路径」与 `change_budget.max_files` 只覆盖 3 个文件，而 `ac1745a` 实际修改 **6 个文件**——遗漏列明的 3 个为治理文件（`tasks/TASK-DM-001.md`、`tasks/TASK-SRS-001.md`、`PROJECT_STATE.md`）。这 3 项修改**有用户 2026-08-08 十步纠偏指令的明确授权**（第 1/5/6 步），**不属越权实现**，但**属于任务范围账目偏差**（任务单未如实登记授权范围）。已于本轮如实补入允许路径并把预算改为 6。**此后不得再声称"无偏离"或"实际仅 3 文件"。**
- 一致性检查结果（Grep 校验，2026-08-08，commit `ac1745a`）：
  1. **版本号三处一致**：`grep -n "v1\.1\.4" docs/design/domain-model.md` → 标题（L1）、整改记录（L8，另 L7 为 1.1.3 历史记录）、页脚（L629）均为 v1.1.4。
  2. **规范正文算法指向清零**：`grep -n "Argon2id" docs/design/domain-model.md` → 仅命中 L7（v1.1.3 历史整改记录，如实描述旧版内容与其缺陷）与 L8（v1.1.4 整改记录中的否定性表述"原 Argon2id 实现指向全部清除"）。§1 存储策略 / §2.3 类图 `User` / §4 ER 图 `USER` / §6.1 字段表**均无算法实现指向**（类图与 ER 图注释为 `algorithm pending Security ADR`）。
  3. **baseline 状态**：`docs/baseline.yml` L16 `domain_model: { version: "1.1.4", status: review }`（**未代签 approved**）。
  4. **下游门禁有意滞后**：`docs/baseline.yml` L20 `srs.based_on.domain_model: "1.1.3"` 保留 → `based_on(1.1.3) ≠ current(1.1.4)`，机器门禁应报 **needs impact check**；注释已写明该滞后为有意设置。
  5. **冲突升级条款存在且已收紧**（2026-08-08 复核修正）：domain-model §1 存储策略 `password_hash` 条目下含"若《安全设计》ADR **拟选择的算法**与 PRD §8.7 记载的 BCrypt 不一致，必须**先通过变更请求（Change Request）更新并批准所有受影响的规范**（至少含 PRD §8.7 及 SRS 相关条款）；**在规范同步完成并获批准之前，不得按该 ADR 实现**"；顶部 v1.1.4 整改记录（L8）与 §6.1 字段表同步该口径。原"由评审决定更新 PRD 或采纳 ADR"表述**已删除**（该写法允许规范继续冲突并存）。
  6. **历史批准未被否认，且历史结论已如实限定**：domain-model L7 与 `tasks/TASK-DM-001.md`（关闭结论 / verified_commit / 关联）均保留 `f64b6de` 为 v1.1.3 的真实批准锚点，注明"已由 v1.1.4 取代、本任务不重开"；**并追记历史结论限定**——`f64b6de` 快照的 v1.1.3 仍含 5 处 Argon2id 实现指向，当时"不预选算法"的评审判断**不完整**，算法彻底中性化属 **v1.1.4 / TASK-DM-002**，未反写为 v1.1.3 已完成（追记落点：TASK-DM-001 目标①、功能验收、未解决风险、关闭结论、阶段性证据评审结论①）。
  7. **UI 冻结未变**：`docs/design/ui-wireframe.md` 与 `tasks/TASK-UI-001.md` 顶部"基线无效 / 不得评审"标记未改动。
- 未解决风险：`domain_model` 1.1.4 处于 review，**待用户独立评审批准**；下游 SRS 的 based_on 仍指向 1.1.3，需 TASK-SRS-001 在 1.1.4 批准后执行 impact review（结论不得记为 none，至少为"需文字同步、不改变用户可观察行为"）
- 是否偏离 TASK：**是（账目层面偏离，已如实登记并修正）** —— `ac1745a` 修改的 6 个文件中，3 个治理文件（TASK-DM-001.md / TASK-SRS-001.md / PROJECT_STATE.md）未在初版任务单「允许修改路径」与 `change_budget` 中列明。**性质**：实现层面有用户十步纠偏指令的明确授权，非越权改动；**但任务单登记不实，属任务范围账目偏差**。**处置**：本轮已补列允许路径、`max_files` 3→6、实际值改 6 并书面记录偏差成因。**不得再声称"无偏离"。**
- 规范影响结论：**downstream_pending** — 对 SRS 有**文字同步级**影响（SRS §6.3 现称"领域模型 §6.1 记为 Argon2id"，1.1.4 后该描述过期），**不改变用户可观察行为**；处理归 TASK-SRS-001
- spec_sync：dirty（v1.1.4 未获批准；下游 SRS based_on 未同步，impact review 未执行）
- verified_commit：<回填 — 待用户批准 domain_model v1.1.4 后生成独立批准锚点；不得复用 f64b6de（该锚点属旧版 1.1.3）>

## 关闭条件（明确，无循环）
本任务关闭前提为以下三项同时满足：
1. `domain_model` v1.1.4 经**用户明确批准**（由用户修改 `docs/baseline.yml` 的 `domain_model.status` 为 approved）；
2. 独立批准锚点（新 `verified_commit`，**不得复用 f64b6de**）与上述交付证据补全；
3. **任务范围账目与实际改动一致**——「允许修改路径」「change_budget.max_files」「修改文件清单」「变更预算实际值」四处均为 6 且互相吻合，账目偏差已书面记录（2026-08-08 用户第二轮复核门禁项）。

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
