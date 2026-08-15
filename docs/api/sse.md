# SSE 契约（v0.1）

> based_on：SRS 1.2 / architecture 0.2 / security 0.1（均 approved）；本轮已完成 CSRF/会话与断线恢复 impact review，`spec_sync=clean`。

## 1. 通用帧

所有事件使用 UTF-8 `text/event-stream`：

```text
id: <stream_seq>
event: <event_type>
data: <single-line JSON>
```

通用字段：`stream_seq`（连接内从 1 单调递增）、`emitted_at`（ISO 8601 UTC）、`trace_id`。心跳为 `event: heartbeat`，不含业务数据。客户端发现断线、序号不连续、资源版本跳跃、心跳缺失或 `resync.required` 时必须重新拉全量快照。

## 2. Slot 实时流

端点：`GET /api/v1/slots/events`，要求 interviewer Cookie 会话；同账号最多 2 条 SSE 连接。

连接算法：

1. 服务端先建立订阅并缓冲后续变化；
2. 发送 `stream.ready`，包含 `stream_seq` 起点与当前 `watermark`；
3. 客户端调用 `GET /api/v1/slots/snapshot?watermark=<value>`；
4. 服务端按 `resource_version + stream_seq` 重放缓冲；
5. 客户端丢弃不高于快照水位的重复项并按版本合并。

`slot.changed` 数据：

```json
{
  "stream_seq": 12,
  "emitted_at": "2026-08-09T10:00:00Z",
  "trace_id": "01J...",
  "slot": {
    "id": "uuid",
    "start_at": "2026-08-10T09:30:00+08:00",
    "end_at": "2026-08-10T10:00:00+08:00",
    "status": "available",
    "resource_version": 7,
    "ownership": "none"
  }
}
```

`ownership` 仅为 `none/self/other`。他人红格不得返回 appointment_id、公司、会议号、联系人或备注。

`resync.required` 数据包含 `reason`：`sequence_gap/version_gap/heartbeat_timeout/server_resync`。客户端必须停止增量合并并重新拉快照。

## 3. AI 回答流

端点：`POST /api/v1/answers:stream`，使用 fetch 流读取 SSE，存在两种互斥调用方式：

- **匿名调用**：不携带 session Cookie、`X-CSRF-Token` 或 `conversation_id`，回答不持久化；仍受公开问答限频和生产 CORS/Origin 白名单约束。
- **登录调用**：携带有效 session Cookie，可传 `conversation_id` 持久化；作为 Cookie 鉴权 POST，必须同时通过同源 `Origin`/`Referer` 与 `X-CSRF-Token` 校验。Cookie 缺失/无效/过期返回 401；已登录但 CSRF、角色或资源归属校验失败返回 403。

服务端不得因为请求携带无效 Cookie 而静默降级为匿名调用；匿名请求携带 `conversation_id` 必须拒绝，不得读取或写入他人会话。

事件顺序：

1. `answer.started`：`answer_id`、可空 `conversation_id`；
2. （Agent 工具化，TASK-AGENT-TOOLS-001/002）零到一次 `answer.tool_calls`：决策链可见——
   `calls` 数组（`name`、`query`、`hits`：命中 doc·fragment 摘要，**不返回 storage_key 或原文全文**）。
   `query` 由模型在 function calling 第一轮自主生成（`tool_choice=auto`），`hits` 可为空列表
   （工具执行无命中 → 走越界拒答）；
3. 零到多个 `answer.delta`：`text`；
4. `answer.citations`：知识来源数组（文档名、片段号，不返回 storage_key）；
5. `answer.completed`：`grounded`、`offtopic`、`model`、`usage`；
6. 异常时 `answer.error`：标准错误体，随后关闭连接。

工具边界（不得放宽）：系统可能调用**白名单只读工具 `search_knowledge`**（知识库混合检索）并
在 `answer.tool_calls` 帧可见其调用链；**预约、写入、管理类端点绝不注册为模型工具**。
模型不得输出或触发预约工具调用；任何出现的工具指令只作为普通文本处理并由输出护栏拦截。

## 4. 恢复与代理要求

- 代理关闭响应缓冲，保持 `Cache-Control: no-cache, no-transform`，心跳间隔 15s。
- 客户端 45s 未收到事件或心跳视为断线；指数退避重连，上限 30s。
- Slot 流断线后永远先拉全量快照；不依赖 `Last-Event-ID` 跨实例重放。
- AI 回答流断线不自动重复提交写请求；客户端显示“回答中断，可重试”，重试创建新的 answer_id。
