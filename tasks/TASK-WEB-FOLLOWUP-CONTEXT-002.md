# TASK-WEB-FOLLOWUP-CONTEXT-002 当前项目追问可见范围修复

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：44c7848

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.2
- `docs/requirements/use-cases.md` UC-03 / UC-04 / UC-05
- `docs/test/test-plan.md` TC-AI-001 / TC-AI-004 / TC-AI-006

## 需求来源
- 页面二验收发现：当前选择 Jianli 项目时，随机追问区仍会展示 Litchi 专属技术问题。上一任务只修正了点击后的检索域，没有约束问题的可见项目范围。

## 目标
- 项目页首屏推荐只展示当前项目技术问题；回答后展示两条当前项目技术追问和一条通用职业追问。
- Jianli、Sleep、Litchi 三个项目之间不再互相展示专属追问。
- 保留每条追问携带自身证据域的既有路由机制。
- 将前端 Sleep 项目标识 `sleep` 转换为 API 契约标识 `sleep202603_an`，确保专属题可正常请求。

## 非目标（明确排除）
- 不修改后端、API、数据库、依赖、Prompt、知识库语料、检索阈值或检索算法。
- 不改变用户自由输入问题默认继承当前页面上下文的行为。
- 不降低越界、隐私或无依据拒答断言。

## 允许修改路径
- `tasks/TASK-WEB-FOLLOWUP-CONTEXT-002.md`
- `apps/web/main.tsx`
- `tests/web-shell/shell.test.ts`

## 禁止修改路径
- `apps/api/**`
- `apps/web/styles.css`
- `apps/web/appointment.css`
- API / migration / dependency / auth / agent-tool 相关文件

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：none
- reason：修复推荐追问展示上下文与当前项目不一致的前端缺陷，使推荐问题符合现有项目上下文约束。

## 功能验收
- Jianli 页只出现 `projectKey: 'jianli'` 的技术追问和 `pageKey: 'resume'` 的通用追问。
- Sleep 页只出现 `projectKey: 'sleep'` 的技术追问和通用追问。
- Litchi 页只出现 `projectKey: 'litchi'` 的技术追问和通用追问。
- 首屏推荐展示三条当前项目题；每次刷新追问保证两条项目题和一条通用题；点击后仍按问题自身域请求。
- Sleep 页面自由输入和专属追问均发送 `project_key=sleep202603_an`，不再触发 422。

## 安全与隐私验收
- 仅收窄已有公开问题的前端可见范围，不扩大数据可见性、权限或工具能力。

## 性能验收
- 不新增网络请求、模型调用或检索阶段。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：50
- expected_test_lines：12

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- 浏览器分别切换 Jianli、Sleep、Litchi，验证推荐追问不包含其他项目专属题。

## 回滚方法
- 回退 `FOLLOWUP_POOL` 项目题补充与 `refreshFollowups` 的项目筛选逻辑。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要修改公开 API、后端检索、数据库、依赖、权限或 Prompt 时立即停止。
- 冻结 Web 验收失败或超过 3 个文件时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待填写
- 修改文件清单：待填写
- 测试命令及结果：待填写
- lint / typecheck：待填写
- DB 迁移验证：无
- 验收证据：待填写
- 变更预算实际值：待填写
- 未解决风险：待填写
- 是否偏离 TASK：待填写
- 规范影响结论：待填写
- spec_sync：待填写
- verified_commit：待填写

## 关联
- 前置任务：`TASK-WEB-FOLLOWUP-SCOPE-001`
- 测试任务：TC-AI-001 / TC-AI-004 / TC-AI-006
