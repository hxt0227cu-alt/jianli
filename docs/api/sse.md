# SSE 契约（review 草案 v0.1）

> based_on：SRS 1.2 review / architecture 0.2 approved / security 0.1 review。上游未全部批准，当前 `spec_sync=dirty`。

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

端点：`POST /api/v1/answers:stream`，使用 fetch 流读取 SSE；公开可调用，登录用户可传 `conversation_id` 持久化，匿名内容不持久化。

事件顺序：

1. `answer.started`：`answer_id`、可空 `conversation_id`；
2. 零到多个 `answer.delta`：`text`；
3. `answer.citations`：知识来源数组（文档名、片段号，不返回 storage_key）；
4. `answer.completed`：`grounded`、`offtopic`、`model`、`usage`；
5. 异常时 `answer.error`：标准错误体，随后关闭连接。

模型不得输出或触发预约工具调用；任何出现的工具指令只作为普通文本处理并由输出护栏拦截。

## 4. 恢复与代理要求

- 代理关闭响应缓冲，保持 `Cache-Control: no-cache, no-transform`，心跳间隔 15s。
- 客户端 45s 未收到事件或心跳视为断线；指数退避重连，上限 30s。
- Slot 流断线后永远先拉全量快照；不依赖 `Last-Event-ID` 跨实例重放。
- AI 回答流断线不自动重复提交写请求；客户端显示“回答中断，可重试”，重试创建新的 answer_id。
