# TASK-IMPL-WEB-002 前端双工作区 UI 重构

## 任务类型
- implementation

## 基线与目标
- 基线：PRD 2.3.3 / SRS 1.2 / UI 1.0 / architecture 0.2 / security 0.1 / OpenAPI 0.1 / test-plan 0.1（均 approved）
- 目标：将静态展示壳重构为桌面端双工作区：页面一为简历占位、共用历史会话栏和对话占位；页面二为项目播放占位、共用历史会话栏和对话占位。
- 来源：用户 2026-08-10 明确 UI 重构指令及两张布局参考图。

## 非目标
- 不接真实 PDF、模型、登录、鉴权、数据库、SSE、通知、预约或外部 API。
- 不修改任何 approved 规格，不修改 `sleep202603-an`，不复制其私有源码或依赖。
- 不虚构项目指标、线上结果、演示素材或真实对话记录。

## 精确规范引用
- `docs/content/project-showcase.md` §1-§4：项目展示内容与证据分级。
- `docs/test/test-plan.md`：TC-UI-001/002/003/005 冻结验收。
- `docs/design/ui-wireframe.md`：U1-U12、A1-A8 作为既有信息边界参考；本任务只调整静态展示壳，不实现预约业务。

## 允许修改路径
- `apps/web/**`
- `tests/web-shell/**`
- `tasks/TASK-IMPL-WEB-002.md`（仅交付证据）

## 禁止修改路径
- `docs/**`（本任务交付证据除外）
- `PROJECT_STATE.md`、`docs/baseline.yml`
- 后端、迁移、鉴权、加密、基础设施
- `C:\Users\<user>\Desktop\sleep202603-an\**`

## 已批准 DB / API / 依赖变更
- DB：无
- API/SSE：无
- 依赖：沿用已接受的 React/TypeScript/Vite/Lucide/Vitest/Playwright；不新增运行时依赖。

## 验收
- 页面一：左侧简历占位区支持后续替换；中间历史会话列表；右侧静态对话区。
- 页面二：项目切换；左侧播放式项目占位区支持步骤切换；中间共用历史会话列表；右侧静态项目对话区。
- 仅桌面端开放，窄屏显示明确阻断提示。
- 所有占位内容明确标注，不能宣称真实 PDF、真实模型响应或未经验证项目结果。
- 键盘可访问导航与主要按钮。

## 变更预算
- `max_files=10`
- `expected_prod_lines<=420`
- `expected_test_lines<=140`

## 测试
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test --run`
- `pnpm exec playwright test tests/web-shell`
- `pnpm build`

## 回滚
- `git revert` 本任务提交，恢复 `TASK-IMPL-WEB-001` 的展示壳。

## 交付证据
- commit / PR：`38ab805`
- 修改文件清单：`apps/web/main.tsx`、`apps/web/styles.css`、`tests/web-shell/shell.spec.ts`、`tests/web-shell/shell.test.ts`、本任务单
- 测试命令及结果：`pnpm test --run` → 1 passed；`pnpm exec playwright test tests/web-shell` → 2 passed；`pnpm build` → pass
- lint / typecheck：`pnpm lint` → pass；`pnpm typecheck` → pass
- DB 迁移验证：无
- 验收证据：1440×900 桌面截图已人工复核；Playwright 覆盖桌面简历区、项目切换/播放及 900px 窄屏阻断
- 变更预算实际值：5 个文件；生产代码约 96 物理行（组件与样式压缩排版）；测试代码约 30 行，未超预算
- 未解决风险：真实 PDF、AI 对话、项目素材和后端能力待后续任务提供
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`38ab805`
- 状态：Closed（静态 UI 重构与冻结验收通过）
