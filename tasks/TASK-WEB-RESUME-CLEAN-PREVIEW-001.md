# TASK-WEB-RESUME-CLEAN-PREVIEW-001 简历高清无外壳预览

## 任务类型
- implementation

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
- 将页面内 iframe PDF 阅读器替换为由同一份 PDF 渲染的高清单页预览，消除黑色浏览器外壳。
- 保留原始 PDF 打开/下载入口以及加载、失败、重试反馈。

## 非目标（明确排除）
- 不修改简历内容或 `resume.pdf` 原文件。
- 不修改 API、数据库、依赖、登录、问答、预约或知识库。
- 不引入 PDF.js 或其他运行时依赖。

## 允许修改路径
- `tasks/TASK-WEB-RESUME-CLEAN-PREVIEW-001.md`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `apps/web/public/resume-preview.png`

## 禁止修改路径
- `apps/api/**`
- `apps/web/public/resume.pdf`
- API / migration / dependency / auth / AIQA 文件

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：none
- reason：修复浏览器原生 PDF 控件破坏已批准“简洁清爽”页面表现的问题；简历内容和原始 PDF 能力不变。

## 功能验收
- 页面内只展示白色高清简历预览，不出现浏览器 PDF 黑色工具栏或缩略图栏。
- 顶部保留原始 PDF 打开与下载入口。
- 图片加载前显示加载提示，失败时显示可重试错误态。
- 预览图必须由当前 `resume.pdf` 渲染，视觉内容完整清晰。

## 安全与隐私验收
- 仅发布与当前公开 PDF 等价的静态预览图，不增加新的个人信息。

## 性能验收
- 预览图不超过 3MB；生产构建成功。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：45
- expected_test_lines：0

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- 浏览器 1440×900 以上视觉验收页面一。

## 回滚方法
- 回退预览组件、样式和 `resume-preview.png`，恢复原 iframe 展示。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要修改 PDF 内容、外部依赖、公开 API、数据库、权限或问答时停止。
- 预览图超过 3MB、视觉渲染缺页/模糊、冻结测试失败或超过 4 个文件时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`3f0b491ac56b2c2ac7addfd478ec151776f31691`
- 修改文件清单：本任务单、`apps/web/main.tsx`、`apps/web/styles.css`、`apps/web/public/resume-preview.png`；均在允许路径内。
- 测试命令及结果：WSL `pnpm test` → 1 passed；`pnpm typecheck` → passed；`pnpm build` → passed（1793 modules transformed）。
- lint / typecheck：TypeScript `tsc --noEmit` → passed；production build → passed；`git diff --check` → passed。
- DB 迁移验证：无
- 验收证据：Poppler `pdfinfo` 确认源 PDF 为 A4 单页；200 DPI 渲染为 1654×2339 PNG，885,980 bytes；原图检查无缺页、裁切、乱码或黑块。本地浏览器 1920×1250 视觉验收确认页面内仅显示白色简历纸张，黑色工具栏/缩略图/背景均消失，下载与原始 PDF 入口可见。
- 变更预算实际值：4/4 文件；生产代码 +15/-2 行；静态预览 1 个（0.85MB），未超预算。
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`3f0b491ac56b2c2ac7addfd478ec151776f31691`

## 关联
- 测试变更：`TASK-TEST-WEB-RESUME-PREVIEW-002`
- 测试任务：TC-UI-002
