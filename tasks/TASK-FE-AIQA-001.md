# TASK-FE-AIQA-001 前端 AI 问答页（ChatPanel 真实化）

> **状态**：Open（2026-08-13 建，用户选定"前端 AI 问答页"为下一步方向，加速口径=主线代码开发、验证一轮跑完）
> **依赖**：后端 M6 已关闭（9 operation 全实现验证，`/answers:stream` SSE 契约见 `docs/api/sse.md` §3）

## 1. 任务类型
- implementation（前端域，apps/web）

## 2. 精确规范引用
- `docs/api/sse.md` §3：SSE 帧 `id/event/data`，事件 `answer.started` / `answer.delta` / `answer.citations` / `answer.completed` / `answer.error`；completed 含 `grounded` / `offtopic` / `model`
- OpenAPI v0.2：`getPageContent`（GET /pages/{page_key}）、`listRecommendedQuestions`（GET /pages/{page_key}/recommendations）、`streamAnswer`（POST /answers:stream，匿名免 CSRF；带 cookie 有效会话须 `X-CSRF-Token` + 同源）
- 既有前端：`apps/web/main.tsx`（`api()` 封装 + `csrfCookie()` + `ChatPanel` 静态占位）

## 3. 目标
把 `ChatPanel` 从静态占位改为**真实 SSE 问答**：推荐问题加载与点击发送、`POST /answers:stream` 流式渲染（fetch + ReadableStream 解析，EventSource 不支持 POST）、引用（citations）展示、越界/grounded 状态徽标、错误处理、回答中禁用输入。resume 页 `page_key=resume`、projects 页 `page_key=projects + project_key=当前项目`；interview/mine 页保留静态降级版（不动既有文案）。

## 4. 非目标
- 历史会话列表真实化（`listConversations` 需登录会话 UI，后续轮次）
- 知识库管理后台页（admin UI，后续）
- 移动端适配；页面一 PDF 内容替换（待真实 PDF 素材）

## 5. 允许修改路径（change_budget：max_files=4）
- `apps/web/main.tsx`（ChatPanel 改造 + ProjectView selected 受控提升 + App 传 pageKey/projectKey）
- `vite.config.ts`（proxy 补 `/pages` `/answers` `/conversations` `/admin` → 127.0.0.1:8000）
- `tests/web-shell/shell.test.ts`（**仅新增**真实问答锚点断言，保留全部既有断言——interview/mine 静态降级保留 `'不会发送真实请求'` 文案，旧断言全部继续通过；如实登记测试演进）
- `PROJECT_STATE.md` / `tasks/TASK-FE-AIQA-001.md`

## 6. 禁止修改路径
- 后端 `apps/api/**`、迁移、契约（本任务纯前端）
- 既有预约/我的预约流程（main.tsx 其余视图 + my-appointments.tsx 不得破坏——shell.test 锚点守住）

## 7. 验收标准
- `npm run typecheck`（tsc --noEmit）通过
- `npm test`（vitest shell.test.ts）通过（旧断言全保留 + 新锚点）
- `npm run build`（tsc -b && vite build）通过
- 手动（用户 WSL dev 环境）：resume 页提问 → 流式回答 + 推荐问题可点；projects 页提问带 project_key；越界问题显示拒答徽标

## 8. 强制停止条件
- 出现未列明变更（改后端/契约/删除既有断言）→ 停止报告

## 9. 交付证据（关闭前填写）
- *实现后回填*（commit / typecheck / vitest / build 结果）

## 10. 关联
- 前置：M6 后端已关闭（`/answers:stream` 就绪）
- 后续：历史会话 UI（登录）、知识库管理页、真实内容素材
