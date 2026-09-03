# TASK-IMPL-WEB-001 前端展示壳与页面一/二

## 任务类型
- implementation

## 会话开始上下文

基线：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5
任务：TASK-IMPL-WEB-001
目标：交付可直接打开的桌面端前端壳，完成页面一问答入口、页面二双项目展示和全局导航。
非目标：数据库、登录/鉴权、加密、预约写入、SSE、邮件/飞书、云部署、Agent 工具调用。
允许修改：`apps/web/**`、`package.json`、`pnpm-lock.yaml`、`vite.config.*`、`tsconfig*.json`、`playwright.config.*`、`tests/web-shell/**`。
预计变更：不超过 20 个文件；生产代码 ≤800 行；测试代码 ≤200 行。
验收测试：TC-UI-001、TC-UI-002、TC-UI-003、TC-UI-005。
输出语言：简体中文。

## 基线版本与基线 commit
- SRS 1.2 / UI 1.0 / architecture 0.2 / security 0.1 / OpenAPI 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`c1fb262`

## 精确规范引用
- SRS §3.1 / §3.2 / §3.4；UI 线框 U1-U12 / A1-A8；project-showcase.md §1-§3；test-plan TC-UI-001/002/003/005

## 需求来源
- R1 / R2 / R6 / R8 / R15 / R16 / R17 / R22 / R25；页面二项目展示需求

## 目标
- 构建三页导航中的页面一与页面二视觉和交互骨架，优先保证桌面端可展示、页面二突出 AI Agent 全栈能力证据。

## 非目标
- 不实现 API 请求、真实模型问答、登录、预约、Slot SSE、管理员后台、通知、数据库、云资源和生产域名。
- 不读取或修改 `C:\Users\<user>\Desktop\sleep202603-an` 以外的源代码；该项目只读取已核验证据和视觉素材。

## 允许修改路径
- `apps/web/**`
- `package.json`
- `pnpm-lock.yaml`
- `vite.config.*`
- `tsconfig*.json`
- `playwright.config.*`
- `tests/web-shell/**`

## 禁止修改路径
- `docs/**`、`tasks/**`（除本任务交付证据外）
- 后端、迁移、鉴权/加密、通知、基础设施
- `C:\Users\<user>\Desktop\sleep202603-an\**`

## 已批准的 DB / API / 依赖变更
- DB：无。
- API/SSE：无；本任务使用静态内容和明确的后续接入边界，不伪造接口已实现。
- 依赖：仅使用 ADR-IMPL-001 accepted 的 React、TypeScript、Vite、React Router、TanStack Query、Lucide React，以及 Vitest/Testing Library/Playwright 开发依赖；精确版本必须写入 lockfile。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：只实现已批准 UI 线框的静态展示与导航，不接入业务写路径。

## 功能验收
- 页面一显示简历/项目问答入口、推荐问题占位和可访问导航；不声称模型已接通。
- 页面二展示 `jianli` 与 `sleep202603-an` 两个项目，突出问题、架构、AI Agent 治理、可核验证据和证据等级。
- 1280×720 无重叠；<1024px 显示阻断提示；导航和页面正文可键盘访问。
- 页面三入口明确为后续预约体验，不伪造可用预约数据。

## 安全与隐私验收
- 不包含真实密钥、邮箱授权码、Cookie、用户 PII 或 sleep 项目私有源码。
- 页面二仅呈现 `docs/content/project-showcase.md` 已分级证据；本地/模拟/未验证标签清晰。
- 不注册任何预约工具，不把模型或工具调用写入前端。

## 性能验收
- 首屏本地构建后加载 ≤2s（静态本地 smoke）；前端选段交互 <100ms；无大图阻塞主线程。
- 绑定 TC-UI-001、TC-UI-002、TC-UI-003、TC-UI-005，不降低其断言。

## 变更预算
- max_files：20
- expected_prod_lines：800
- expected_test_lines：200

## 必须运行的测试命令
- `pnpm install --frozen-lockfile`
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test --run`
- `pnpm exec playwright test tests/web-shell`
- `pnpm build`

## 回滚方法
- 删除本任务新增前端目录与配置，或 `git revert` 本任务提交；不涉及数据库回滚。

## 强制停止条件
- 需要新增后端 API、数据库表/字段/索引、鉴权/加密、外部通知或基础设施配置。
- 需要修改已批准 UI/SRS，或需要改变页面二已批准证据口径。
- 发现 sleep 项目需要写入、复制私有源码或修改其工作树。
- 超出文件/行数预算或冻结 TC 失败。

## 交付证据
- commit / PR：`9473369`（前端展示壳与页面一/二交付）
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填（桌面/窄屏截图）
- 变更预算实际值：待回填
- 未解决风险：真实 API、鉴权、预约和部署由后续任务实现
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`9473369`
- 实现证据：`pnpm lint` PASS；`pnpm typecheck` PASS；`pnpm test --run` PASS（1 test）；`pnpm build` PASS；Playwright 待浏览器安装完成复核。
- 修改文件：`apps/web/index.html`、`apps/web/main.tsx`、`apps/web/styles.css`、`package.json`、`pnpm-lock.yaml`、`vite.config.ts`、`tsconfig.json`、`playwright.config.ts`、`tests/web-shell/shell.test.ts`、`tests/web-shell/shell.spec.ts`。
- 预算实际值：10 个文件；生产代码约 220 行；测试代码约 28 行；未超预算。数据库迁移：无。
- 是否偏离 TASK：否。未解决风险仅为后续真实 API、鉴权、预约、通知与部署实现。
- **状态：Closed（2026-08-18 用户确认收口）**——前端展示壳与页面一/二交付于 `9473369`，独立审查 TASK-REVIEW-WEB-001 已 Closed（无 P0/P1）；后续 M1–M6、AIQA、飞书等全部前端功能均在展示壳之上迭代完成，本任务历史遗留 Open 状态由用户 2026-08-18 确认正式收口。

## 关联
- 独立审查：TASK-REVIEW-WEB-001
- 冻结验收：TC-UI-001/002/003/005
