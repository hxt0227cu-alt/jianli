# TASK-TEST-WEB-RESUME-PREVIEW-002 简历无浏览器外壳冻结验收更新

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：e4712af

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.1
- `docs/requirements/use-cases.md` UC-01
- `docs/test/test-plan.md` TC-UI-002

## 需求来源
- 用户 2026-08-30 明确要求移除页面内嵌 PDF 阅读器的黑色工具栏与缩略图外壳。

## 目标
- 将过期的“必须使用 iframe”实现断言更新为“高清简历预览图 + 原始 PDF 入口 + 加载/失败态”的用户行为断言。

## 非目标（明确排除）
- 不修改生产代码、PDF 内容、API、数据库、依赖、权限或问答行为。
- 不降低原始 PDF 可访问、加载反馈与失败重试断言。

## 允许修改路径
- `tasks/TASK-TEST-WEB-RESUME-PREVIEW-002.md`
- `tests/web-shell/shell.test.ts`

## 禁止修改路径
- `apps/web/**`
- `apps/api/**`
- `docs/**`

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：test_plan 等价更新；其余 none
- reason：TC-UI-002 要求可查看/下载简历，不要求浏览器 PDF iframe；更新过度绑定实现的冻结断言，不降低用户能力。

## 功能验收
- 断言存在 `/resume-preview.png` 高清预览和 `/resume.pdf` 原文件入口。
- 断言不存在页面内嵌 `iframe`。
- 保留资源检查、加载提示、失败提示和重试断言。

## 安全与隐私验收
- 仅验收已公开简历静态资源，不新增数据路径。

## 性能验收
- 不新增测试网络依赖。

## 变更预算（change_budget）
- max_files：2
- expected_prod_lines：0
- expected_test_lines：8

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`

## 回滚方法
- 回退本任务提交，恢复 iframe 实现断言。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要降低原始 PDF、加载/失败态断言或修改生产代码时停止。
- 超出 2 个文件或冻结验收失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：测试期望提交 `75adf1d4fbc8910c314b4752981f08449c1baeea`；通过验收的实现快照 `3f0b491ac56b2c2ac7addfd478ec151776f31691`
- 修改文件清单：本任务单、`tests/web-shell/shell.test.ts`；均在允许路径内。
- 测试命令及结果：WSL `pnpm test` → 1 passed；`pnpm typecheck` → passed；`pnpm build` → passed（1793 modules transformed）。
- lint / typecheck：TypeScript `tsc --noEmit` → passed；production build → passed；`git diff --check` → passed。
- DB 迁移验证：无
- 验收证据：冻结测试明确断言高清预览图、原始 PDF 入口、资源检查、加载/失败/重试态，并明确禁止页面内嵌 iframe；全部通过。
- 变更预算实际值：2/2 文件；生产代码 0 行；测试 +3/-1 行，未超预算。
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：test_plan 等价更新，未降低 TC-UI-002
- spec_sync：clean
- verified_commit：`3f0b491ac56b2c2ac7addfd478ec151776f31691`

## 关联
- 前置任务：`TASK-TEST-WEB-RESUME-001`
- 实现任务：`TASK-WEB-RESUME-CLEAN-PREVIEW-001`
- 测试任务：TC-UI-002
