# TASK-IMPL-WEB-003 预约工作区与跨页引导

## 任务类型
- implementation

## 基线与目标
- 基线：PRD 2.3.3 / SRS 1.2 / UI 1.0 / architecture 0.2 / security 0.1 / OpenAPI 0.1 / test-plan 0.1（均 approved）
- 目标：增加静态预约面试页面，并在简历页、项目页提供预约引导按钮。
- 来源：用户 2026-08-10 明确要求。

## 精确规范引用
- SRS §3.3-§3.7：登录、时段选择、确认、改期/取消信息边界。
- UI 线框 U3-U9：预约相关界面边界。
- test-plan TC-UI-001/002/003/005。

## 非目标
- 不接真实登录、邮箱验证、时段 API、SSE、预约写入、通知或数据库。
- 不显示伪造可用时段，不提交真实预约。
- 不修改 approved 规格或 `sleep202603-an`。

## 允许修改路径
- `apps/web/**`
- `tests/web-shell/**`
- 本任务单（仅交付证据）

## 禁止修改路径
- `docs/**`、`PROJECT_STATE.md`、`docs/baseline.yml`
- 后端、迁移、鉴权、加密、通知、基础设施、`sleep202603-an/**`

## 已批准 DB / API / 依赖变更
- DB：无
- API/SSE：无
- 依赖：无新增，沿用现有前端依赖。

## 验收
- 页面一、页面二均有可键盘访问的“预约面试”入口并导航至第三页。
- 第三页呈现登录验证、选择时间、确认预约三步静态流程及明确占位说明。
- 不出现真实时段、真实邮箱、真实预约成功或外部通知结果。
- 1024px 以下继续显示桌面端阻断提示。

## 变更预算
- `max_files=5`
- `expected_prod_lines<=180`
- `expected_test_lines<=50`

## 测试
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test --run`
- `pnpm exec playwright test tests/web-shell`
- `pnpm build`

## 回滚
- `git revert` 本任务提交。

## 交付证据
- commit / PR：`474e541`
- 修改文件清单：`apps/web/main.tsx`、`apps/web/appointment.css`、`tests/web-shell/shell.spec.ts`、`tests/web-shell/shell.test.ts`、本任务单
- 测试命令及结果：`pnpm test --run` → 1 passed；`pnpm exec playwright test tests/web-shell` → 2 passed；`pnpm build` → pass
- lint / typecheck：`pnpm lint` → pass；`pnpm typecheck` → pass
- DB 迁移验证：无
- 验收证据：1440×900 预约页截图人工复核通过；Playwright 覆盖页面一预约入口、页面二预约入口、预约工作区与窄屏阻断
- 变更预算实际值：5 个文件；生产代码约 120 行；测试代码变更约 8 行，未超预算
- 未解决风险：真实预约链路由后续独立任务实现
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`474e541`
- 状态：Closed（静态预约工作区与跨页入口验收通过）
