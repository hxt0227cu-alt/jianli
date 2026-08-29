# TASK-PAGE2-TYPE-SCALE-001 三项目展示字号整体放大

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`f2186089b8a66f0a7e211c72eaefd48a5456fb04`

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` §3 U2
- `docs/requirements/use-cases.md` UC-02
- 现有 `tests/web-shell/shell.test.ts` 冻结回归

## 需求来源
- 用户 2026-08-29 基于评测中心截图提出：三个项目内文字整体过小，统一调大两个字号层级。

## 目标
统一提升 Jianli、Sleep、Litchi 三个项目全部展示板块的标签、正文、指标、证据边界与辅助说明字号，在不改变内容和结构的前提下提高桌面端可读性。

## 非目标（明确排除）
- 不修改项目文案、事实、指标、板块结构或交互。
- 不修改问答、RAG、知识库、Prompt 或评测报告。
- 不修改 API、数据库、迁移、权限、依赖与部署。

## 允许修改路径
- `tasks/TASK-PAGE2-TYPE-SCALE-001.md`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`（仅新增字号断言，不得修改或放宽既有断言）

## 禁止修改路径
- `apps/web/main.tsx`
- `apps/api/**`
- `docs/**`
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
- reason：仅调整 U2 项目展示页的字号与随内容自然增长的卡片高度，不改变用户操作、业务行为或契约。

## 功能验收
- 三个项目核心价值卡的标签、正文、指标和证据边界均明显放大。
- Jianli Agent Lab 与版本化评测中心的所有微型文字提升约两个字号层级。
- Sleep 可靠性复盘/交付账本和 Litchi 工程链路/毕设验收板同步放大。
- 1440×1000 桌面视口无横向溢出、文本裁切或卡片重叠；三个项目切换正常。

## 安全与隐私验收
- 不新增或改变任何公开事实、隐私数据或 NDA 内容。

## 性能验收
- 纯 CSS 调整，不新增网络请求、资源、依赖或动画。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：90
- expected_test_lines：20

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`
- `git diff --check`
- 浏览器 1440×1000 逐项检查 Jianli / Sleep / Litchi 的字号、换行、溢出与控制台。

## 回滚方法
- 回退本任务提交；无数据迁移或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要改变文案、结构、依赖、API/DB/权限时停止报告。
- 超过 3 个文件、超出预算或冻结测试失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`19f1cb5fef832ef7b283ef49ced7581520c39e36`
- 修改文件清单：`apps/web/styles.css`、`tests/web-shell/shell.test.ts`、`tasks/TASK-PAGE2-TYPE-SCALE-001.md`
- 测试命令及结果：`npm test` → 1 test / 1 file passed；`npm run build` → 1793 modules transformed，production build 成功
- lint / typecheck：`npm run typecheck` → 0 error；`git diff --check` → 0 error
- DB 迁移验证：无
- 验收证据：Codex 内置浏览器 1440×1000 实测：Jianli 事实卡正文 15px、Agent Lab 正文 17px、评测正文 13px/commit 12px；Sleep 复盘正文 16px、证据账本正文 15px；Litchi 双链路与验收正文均 15px。三个项目无横向溢出、裁切或重叠，warning/error 控制台记录为 0。
- 变更预算实际值：3 / 3 files；生产样式 71 行≤90；测试 9 行≤20
- 未解决风险：字号增大后各板块纵向高度同步增加，符合桌面端滚动展示预期。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`19f1cb5fef832ef7b283ef49ced7581520c39e36`

## 关联
- Change Request：无（纯视觉可读性调整）
- 测试任务：现有 web-shell 冻结回归
