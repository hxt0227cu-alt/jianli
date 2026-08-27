# ADR-RERANK-001：RRF 后置 Cross-Encoder 重排

- 状态：accepted
- 日期：2026-08-27
- 决策者：用户显式全权批准
- 依据：architecture 0.4 / security 0.3 / test-plan 1.0

## 决策

保留 vector + BM25 + RRF 作为高召回候选生成层，在域过滤和相关性门槛之后，对最多 12 个候选调用可选的 OpenAI 风格 `/rerank` Cross-Encoder 服务，最终取 top6。默认未配置时保持原 RRF 顺序。

## 失败策略

Reranker 超时、限频、服务错误、索引越界或畸形响应时 fail-open：返回原候选顺序并记录固定失败类别；回答仍受既有 grounded/拒答约束。独立超时上限 5 秒，每次检索最多一次请求。

## 数据与可观测边界

- 只发送当前问题和已经过页面/项目域过滤的候选片段，不发送账号、会话、预约或后台数据。
- 指标与日志只记录 `completed/fallback/disabled`、候选数量、耗时和模型配置名，不记录问题、片段或服务异常正文。
- 对照报告分别标识 deterministic protocol 与真实 provider，真实运行缺失时不得声称质量提升。

## 放弃方案

- 不在 API 镜像安装 PyTorch、Transformers 或模型权重，避免显著扩大镜像与冷启动成本。
- 不让 reranker 扩大召回范围或推翻无证据拒答门槛。
- 不加入第二套向量库、缓存或微服务。
