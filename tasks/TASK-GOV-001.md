# TASK-GOV-001 治理边界修正（.workbuddy 取消跟踪 + 锚点语义校正）

> 本任务单为 AI 仓库变更的唯一范围约束。无任务单不得写入仓库。
> **本任务授权范围严格限定**（见「允许修改路径」），超出范围的文件一律不得触碰。

## 任务类型
- governance（治理边界修正，非规范升版）

## 背景（缺陷事实）

- 2026-08-08 关闭 TASK-DM-002 后，提交 `f864937`（`docs(memory): 补记 TASK-DM-002 关闭收口…`）将 `.workbuddy/memory/*`（2026-08-07.md / 2026-08-08.md / MEMORY.md 等）提交进了项目 Git 历史。
- **边界违规**：`.workbuddy/` 是 WorkBuddy 的**工作目录**（本地记忆 / 运行态），**不属于项目治理证据**，不得进入项目 Git 历史。该提交属 TASK-DM-002 关闭后产生的**范围外提交**，不应作为项目治理证据被追溯。
- 修正方式 = **向前修正**：取消对 `.workbuddy/` 的 Git 跟踪并加入 `.gitignore`，**不重写或删除 `f864937` 历史**。

## 目标

1. **取消跟踪**：`git rm --cached -r .workbuddy/`，将整个 `.workbuddy/` 从 Git 索引移除，**保留本地文件**。
2. **忽略规则**：在 `.gitignore` 增加 `.workbuddy/`，使工作树不再将其列为未跟踪。
3. **锚点语义校正（TASK-DM-002）**：
   - `approval_commit` = `f537296`（domain_model v1.1.4 单一用途独立批准锚点）
   - `verified_commit` = `94bedb5`（已含 domain_model approved + SRS impact review/spec_sync=clean + TASK-DM-002 Closed 的完整验证快照）
   - 理由：`f537296` 发生时 `spec_sync` 仍为 dirty，**不能**兼任最终 `verified_commit`。
4. **PROJECT_STATE 同步**：凡把 `f537296` 误写为 `verified_commit` 处改 `94bedb5`；baseline 中 `f537296` 作为领域模型批准锚点的记录保持不变。
5. **如实记录**：`f864937` 系 TASK-DM-002 关闭后范围外提交，非项目治理证据，现已通过取消跟踪 + ignore 规则收口。

## 非目标（明确排除）

- 不修改任何规范正文（SRS.md / domain-model.md / PRD.md / use-cases.md）
- 不修改 `docs/baseline.yml` 的 `f537296` 批准锚点记录（保留为 domain_model 批准锚点）
- 不重新批准 SRS / 不代签
- 不推进 UI / 架构 / 安全设计 / OpenAPI / 测试计划 / 编码

## 允许修改路径（授权范围，严格限定「仅包括」以下 5 项）

- `.gitignore`                                  # 增加 `.workbuddy/` 忽略项
- （Git 索引操作）`git rm --cached -r .workbuddy/`   # 仅取消跟踪，保留本地文件
- `tasks/TASK-DM-002.md`                        # 仅锚点语义校正（approval_commit / verified_commit 两字段）
- `PROJECT_STATE.md`                            # 仅把 `f537296` 误写为 `verified_commit` 处改 `94bedb5`
- `tasks/TASK-GOV-001.md`                       # 本任务单自身

## 禁止修改路径（越界即停）

- `docs/baseline.yml`（本任务不触碰；其 `f537296` 批准锚点记录保持不变）
- `docs/requirements/*.md`、`docs/design/domain-model.md`、`docs/design/ui-wireframe.md`
- `tasks/TASK-SRS-001.md`、`tasks/TASK-DM-001.md`、`tasks/TASK-UI-001.md`
- 任何代码 / 契约 / 测试文件

## 变更预算（change_budget）

- max_files：**5**（原始预算声明；实际为 **12 个 Git 路径**，已超出预算，偏差见下 + TASK-GOV-002 追认）。
- 计数口径错误（TASK-GOV-002 追认）：原任务单将 `git rm --cached -r .workbuddy/` 产生的 **8 个 memory 文件取消跟踪** 合并记为「1 项索引操作」，未按**文件路径**逐条计数；正确应为 8 路径 + 4 文件 = **12 个 Git 路径**。
- expected_prod_lines：小幅（.gitignore 1 行 + TASK-DM-002 锚点字段 + PROJECT_STATE 1 处 + 本任务单）
- expected_test_lines：0

## spec_sync

- **clean（n/a）** —— 本任务不涉及任何规范版本（SRS / 领域模型 / PRD）的内容变更，无下游规范影响，机器门禁无需 impact check。

## 交付证据（任务关闭前必须填写）

- commit / PR：治理修正本身见本任务关闭提交（sha 见下「verified_commit」）；`94bedb5`（TASK-DM-002 关闭快照，仅引用，本任务不改动）作锚点校正依据。
- verified_commit：**`f56a47803137fe1c17c268492abd2f8404e18330`** —— 本治理修正提交（含 `.gitignore` + TASK-DM-002 锚点校正 + PROJECT_STATE 同步 + 本任务单 + 索引取消跟踪 `.workbuddy/`）。
- 取消跟踪操作：`git rm --cached -r .workbuddy/` → 8 个 memory 文件移出索引，工作树原文件保留。
- `.gitignore` 变更：`+ .workbuddy/`（原 `.workbuddy/archive/` 被 `.workbuddy/` 覆盖，无需单列）。
- 修改文件清单（**实际 12 个 Git 路径**，按文件路径逐条计数，不按操作类别合并）：
  - 取消跟踪（8 个 `.workbuddy/memory/*` 文件，路径各自独立，不得合并为 1 项索引操作）：
    1. `.workbuddy/memory/2026-07-31.md`
    2. `.workbuddy/memory/2026-08-03.md`
    3. `.workbuddy/memory/2026-08-04.md`
    4. `.workbuddy/memory/2026-08-05.md`
    5. `.workbuddy/memory/2026-08-06.md`
    6. `.workbuddy/memory/2026-08-07.md`
    7. `.workbuddy/memory/2026-08-08.md`
    8. `.workbuddy/memory/MEMORY.md`
  - 修改/创建（4 个文件）：
    9. `.gitignore`
    10. `tasks/TASK-DM-002.md`
    11. `PROJECT_STATE.md`
    12. `tasks/TASK-GOV-001.md`
- 测试命令及结果：无（治理操作）；交付后 `git status` 校验 `.workbuddy/` 不再出现于索引、工作树文件保留。
- 变更预算实际值：**max_files=5，实际 12 个 Git 路径，已超出预算（偏差 +7）**。偏差原因 = 任务单按「操作类别」而非「文件路径」计数（8 个 memory 路径被合并记为 1 项索引操作）。此偏差由 TASK-GOV-002 追认并向前收口，不重写 `f56a478` 历史。
- 未解决风险：无（范围内已闭环）。
- 是否偏离 TASK：**变更预算偏离（change_budget 硬停偏差，已发生）**——实际改动 12 个 Git 路径，超出本任务声明的 `max_files=5`；所有 12 个路径均在「允许修改路径」5 项授权**意图范围**内（8 个 memory 文件由索引取消跟踪授权覆盖，4 个文件为显式列出），故**授权范围未越界**，但**预算计数偏差属已发生的 change_budget 硬停偏差**：原任务单在未标记超预算的情况下关闭。向前收口方式 = 由 TASK-GOV-002 如实追记本偏差并校正计数口径，历史不重写。
- 规范影响结论：**none**（不改变任何规范内容）。
- 账目记录（必读）：`f864937` 系 TASK-DM-002 关闭后**范围外提交**，非项目治理证据，已通过 `git rm --cached -r .workbuddy/` + `.gitignore` 忽略规则收口；`f864937` 历史**未重写、未删除**。
- 计数口径校正（TASK-GOV-002 追认）：本任务原始「变更预算实际值=未超预算 / 是否偏离 TASK=否」结论**有误**——实际 12 个 Git 路径超出 `max_files=5`，属已发生的 change_budget 硬停偏差；偏差仅限预算计数（授权范围未越界），由 TASK-GOV-002 向前收口，不重写 `f56a478`。

## 关闭条件（对齐 `tasks/TASK-TEMPLATE.md` 四条件）

1. **测试通过**：纯治理操作，无执行测试；`git status` 校验 `.workbuddy/` 不再出现于索引、工作树文件保留。
2. **规范影响已处理**：无规范变更（none）。
3. **spec_sync = clean**（本任务不涉及规范版本，n/a 等同满足 TASK-TEMPLATE 第 ③ 条）。
4. **真实 verified_commit** 已记录（回填本任务关闭提交真实 sha）。

## 关闭结论

- **任务状态：Closed**。
- `f864937` 系 TASK-DM-002 关闭后范围外提交，非项目治理证据，已通过 `git rm --cached -r .workbuddy/` + `.gitignore` 忽略规则收口；`f864937` 历史未重写、未删除。
- TASK-DM-002 锚点语义已校正：`approval_commit=f537296`（domain_model v1.1.4 独立批准锚点），`verified_commit=94bedb5`（完整验证快照；`f537296` 发生时 `spec_sync` 仍 dirty，不兼任 `verified_commit`）。
- PROJECT_STATE 中 `f537296` 误写为 `verified_commit` 处已改 `94bedb5`；baseline 中 `f537296` 作为领域模型批准锚点记录保持不变。
- 状态保持：domain_model=1.1.4/approved、SRS=review、TASK-SRS-001 spec_sync=clean、UI 冻结。未代签 SRS。
