# TASK-AIQA-RESILIENCE-001 Semantic Cache + Circuit Breaker 实现

> **状态：Ready（2026-08-27）**

## 任务类型
- implementation
- test
- observability

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.5 / security 0.4 / test-plan 1.1
- 基线 commit：待 CR 提交

## 精确规范引用
- `docs/adr/ADR-RESILIENCE-001.md`
- `docs/design/architecture.md §8.3/§9.4`
- `docs/design/security.md §9/§11`
- `docs/test/test-plan.md TC-AI-013`

## 目标
- 实现匿名 grounded Semantic Cache、LLM/Reranker 熔断状态机及低基数可观测证据。

## 非目标
- 不缓存登录态/工具/拒答/错误，不改 DB/API/Prompt/权限，不新增依赖。

## 允许修改路径
- `tasks/TASK-AIQA-RESILIENCE-001.md`
- `apps/api/app/config.py`
- `apps/api/app/aiqa/resilience.py`
- `apps/api/app/aiqa/semantic_cache.py`
- `apps/api/app/aiqa/gateway.py`
- `apps/api/app/aiqa/reranker.py`
- `apps/api/app/aiqa/runtime.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/app/observability.py`
- `apps/api/tests/aiqa/test_resilience.py`
- `apps/api/tests/aiqa/test_semantic_cache.py`
- `apps/api/tests/test_observability.py`
- `deploy/observability/grafana/dashboards/agent-overview.json`
- `apps/api/.env.prod.example`
- `apps/web/evals/latest.json`
- `tests/web-shell/shell.test.ts`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、OpenAPI、领域模型、Prompt、工具注册、冻结测试断言。

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；复用 `redis==8.1.0`。
- 配置：`JIANLI_SEMANTIC_CACHE_*` 与 `JIANLI_CIRCUIT_BREAKER_*`。

## 规范影响评估
- behavior_change：true（仅匿名 grounded 回答可复用；故障 provider 快速失败）。
- affected_specs：architecture/security/test-plan 已更新；SRS/domain/openapi none。

## 功能、安全与性能验收
- Cache hit/miss/域隔离/失效/故障旁路；命中不执行第二轮回答生成。
- Breaker 连续失败、open 拒绝、恢复单探针、成功关闭；LLM/Reranker 独立。
- 指标/Span/Redis 无问题原文、用户/会话、工具/预约、key 或异常正文。

## 变更预算
- max_files：17
- expected_prod_lines：560
- expected_test_lines：260

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_resilience.py tests/aiqa/test_semantic_cache.py tests/test_observability.py tests/aiqa/test_agent_tools.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app tests/aiqa/test_resilience.py tests/aiqa/test_semantic_cache.py tests/test_observability.py && mypy app`
- `cd apps/web && pnpm test -- --run && pnpm typecheck && pnpm build`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；关闭 Semantic Cache 配置即可停用缓存。

## 强制停止条件
- 需要 DB/API/新依赖/Prompt/权限变化、缓存敏感内容或超 17 文件时停止。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- spec_sync：clean
- verified_commit：待回填
