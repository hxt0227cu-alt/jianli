# TASK-WEB-FOLLOWUP-SCOPE-001 推荐追问检索域路由修复

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：9b333b0da18402734d1fa9f3c9cbf3df82003a54

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.2
- `docs/requirements/use-cases.md` UC-03 / UC-04 / UC-05
- `docs/test/test-plan.md` TC-AI-001 / TC-AI-004 / TC-AI-006

## 需求来源
- `TASK-AIQA-RECOMMENDATION-RECALL-001` 页面验收发现：随机追问池同时包含 Jianli、Sleep、Litchi 与通用职业问题，但请求始终继承当前项目 `project_key`，导致跨域推荐问题 0 命中并误报越界。

## 目标
为每条站内追问绑定其真实检索域；项目技术题检索对应项目，跨项目与职业/行为题检索简历与全部项目。

## 非目标（明确排除）
- 不修改后端、API、数据库、依赖、语料、检索阈值或检索算法。
- 不改变用户自由输入问题默认继承当前页面上下文的行为。
- 不降低越界与隐私拒答断言。

## 允许修改路径
- `tasks/TASK-WEB-FOLLOWUP-SCOPE-001.md`
- `apps/web/main.tsx`
- `tests/web-shell/shell.test.ts`

## 禁止修改路径
- `apps/api/**`
- `apps/web/styles.css`、`apps/web/appointment.css`
- API / migration / dependency / auth / agent-tool 相关文件

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：修复推荐问题未按其内容域发送的前端 Bug，使其重新符合已批准的推荐问题正常问答流程。

## 功能验收
- “你适合什么样的团队和岗位？”与“你最有成就感的一段工程经历是哪一段？”使用 `page_key=resume` 且不携带 `project_key`。
- Litchi 与 Sleep 技术追问分别携带对应项目过滤，不继承当前展示项目。
- 普通输入和 API 首屏推荐仍默认使用当前页面/项目上下文。

## 安全与隐私验收
- 仅改变已有公开问题的检索域元数据；不扩大 API 权限、数据可见性或工具能力。
- 真正越界、隐私问题仍由后端证据门和护栏拒答。

## 性能验收
- 不新增网络请求、模型调用或检索阶段。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：35
- expected_test_lines：8

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- 浏览器在项目页点击并实问两道通用追问，均显示引用与“已基于资料回答”。

## 回滚方法
- 回退 `FOLLOWUP_POOL` 结构化检索域与 `send` 的请求域选择逻辑。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要修改公开 API、后端检索、数据库、依赖、权限或 Prompt 时立即停止。
- 冻结 Web 验收失败或超过 3 个文件时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待完成
- 修改文件清单：待完成
- 测试命令及结果：待完成
- lint / typecheck：待完成
- DB 迁移验证：无
- 验收证据：待完成
- 变更预算实际值：待完成
- 未解决风险：待完成
- 是否偏离 TASK：待完成
- 规范影响结论：none
- spec_sync：待完成
- verified_commit：待完成

## 关联
- 前置任务：`TASK-AIQA-RECOMMENDATION-RECALL-001`
- 测试任务：TC-AI-001 / TC-AI-004 / TC-AI-006
