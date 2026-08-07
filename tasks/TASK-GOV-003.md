# TASK-GOV-003 治理文字收口（SRS 关闭后陈旧 review 表述校正）

> 最小治理修正 TASK。授权范围严格限定以下 3 项，越界即停。

## 任务类型
- governance

## 授权范围（允许修改路径）
- tasks/TASK-SRS-001.md        # 仅校正交付证据中的陈旧 review 表述（不改动历史阶段记录）
- PROJECT_STATE.md             # 仅校正第 25 行陈旧 review 表述
- tasks/TASK-GOV-003.md        # 本任务单自身

## 禁止修改路径（越界即停）
- docs/baseline.yml            # 不变
- docs/requirements/SRS.md     # 正文不变（SRS 已 approved）
- docs/design/domain-model.md  # 领域模型不变（v1.1.4）
- docs/design/ui-wireframe.md  # UI 文件不变
- 任何其他文件

## 目标
SRS v1.0 已批准并关闭（approval_commit=`26ae844`、verified_commit=`06798a2`）。在 TASK-SRS-001 与 PROJECT_STATE 中仍存在"SRS 仍 review / 未 approved"的陈旧当前态表述，须校正为最终 approved/Closed 状态，且**不得改写历史阶段记录**中的 review 状态（那些是事实性历史）。

## 非目标
- 不批准或推进 UI / 架构 / 安全 / OpenAPI / 测试计划 / 编码
- 不改任何规范正文（baseline / SRS / 领域模型 / UI）

## 变更预算（change_budget）
- max_files：3（TASK-SRS-001.md + PROJECT_STATE.md + 本任务单）

## 必须运行的测试命令
- 无（纯文字）；交付前执行全仓 Grep 复核。

## 回滚方法
- 本任务仅文字校正，git revert 即可。

## 强制停止条件
- 出现任何未在「允许修改路径」列明的变化（含改 baseline / SRS / 领域模型 / UI 正文）→ 立即停止并报告。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`ab2cf1d174eb74ef7353707db58fb78f07720891`（TASK-GOV-003 关闭提交 / 本任务 verified_commit）
- 修改文件清单（**3 个，按文件路径逐条计数，不合并**）：
  1. `tasks/TASK-SRS-001.md` — 3 处文字校正（均限交付证据当前态，不改历史阶段记录）：
     a. 交付证据 commit/PR 链：补入 `26ae844`（SRS 批准锚点 / approval_commit）、`06798a2`（TASK-SRS-001 关闭快照 / verified_commit）；"SRS 状态仍 = review，未 approved"→"SRS 现已 approved（26ae844）/ Closed（06798a2），本任务已关闭"。
     b. 验收证据末句"待用户/独立评审通过后方可 approved"删除（该当前态表述已过时）。
     c. spec_sync 说明末句"SRS 自身仍 status=review…不表示 SRS 已获批准"→"SRS 已于 26ae844 获批；spec_sync=clean 与批准状态均已闭环"。
  2. `PROJECT_STATE.md` — 第 25 行"SRS 仍 review"→"TASK-DM-002 关闭当时 SRS 仍为 review（现已于 26ae844 approved）"，保留"不构成本任务关闭条件"治理点。
  3. `tasks/TASK-GOV-003.md` — 本任务单。
- 测试命令及结果：全仓 Grep 复核无残留"SRS 仍 review"当前态表述（历史阶段记录中的 review 属预期保留）。
- 变更预算实际值：max_files=3，实际 3 文件，未超预算。
- 未解决风险：无（范围内已闭环）。
- 是否偏离 TASK：否（全部改动在授权 3 项内）。
- 规范影响结论：none（纯文字校正，不改规范正文/行为）。
- spec_sync：clean（不涉及规范版本变化）。
- verified_commit：`ab2cf1d174eb74ef7353707db58fb78f07720891`（TASK-GOV-003 关闭提交；含 TASK-SRS-001 文字校正 + PROJECT_STATE 第 25 行校正 + 本任务单）

## 关闭结论
任务于治理文字收口完成后关闭。关闭门禁四条件复核：
1. **测试通过**：纯文字；Grep 复核无残留"SRS 仍 review"当前态表述（历史阶段记录保留 review 为预期）。
2. **规范影响已处理**：none（不改规范正文/行为）。
3. **spec_sync = clean**：无规范版本变化。
4. **真实 verified_commit**：`ab2cf1d174eb74ef7353707db58fb78f07720891`（TASK-GOV-003 关闭提交）。
状态：Closed（2026-08-08）。

## 关联
- 上游任务：TASK-SRS-001（SRS v1.0，已关闭，approval_commit=26ae844 / verified_commit=06798a2）
- 下游：TASK-UI-IMPACT-001（UI 线框影响评审，独立新建）
