# TASK-CONTENT-LITCHI-001 展示 litchi（荔枝问答平台，毕设）为第 3 个项目

## 任务类型
- documentation + content（展示内容扩展，非行为/契约变更）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1（全部 approved）
- 基线 commit：62620df

## 需求来源
- 用户 2026-08-16 23:06 明确决定**保留 sleep/litchi（展示 3 个项目）**，此前"删 sleep/litchi tab"历史计划**作废**。工作树未提交的 sleep/litchi 改动为**有意保留**，非废弃。
- 与 TASK-CONTENT-FIX-001 关联：CONTENT-FIX-001 明确"不动 sleep/litchi tab 增删（存在未提交的相关改动，单独评审）"，故本任务承接该部分，与 CONTENT-FIX-001 / GROUNDING-001 / FACT-001 **不混提交**。

## 目标
将 litchi（荔枝问答平台，毕设项目）作为与 jianli / sleep 并列的第 3 个项目展示：知识库新增 litchi chunk、项目区新增 projects_litchi、数字分身问答新增 litchi 问题；模型键 `ProjectKey` 增加 `"litchi"`；前端补 litchi 紫色主题（镜像 `.blue` 的 accent 覆盖）。

## 非目标
- 不改动 jianli / sleep 既有内容或行为。
- 不改拒答阈值 / API / 迁移 / 依赖 / 加密 / 鉴权。
- litchi 正文当前为占位（"上传文档后由真实语料补充"），不引入真实语料。

## 允许修改路径
- `apps/api/app/aiqa/content.py`（`projects_litchi` 段、`projects_sections` 含 litchi、`_chunk("litchi", ...)`、litchi 数字分身问题）
- `apps/api/app/aiqa/models.py`（`ProjectKey = Literal[..., "litchi"]`）
- `apps/web/styles.css`（`.project-stage.purple` 等 litchi 紫色主题 9 行）
- 本任务单 `tasks/TASK-CONTENT-LITCHI-001.md`

## 禁止修改路径
- 除上列精确片段外的任何内容；jianli / sleep 相关；迁移 / 规范 / API / 依赖。

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：false（仅扩展展示项目集，不改变用户可观察的产品行为逻辑；litchi 为占位）
- affected_specs：srs none / domain_model none / openapi none / security none / test_plan none
- reason：展示内容扩展，与既有 SRS/领域模型无冲突；litchi 属"项目展示"范畴已在用例/PRD 框架内。

## 功能验收
- `apps/api/app/aiqa/models.py` `ProjectKey` 含 `"litchi"`。
- `apps/api/app/aiqa/content.py` 含 `projects_litchi` 且 `projects_sections` 列表含 litchi；存在 `_chunk("litchi", ...)` 与 litchi 数字分身问题。
- `apps/web/styles.css` 含 `.project-stage.purple` 规则。

## 安全与隐私验收
- 无（纯展示内容；litchi 正文为占位，不含真实个人数据）

## 性能验收
- 无新增量化阈值

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：~25

## 必须运行的测试命令
- 无（纯静态内容；不触碰测试）

## 回滚方法
- `git revert` 本任务 commit；或 `git checkout -- apps/api/app/aiqa/content.py apps/api/app/aiqa/models.py apps/web/styles.css` 仅回滚本任务片段（需保留其他任务的同文件改动，故优先用 revert 整提交）。

## 强制停止条件
- 若发现需改 jianli/sleep 内容或 API/迁移/依赖 → 停止并报告。

## 交付证据（任务关闭前必须填写）
- commit / PR：本提交（HEAD，含 tasks/TASK-CONTENT-LITCHI-001.md）
- 修改文件清单：content.py（litchi 片段）、models.py（ProjectKey+litchi）、styles.css（litchi 紫主题）、本任务单
- 测试命令及结果：无（纯内容）
- lint / typecheck：py_compile 通过（content.py/models.py）；前端样式不进 tsc 逻辑
- DB 迁移验证：无
- 验收证据：上述三文件片段均已落地
- 变更预算实际值：max_files=4 / 生产行数≈25
- 未解决风险：litchi 正文为占位，待真实语料补充（属后续内容任务，非本任务范围）
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：本提交（HEAD）
- 关闭门禁：①内容落地 ②规范影响 none ③spec_sync clean ④verified_commit 已记录
