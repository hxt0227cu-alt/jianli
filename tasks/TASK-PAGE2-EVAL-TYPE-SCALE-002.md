# TASK-PAGE2-EVAL-TYPE-SCALE-002 评测证据板二次放大

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`9f51ac51dbb07853464e54553ffea23a9cfe82d3`

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.1 U2
- `docs/design/ui-wireframe.md` §3 U2
- `docs/test/test-plan.md` TC-AI-011

## 需求来源
- 用户 2026-08-30 基于 Jianli 评测证据板截图提出：该板块文字仍然过小，需要再次放大。

## 目标
只提升页面二 Jianli 评测证据板的标题、标签、指标、说明、提交号、案例与边界文字，并同步调整行高和内边距，改善桌面端可读性。

## 非目标（明确排除）
- 不修改评测内容、指标、commit、CI 状态、失败案例或板块结构。
- 不修改页面二其他板块及 Sleep / Litchi 展示。
- 不修改问答、RAG、知识库、Prompt、API、数据库、权限、依赖或部署。

## 允许修改路径
- `tasks/TASK-PAGE2-EVAL-TYPE-SCALE-002.md`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`（仅强化本板块字号断言，不得放宽其他断言）

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
- reason：仅在既有 U2 评测证据板内提高字体与间距，不改变内容、交互、业务行为或接口契约。

## 功能验收
- 评测板微型文字由 12–14px 提升至正文/标签 14–15px、提交号 13px、主指标 27px 以上。
- 标题、总分、套件卡、Reranker 对照、失败案例和边界说明均同步放大。
- 桌面视口下无横向溢出、文字裁切或卡片重叠，评测内容与数据保持不变。

## 安全与隐私验收
- 不新增或改变任何公开事实、隐私数据、Prompt、问题原文或 NDA 内容。

## 性能验收
- 纯 CSS 调整，不新增网络请求、资源、依赖或动画。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：40
- expected_test_lines：8

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `git diff --check`
- 浏览器实屏检查评测板字号、换行、溢出与控制台。

## 回滚方法
- 回退本任务提交；无数据迁移或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要改变文案、数据、结构、依赖、API、数据库或权限时停止报告。
- 超过 3 个文件、超出预算或冻结验收测试失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：待回填
- verified_commit：待回填

## 关联
- Change Request：无（纯视觉可读性调整）
- 测试任务：TC-AI-011 + 现有 web-shell 回归
