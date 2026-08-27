# ADR-OBS-001：AIQA 可观测闭环

- 状态：accepted
- 日期：2026-08-27
- 决策者：用户显式全权批准
- 依据：architecture 0.3 / security 0.2 / test-plan 0.9

## 决策

采用 OpenTelemetry SDK + OTLP/HTTP 导出 Trace，Prometheus client 暴露内部指标，Prometheus 抓取并由 Grafana 展示。可观测能力保持应用内轻量埋点，采集后端作为独立 Compose 服务，不拆微服务。

## 边界

- `/internal/metrics` 仅容器私网直连；Nginx 明确拒绝，且不进入公开 OpenAPI。
- 指标标签限定为规范化 route、HTTP method/status、AIQA outcome、固定工具名/status、token kind。
- Span 属性限定为阶段、结果、白名单工具名、模型名、token 数和耗时；禁止业务原文、PII、密钥、高基数 ID 与异常正文。
- OTLP endpoint 未配置时 no-op；Collector/Prometheus 故障不得改变业务结果。

## 选择理由

- OpenTelemetry 提供厂商中立的 Trace 语义，未来替换后端无需改业务埋点。
- Prometheus/Grafana 是招聘 JD 可识别、可本地演示的指标闭环；无需新增数据库或云账号。
- 使用固定标签和私网抓取，避免指标基数膨胀与监控面泄露。

## 放弃方案

- 不直接把 trace_id/conversation_id/user_id 作为 Prometheus 标签。
- 不在公网暴露 metrics，不把 Grafana 嵌入公开作品页面。
- 不引入 ELK/Loki/Tempo；当前 JSON 日志和 OTLP Trace 已足够证明闭环。

## 重裁触发

- 多实例 Prometheus 指标需要集中聚合或 exemplar；需要日志统一查询；需要生产告警与 on-call；届时另立任务。
