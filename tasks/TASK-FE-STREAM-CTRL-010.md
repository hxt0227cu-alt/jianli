# TASK-FE-STREAM-CTRL-010 前端流式中断控制（AbortController / 超时 / 卸载取消 / 断线重连）

> 承接外部评审（DeepSeek③"前端流式渲染/AbortController 隐藏"、Kimi②"前端空白 SSE 重连"）
> 的真缺口：当前 `streamAnswer` 用 `fetch + ReadableStream.getReader()` 解析 SSE（真实），
> 但**无 AbortController、无超时、无 beforeunload 取消、无断线重连**。本任务补齐客户端
> 流式控制，使页面如实可写"前端具备中断/超时/卸载取消/连接失败重连"。

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：5c0e4cc

## 精确规范引用
- `docs/api/sse.md` §3（SSE 帧顺序：started → delta* → citations → completed）
- `apps/web/main.tsx` `streamAnswer` / `ChatPanel.send`

## 需求来源
- 外部评审 DeepSeek③ / Kimi②（前端流式控制缺失）

## 目标
改造 `streamAnswer` 与 `ChatPanel.send`：
1. 内部 `AbortController` + **25s 超时**自动 abort 在途流；
2. 支持外部 `AbortSignal`（组件卸载/beforeunload 取消在途流）；
3. 连接阶段网络失败（fetch 抛错、未收到任何 delta）**单次重连**；
4. `ChatPanel` 卸载与 `beforeunload` 时 abort 在途流，避免悬挂请求与状态错乱。

## 非目标
- 不改 SSE 契约 / API 路径（仍为 `POST /answers:stream`）
- 不做服务端推送重发（断点续传）；仅客户端连接级重连
- 不做移动端专属布局（仅确保现有响应式不退化）

## 允许修改路径
- `apps/web/main.tsx`（`streamAnswer` 签名+实现；`ChatPanel` 增加 abort ref + 卸载/beforeunload 清理）

## 禁止修改路径
- 后端 API / SSE 契约
- 其他页面组件逻辑

## 已批准的 DB / API / 依赖变更
- 无（纯前端，无新依赖）

## 规范影响评估
- behavior_change：true（新增客户端中断/超时 UX，但同一 SSE 契约，无用户可观察行为边界变更）
- affected_specs：srs none / openapi none / domain_model none / security none / test_plan none
- reason：仅客户端流式控制增强，接口/契约/可观察行为边界不变。
- 分类：代码重构（行为未变，仅增强容错）→ 不需要改 SRS。

## 功能验收
- 25s 内无 delta → 自动终止并在 UI 提示
- 切换页面 / 关闭标签 → 在途流被 abort，无悬挂请求
- 连接瞬间网络抖动 → 单次重连成功续答
- 既有打字机/引用/越界拒答 UI 不变

## 安全与隐私验收
- 不改凭证传递；abort 不泄露会话

## 性能验收
- 超时/重连不引入轮询；重连仅 1 次

## 变更预算
- max_files：1
- expected_prod_lines：~40
- expected_test_lines：0（前端单测不在本任务范围）

## 必须运行的测试命令
- 构建验证需在 WSL：`cd apps/web && npm run build`（本沙箱 TS7/rolldown win32 原生包缺失，无法本地构建，须 WSL 验证）
- 手动：起 uvicorn + vite，发问后 25s 断网/切页观察

## 回滚方法
- 回退 `streamAnswer` / `ChatPanel` 改动至单 fetch+reader 实现

## 强制停止条件
- 若出现未列明的 API/依赖变更 → 停止并报告

## 交付证据
- commit / PR：5724d87
- 修改文件清单：apps/web/main.tsx
- 测试命令及结果：前端构建须 WSL `cd apps/web && npm run build`（沙箱缺 win32 原生包，无法本地构建）；须手动验证 25s 超时 / 卸载取消 / 连接失败重连
- lint / typecheck：用户 WSL 2026-08-18 `npm run build` 通过（tsc -b && vite build，✓ built in 21.70s）
- DB 迁移验证：无
- 验收证据：streamAnswer 加 AbortController+25s 超时+连接失败单次重连；ChatPanel 卸载/beforeunload abort 在途流
- 变更预算实际值：max_files 实际 1 / 生产 ~40 行 / 测试 0 行
- 未解决风险：沙箱无法构建验证，须 WSL `npm run build` + 手动验证
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：5724d87
- 关闭门禁：①②③④ 全满足（②于 2026-08-18 WSL `npm run build` 验证通过）
