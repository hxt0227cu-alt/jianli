# TASK-CR-AIQA-RESILIENCE-001 Semantic Cache + Circuit Breaker 变更请求

> **状态：Approved / Closed（2026-08-27，verified_commit=`a73c5a8`）**

## 任务类型
- architecture
- security
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.4 / security 0.3 / test-plan 1.0
- 基线 commit：`fd96de2`

## 精确规范引用
- `docs/design/architecture.md §8.3/§9.4`
- `docs/design/security.md §9/§11`
- `docs/test/test-plan.md §2.2`
- `docs/adr/ADR-RESILIENCE-001.md`

## 需求来源
- 用户要求继续增强唯一公开作品的 Agent 开发岗竞争力，并已全权批准 Semantic Cache 与熔断器主线。

## 目标
- 批准匿名公共 grounded 回答的 Redis Semantic Cache，以及 LLM/Reranker 客户端熔断器与可观测状态。

## 非目标
- 不缓存登录态会话、工具调用、预约结果、拒答、错误或问题原文。
- 不新增 DB、公开 API、依赖、Prompt、工具或权限。

## 允许修改路径
- `tasks/TASK-CR-AIQA-RESILIENCE-001.md`
- `tasks/TASK-AIQA-RESILIENCE-001.md`
- `docs/adr/ADR-RESILIENCE-001.md`
- `docs/design/architecture.md`
- `docs/design/security.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用代码、迁移、OpenAPI、领域模型、Prompt、工具注册。

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；复用既有 `redis==8.1.0`。
- 配置：Semantic Cache 开关/TTL/阈值/容量；Circuit Breaker 失败阈值与恢复时间。

## 批准决策
- Cache 仅用于匿名、无 conversation_id、无预约工具步骤且最终 grounded 的公开回答；Redis 仅保存 embedding、回答、引用与固定元数据，不保存问题原文。
- Cache 按 page/project 域隔离，相似度默认 ≥0.94；TTL 默认 600 秒、每域最多 100 条；知识库上传/删除成功后全量失效。
- Redis/embedding/cache 失败一律旁路，不影响问答；不得将 Cache 当业务真相源。
- LLM 与 Reranker 分别使用进程内状态机熔断：连续 3 次逻辑失败打开 30 秒，之后单探针 half-open；成功恢复 closed。
- 熔断器只减少对故障 provider 的调用，不切换第二模型；开放/拒绝/恢复以及 cache hit/miss/bypass/error 使用固定枚举观测。

## 功能、安全与性能验收
- TC-AI-013：语义命中、域隔离、TTL/容量、知识变更失效、Redis 故障旁路、熔断 open/half-open/recover 与并发单探针。
- Cache 命中不进入回答生成；默认关闭时零 Redis cache 操作。
- 指标/Span/日志禁止问题、回答、embedding、key、用户/会话 ID 和异常正文。

## 变更预算
- max_files：8
- expected_prod_lines：210
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`。

## 强制停止条件
- 需要 DB/公开 API/新依赖/Prompt/权限变化或超 8 文件时停止。

## 交付证据
- commit / PR：`a73c5a8`
- 修改文件清单：8 个（本任务、下游任务、ADR、architecture、security、test-plan、baseline、PROJECT_STATE）
- 测试命令及结果：`git diff --cached --check` → pass
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：ADR accepted；architecture 0.5 / security 0.4 / test-plan 1.1 approved；TC-AI-013 已冻结
- 变更预算实际值：8 files，213 insertions / 9 deletions
- 未解决风险：实现与真实 Redis 行为由下游任务验证
- 是否偏离 TASK：否
- spec_sync：clean
- verified_commit：`a73c5a8`
