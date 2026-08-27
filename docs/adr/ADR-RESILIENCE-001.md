# ADR-RESILIENCE-001：AIQA Semantic Cache 与 Provider 熔断

- 状态：accepted
- 日期：2026-08-27
- 决策者：用户显式全权批准
- 依据：architecture 0.5 / security 0.4 / test-plan 1.1

## 决策

使用既有 Redis 实现可选 Semantic Answer Cache，仅缓存匿名公共 grounded 回答；使用进程内、线程安全的 closed/open/half-open Circuit Breaker 保护 LLM 与 Reranker provider。

## Cache 边界

- Redis 只保存 question embedding、回答、公开引用和固定模型元数据，不保存问题原文、用户/会话标识或工具结果。
- page/project 域隔离，相似度默认 0.94，TTL 600 秒，每域最多 100 条。
- 仅 grounded 成功回答写入；登录态、conversation_id、工具路径、拒答和错误全部 bypass。
- 知识库上传/删除成功后清空命名空间；Redis 或 embedding 失败旁路，不影响主请求。

## Circuit Breaker 边界

连续 3 次逻辑失败后 open 30 秒；恢复窗口后只允许一个 half-open 探针。成功恢复 closed，失败重新 open。熔断只阻止对已故障 provider 的调用，不提供第二模型 fallback。

## 可观测与隐私

仅记录 cache `hit/miss/bypass/error` 与 circuit `opened/rejected/recovered`、固定组件名和耗时；禁止正文、embedding、Redis key、异常正文或高基数 ID。
