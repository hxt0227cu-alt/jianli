# TASK-WEB-RECOVERY-UI-001 Web 失败恢复与预约页面尺度修复

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：164fa1b9928f1df69608568e48a7978fa7b85d96

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.1、§3.3、§8
- `docs/requirements/use-cases.md` UC-01、UC-06、UC-10
- `docs/design/ui-wireframe.md` U1、U4、U10
- `TC-WEB-001`（现有 Web 壳冻结验收）

## 需求来源
- 用户 2026-08-29 本地验收反馈：我的预约页面尺度不合理、登录失败原因不清晰、PDF 原生失败页不可控。

## 目标
修正我的预约页面宽度与加载/错误/空态互斥，提供符合防枚举要求的中文登录错误，并为简历 PDF 加载失败增加可重试兜底。

## 非目标（明确排除）
- 不区分“账号不存在”和“密码错误”，继续遵守 `INVALID_CREDENTIALS` 防账号枚举约束。
- 不修改登录、会话、预约、PDF 文件内容或任何后端业务规则。
- 不处理生产部署、域名、邮件、飞书、Agent 或知识库。

## 允许修改路径
- `apps/web/main.tsx`
- `apps/web/my-appointments.tsx`
- `apps/web/appointment.css`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `tasks/TASK-WEB-RECOVERY-UI-001.md`

## 禁止修改路径
- `apps/api/**`
- `docs/api/**`
- `docs/requirements/**`
- 数据库迁移、依赖清单、密钥与部署配置

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact，每个代码 TASK 必填）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：本任务是使前端错误展示、PDF 失败恢复和页面布局重新符合已批准 SRS/UI 的缺陷修复，不改变业务或接口行为。

## 功能验收
- “我的预约”使用可用内容宽度，加载、失败、空数据三种状态不会同时误显；失败态支持重试。
- 登录网络不可达、凭证错误、邮箱未验证、限频和请求格式错误均显示对应中文提示。
- 账号不存在与密码错误仍统一显示“邮箱或密码错误”，不得暴露账号存在性。
- PDF 可用时继续使用真实 `/resume.pdf` iframe；不可用时显示站内失败说明和重试按钮，不暴露浏览器原生拒绝页。
- “我的预约”页顶栏标题与当前导航一致。

## 安全与隐私验收
- 不修改服务端 `INVALID_CREDENTIALS` 同码同文案契约。
- 错误提示不得回显密码、原始响应体或邮箱存在性。

## 性能验收
- 不新增外部请求；PDF 预检仅在进入简历页或用户主动重试时执行一次 HEAD。

## 变更预算（change_budget）
- max_files：6
- expected_prod_lines：180
- expected_test_lines：30

## 必须运行的测试命令
- `npm run test`
- `npm run typecheck`
- `npm run build`
- 浏览器验收：我的预约失败/空态、登录失败提示、PDF 成功与失败兜底

## 回滚方法
- 回滚本任务提交；无数据库迁移或外部状态需要恢复。

## 强制停止条件（与 `AGENTS.md §2` 一致）

- 出现未批准的 API、数据库、依赖、鉴权或安全策略变化立即停止。
- 冻结测试失败或实际修改超过 6 个文件立即停止，不得降低断言。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`1b0033681107d28a8bd8425b893f725651ce1ec2`
- 修改文件清单：`apps/web/main.tsx`、`apps/web/my-appointments.tsx`、`apps/web/appointment.css`、`apps/web/styles.css`、`tests/web-shell/shell.test.ts`、本任务单；均在允许路径内
- 测试命令及结果：WSL `npm run test` → 1 passed；`npm run build` → production build passed（1793 modules）
- lint / typecheck：WSL `npm run typecheck` → 0 error；`git diff --check` → 0 error
- DB 迁移验证：无
- 验收证据：本地 `http://127.0.0.1:5173/resume.pdf` HEAD 200 / `application/pdf`；浏览器真实 PDF 成功渲染；不存在邮箱登录统一显示“邮箱或密码错误，请检查后重试”；匿名进入“我的预约”仅显示全宽可恢复错误态且顶栏标题正确；受控移除 PDF 时 DOM 显示“简历暂时无法加载”及“重新加载”，随后已恢复 PDF 并复验 200
- 变更预算实际值：6/6 文件；生产代码 +127/-36 行，测试 +12/0 行，未超预算
- 未解决风险：整个前端进程完全停机时无法由已停机的页面代码展示兜底，正式部署仍须依赖容器探活与自动重启；本任务已覆盖应用仍运行时的 API/PDF 失败恢复
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`1b0033681107d28a8bd8425b893f725651ce1ec2`

## 关联
- Change Request：无（符合现有规范的缺陷修复）
- 测试任务：TC-WEB-001
