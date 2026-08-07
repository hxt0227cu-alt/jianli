# TASK-GOV-002 治理账目校正（TASK-GOV-001 change_budget 计数口径 + PROJECT_STATE 验证锚点）

> 本任务单为 AI 仓库变更的唯一范围约束。无任务单不得写入仓库。
> **本任务授权范围严格限定**（见「允许修改路径」），超出范围的文件一律不得触碰。

## 任务类型
- governance（治理账目校正，非规范升版、非边界修正）

## 背景（缺陷事实）

- `TASK-GOV-001`（`f56a478`）关闭时，其 change_budget 计数口径错误：将 `git rm --cached -r .workbuddy/` 产生的 **8 个 `.workbuddy/memory/*` 文件取消跟踪** 合并记为「1 项索引操作」，而非按**文件路径**逐条计数。
- 正确计数应为 **12 个 Git 路径**：8 个 memory 文件（`.workbuddy/memory/2026-07-31.md`、`.workbuddy/memory/2026-08-03.md`、`.workbuddy/memory/2026-08-04.md`、`.workbuddy/memory/2026-08-05.md`、`.workbuddy/memory/2026-08-06.md`、`.workbuddy/memory/2026-08-07.md`、`.workbuddy/memory/2026-08-08.md`、`.workbuddy/memory/MEMORY.md`）+ `.gitignore` + `PROJECT_STATE.md` + `tasks/TASK-DM-002.md` + `tasks/TASK-GOV-001.md`。
- 因此 `TASK-GOV-001` 的「变更预算实际值=未超预算」「是否偏离 TASK：否」两项结论**不成立**：实际 12 路径 > `max_files=5`，属已发生的 change_budget 硬停偏差。
- 偏差仅限**预算计数口径**；8 个 memory 文件由「索引取消跟踪」授权覆盖、4 个文件为显式列出，**授权范围未越界**。
- 修正方式 = **向前修正**：由本任务如实追记偏差并校正计数口径，**不重写 `f56a478` 历史**，也**不**将 `max_files` 事后改 12 并宣称未超预算。

## 目标

1. **校正 TASK-GOV-001 账目**：保留 `max_files=5`；将「变更预算实际值」改为实际 12 路径、已超预算；删除「未超预算」「是否偏离 TASK：否」结论，改为 change_budget 硬停偏差 + 向前收口说明；将 8 个 memory 文件逐路径列出，不得合并为 1 项索引操作。
2. **校正 PROJECT_STATE 验证锚点**：`adc7c8d3…/gov-sync-001-verified` 保留为**历史治理锚点**，但不得再称其为当前「最后 verified commit」；补充领域模型完整验证快照 `94bedb5`；追加本治理修正完成后的**最新验证锚点**（回填本任务关闭提交 sha）。

## 非目标（明确排除）

- 不修改任何规范正文（SRS.md / domain-model.md / PRD.md / use-cases.md）
- 不修改 `docs/baseline.yml`（领域模型批准锚点 `f537296` 保持不变）
- 不改动 `.gitignore` / `.workbuddy/` 的跟踪状态（保持：`.workbuddy/` 不受 Git 跟踪且继续被 `.gitignore` 忽略）
- 不重新批准 SRS / 不代签
- 不推进 UI / 架构 / 安全设计 / OpenAPI / 测试计划 / 编码
- 不改变 `domain_model=1.1.4/approved`、`SRS=review`、`TASK-SRS-001 spec_sync=clean`、UI 冻结等既有状态

## 允许修改路径（授权范围，严格限定「仅包括」以下 3 项）

- `tasks/TASK-GOV-001.md`                      # 仅 change_budget 计数口径校正（max_files 不变、actual 改为 12、删除错误结论、列全 8 个 memory 路径）
- `PROJECT_STATE.md`                           # 仅「最后 verified commit」节：历史锚点降级 + 补 94bedb5 + 追加本任务最新锚点
- `tasks/TASK-GOV-002.md`                      # 本任务单自身

## 禁止修改路径（越界即停）

- `.gitignore`、`.workbuddy/`（本任务不触碰其跟踪/忽略状态）
- `docs/baseline.yml`（其 `f537296` 批准锚点记录保持不变）
- `docs/requirements/*.md`、`docs/design/domain-model.md`、`docs/design/ui-wireframe.md`
- `tasks/TASK-SRS-001.md`、`tasks/TASK-DM-001.md`、`tasks/TASK-DM-002.md`、`tasks/TASK-UI-001.md`
- 任何代码 / 契约 / 测试文件

## 变更预算（change_budget）

- max_files：**3**（本任务实际仅改 `tasks/TASK-GOV-001.md` + `PROJECT_STATE.md` + `tasks/TASK-GOV-002.md` 共 3 个文件；**按文件路径计数**，不合并、不漏计）
- expected_prod_lines：小幅（TASK-GOV-001 账目段落重写 + PROJECT_STATE 验证锚点段落 + 本任务单）
- expected_test_lines：0

## spec_sync

- **clean（n/a）** —— 本任务不涉及任何规范版本（SRS / 领域模型 / PRD）的内容变更，无下游规范影响，机器门禁无需 impact check。

## 交付证据（任务关闭前必须填写）

- commit / PR：治理校正本身见本任务关闭提交（sha 见下「verified_commit」）；`f56a478`（TASK-GOV-001 关闭提交，仅引用，本任务不改动）为被校正对象。
- verified_commit：**（本治理修正提交 sha，创建后回填）** —— 含 `tasks/TASK-GOV-001.md` 计数口径校正 + `PROJECT_STATE.md` 验证锚点同步 + 本任务单。
- 被校正事实：`f56a478` 实际改动 **12 个 Git 路径**（8 memory 取消跟踪 + 4 文件），超出 TASK-GOV-001 声明的 `max_files=5`；偏差仅限预算计数，授权范围未越界。
- 测试命令及结果：无（治理操作）；交付后 `git status` 校验 `.workbuddy/` 仍不在索引、`PROJECT_STATE.md` 与 `TASK-GOV-001.md` 已更新。
- 变更预算实际值：max_files=3，实际改 3 文件，未超预算（本任务自身计数准确）。
- 未解决风险：无（范围内已闭环）。
- 是否偏离 TASK：**否**（全部 3 个改动文件在「允许修改路径」3 项内，且计数按文件路径逐条，无合并/漏计）。
- 规范影响结论：**none**（不改变任何规范内容）。

## 关闭条件（对齐 `tasks/TASK-TEMPLATE.md` 四条件）

1. **测试通过**：纯治理操作，无执行测试；`git status` 校验 `.workbuddy/` 仍不在索引、工作树文件保留。
2. **规范影响已处理**：无规范变更（none）。
3. **spec_sync = clean**（本任务不涉及规范版本，n/a 等同满足 TASK-TEMPLATE 第 ③ 条）。
4. **真实 verified_commit** 已记录（回填本任务关闭提交真实 sha）。

## 关闭结论

- **任务状态：Closed**。
- TASK-GOV-001 账目已校正：保留 `max_files=5`；`变更预算实际值` 改为实际 **12 个 Git 路径、已超出预算**；删除错误的「未超预算」「是否偏离 TASK：否」，改为 change_budget 硬停偏差 + 向前收口说明；8 个 memory 文件逐路径列出（不合并为 1 项索引操作）。`f56a478` 历史未重写、未删除。
- PROJECT_STATE「最后 verified commit」节已校正：`adc7c8d3…/gov-sync-001-verified` 降级为**历史治理锚点**（不再称当前最后 verified commit）；补充领域模型完整验证快照 `94bedb5`；本任务关闭提交 sha 作为**最新验证锚点**回填。
- `.workbuddy/` 仍不受 Git 跟踪且继续被 `.gitignore` 忽略；`domain_model=1.1.4/approved`、`SRS=review`、`TASK-SRS-001 spec_sync=clean`、UI 冻结等状态保持不变。未代签 SRS。
