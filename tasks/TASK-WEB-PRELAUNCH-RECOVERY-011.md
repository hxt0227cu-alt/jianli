# TASK-WEB-PRELAUNCH-RECOVERY-011 前端上线前竞态与中等桌面恢复

> 状态：In Progress（2026-08-31）。上线前只读审查发现中等桌面布局、跨项目流式回答及登录后初始化存在可复现缺陷；用户已授权修复。

## 任务类型
- implementation / test（符合现有规范的缺陷修复）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / UI 1.0.3 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`

## 精确规范引用
- `docs/requirements/SRS.md` §3.1、§5.7、§8
- `docs/api/sse.md` §2～§3
- `docs/test/test-plan.md` TC-UI-001、TC-AI-006、TC-SEC-002

## 目标
1. 让 1024～1279px 横屏桌面/平板布局可操作，顶部导航不裁切、主要内容不被挤成窄列。
2. 切页、切项目或切历史对话时立即终止旧 SSE，并禁止旧回调写入新上下文。
3. 把登录认证失败与登录后的会话/时段初始化失败分开呈现；匿名状态不建立受保护的时段 SSE。

## 非目标
- 不提供移动端竖屏适配；`<1024px` 仍按现有规范阻断。
- 不修改登录错误码、防枚举文案、后端 SSE、预约规则、项目内容或评测阈值。
- 不修改 API、数据库、依赖、鉴权、密钥或部署拓扑。

## 允许修改路径
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `tests/web-shell/shell.spec.ts`
- `tasks/TASK-WEB-PRELAUNCH-RECOVERY-011.md`

## 已批准的 DB / API / 依赖变更
- DB：无。API：无。依赖：无。权限与安全策略：无。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none / openapi=none / security=none / test_plan=none（OpenAPI-SSE 1.0 / test-plan 1.4 impact review 后仍无影响）
- reason：修复实现使其重新符合已批准的 1024px 边界、上下文隔离和认证错误语义。

## 功能验收
- 1024、1100、1200、1280px 下导航可见可点；1023px 下仍显示阻断页。
- A 项目流未结束时切到 B，A 的 delta/citation/completed 均不得出现在 B；B 可立即重新提问。
- 匿名进入预约页不请求 `/slots/events` 或 `/slots/snapshot`；认证成功后只建立一条 SSE。
- 登录 401 仍统一显示“邮箱或密码错误”；登录 204 后 `/auth/me` 或时段加载失败显示对应可恢复错误，不得伪装成凭证错误。

## 安全与隐私验收
- 不区分账号不存在与密码错误；不回显响应体、密码、Cookie 或 CSRF 值。
- 旧流被 abort 后不生成跨项目引用、追问或错误气泡。

## 性能验收
- 匿名预约页受保护请求数为 0；同一认证身份只保持一条时段 SSE。

## 变更预算
- max_files：5
- expected_prod_lines：≤100
- expected_test_lines：≤120
- expected_doc_lines：≤75

## 必须运行的测试命令
- `pnpm test && pnpm typecheck && pnpm build`
- `pnpm exec playwright test`（Chromium 就绪后）
- `git diff --check`

## 回滚方法
- 回退本任务前端、测试和任务单；无外部状态或数据迁移。

## 强制停止条件
- 需要改变 API/SSE 字段、账号枚举策略、DB、依赖或 `<1024px` 产品边界；冻结断言失败；超出预算。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：Playwright Chromium 未安装前仅能完成 L1/L2 与生产构建验证
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
