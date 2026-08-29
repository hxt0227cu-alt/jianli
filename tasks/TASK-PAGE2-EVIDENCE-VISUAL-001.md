# TASK-PAGE2-EVIDENCE-VISUAL-001 项目证据密度与暖色主题修正

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`7b0fa9722edc6d60c0ca776338215e4b0e0c7cc2`

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` §1.1、§3 U2
- `docs/requirements/use-cases.md` UC-02
- `docs/fact-consistency/fact-bank.md` FQ-31～FQ-52
- `apps/api/app/aiqa/content.py` Sleep / Litchi canonical facts
- 现有 `tests/web-shell/shell.test.ts` 冻结回归

## 需求来源
- 用户 2026-08-29 基于项目页截图提出：Agent Lab 卡片文字过小；Sleep/Litchi 事实卡密度不足；蓝紫配色改为卡其与浅黄色暖色。

## 目标
提高 Agent Lab 小卡可读性，为 Sleep/Litchi 各补三张可核验工程事实卡，并以高对比卡其/浅金主题替换冷蓝/紫主题。

## 非目标（明确排除）
- 不修改项目事实来源、知识库、检索、Prompt、评测阈值或推荐问题。
- 不改变项目切换、Agent Lab、问答或预约交互。
- 不修改 API、数据库、迁移、权限、依赖与部署。
- 不把计划、实验模板或失败部署包装成已生产落地。

## 允许修改路径
- `tasks/TASK-PAGE2-EVIDENCE-VISUAL-001.md`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`（仅新增内容与主题断言，不得修改或放宽既有断言）

## 禁止修改路径
- `apps/api/**`
- `docs/api/**`
- `apps/web/appointment.css`
- 数据库迁移、依赖锁文件、权限与密钥配置

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估（spec impact，每个代码 TASK 必填）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅补充既有项目事实的页面摘要并调整视觉主题与字号，不改变结构、交互、契约或业务行为；UI 线框不规定具体配色与字号。

## 功能验收
- Agent Lab 四张挑战卡的描述和动作文字在 1440px 视口可直接阅读。
- Sleep/Litchi 各展示六张事实卡，新增事实均可追溯到 canonical content / fact bank。
- Sleep 使用卡其/橄榄暖色，Litchi 使用浅金/蜂蜜暖色；标题、正文、标签、证据边界满足清晰对比。
- Jianli 原有内容、Agent Lab 和评测中心不退化。

## 安全与隐私验收
- 不展示 NDA 源码、日志、内部标识、绝对路径或个人敏感信息。
- 不把真实硬件日志、公司内部 RC 或云环境经历写成公开可复现证据。

## 性能验收
- 不新增网络请求、图片、字体、JavaScript 依赖或持续动画。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：180
- expected_test_lines：20

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`
- 浏览器 1440×1000 逐项检查 Jianli / Sleep / Litchi。

## 回滚方法
- 回退本任务提交；无数据迁移或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要新增依赖、API/DB/权限变化或修改 canonical 事实源时停止报告。
- 事实无法从既有语料核验、超过 4 个文件、超出预算或冻结测试失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`6ad01d76603d4165306e22b48d578b6e77e04576`
- 修改文件清单：`apps/web/main.tsx`、`apps/web/styles.css`、`tests/web-shell/shell.test.ts`、`tasks/TASK-PAGE2-EVIDENCE-VISUAL-001.md`
- 测试命令及结果：`npm test` → 1 test / 1 file passed；`npm run build` → 1793 modules transformed，production build 成功
- lint / typecheck：`npm run typecheck` → 0 error；`git diff --check` → 0 error
- DB 迁移验证：无
- 验收证据：Codex 内置浏览器 1440×1000 实测：Agent Lab 4 卡为 2×2（487px×2），说明文字 14px / 23.8px 行高；Sleep 6 张事实卡、`project-card khaki`；Litchi 6 张事实卡、`project-card sun`；三个项目切换正常，控制台 0 warning / 0 error。
- 变更预算实际值：4 / 4 files；生产代码/样式 58 增 / 4 删≤180；测试 13 行≤20
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`6ad01d76603d4165306e22b48d578b6e77e04576`

## 关联
- Change Request：无（不改变业务行为或契约）
- 测试任务：现有 web-shell 冻结回归
