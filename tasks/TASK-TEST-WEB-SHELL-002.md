# TASK-TEST-WEB-SHELL-002 页面二三项目真实 Playwright 验收同步

> 状态：In Progress（2026-08-31）。上游 `TASK-CR-UI-THREE-PROJECTS-001` 已按用户既有明确决策批准并将 TC-UI-003 对齐三项目；本任务恢复执行。

## 任务类型
- test（过期冻结验收同步，不改产品行为）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / test-plan 1.3
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`

## 精确规范引用
- `docs/test/test-plan.md` §1、§2.1、§4 与 TC-UI-003
- `tasks/TASK-AIQA-PAGE2-SLEEP-LITCHI-017.md`（三项目 tab）
- `tests/web-shell/shell.test.ts` 当前静态验收（三项目等证据密度、每项目三大板块、真实简历预览）
- 过期复现：`tests/web-shell/shell.spec.ts` 仍断言已不存在的“用播放式演示讲清楚项目”、“播放下一页”、“Agent 边界”与“系统全景”。

## 目标
- 保留桌面端主路径 E2E，改为验收当前真实 UI：简历图片预览、面试官登录入口、三项目 tab 以及每个项目的三大实质板块。
- 保留并继续执行窄屏“请使用桌面端访问”验收。

## 非目标
- 不修改 `apps/web/**`、API、数据库、依赖、样式或产品文案。
- 不删除、skip 或放宽窄屏与桌面主路径断言。
- 不联网下载 Chromium；缺少浏览器时按用户约束停下并给出一次性命令。

## 允许修改路径
- `tests/web-shell/shell.spec.ts`
- `tasks/TASK-TEST-WEB-SHELL-002.md`
- `PROJECT_STATE.md`（仅最终任务状态与证据）

## 禁止修改路径
- `apps/**`、`docs/requirements/**`、`docs/api/**`、迁移、依赖清单和其他冻结测试。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无；复用仓库现有 `@playwright/test` 与 Chromium 运行时。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：上游 Change Request 已独立更新并批准 test-plan 1.3；本任务只实现该冻结浏览器验收，不改产品行为。

## 功能验收
- 简历页标题与真实 `resume-preview-image` 可见。
- 预约页进入后展示“面试官登录”，不依赖未启动 API 伪造时段结果。
- Jianli 页可见项目主卡、Agent Lab 与评测中心。
- Sleep 页可见项目主卡、可靠性回放与交付证据。
- Litchi 页可见项目主卡、工程地图与答辩证据。
- 900px 窄屏仍显示桌面端访问提示。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：≤55

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `pnpm exec playwright test` （Chromium 就绪后）

## 回滚方法
- 回退本任务的 Playwright 断言同步；无数据与业务回滚。

## 强制停止条件
- 需要修改前端实现、删除窄屏断言、引入依赖或超出变更预算。
- 上游 TC-UI-003 变更未批准或冻结断言再次与产品规范冲突。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：本机 Chromium 仍需用户网络配合安装
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
