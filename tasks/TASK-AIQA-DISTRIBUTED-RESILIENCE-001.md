# TASK-AIQA-DISTRIBUTED-RESILIENCE-001 Redis 多副本熔断实现

> **状态：Closed（2026-08-27，verified_commit=`b8e973d`）**

## 任务类型
- implementation
- test
- ci

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.6 / security 0.5 / test-plan 1.2
- 基线 commit：`e6b1a1c`

## 精确规范引用
- `docs/adr/ADR-RESILIENCE-001.md`
- `docs/design/architecture.md §9.4`
- `docs/design/security.md §9`
- `docs/test/test-plan.md TC-AI-014`

## 目标
- 实现 Redis 原子共享熔断状态、本地 fail-open fallback，并使 CI 覆盖 TC-AI-013/014。

## 非目标
- 不 push、不新增 DB/API/依赖/Prompt/工具/权限。

## 允许修改路径
- `tasks/TASK-AIQA-DISTRIBUTED-RESILIENCE-001.md`
- `apps/api/app/aiqa/resilience.py`
- `apps/api/app/aiqa/gateway.py`
- `apps/api/app/aiqa/runtime.py`
- `apps/api/tests/aiqa/test_resilience.py`
- `apps/api/tests/aiqa/test_distributed_resilience.py`
- `apps/api/tests/test_observability.py`
- `.github/workflows/agent-quality-gate.yml`
- `scripts/validate_eval_report.py`
- `apps/web/evals/latest.json`
- `tests/web-shell/shell.test.ts`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、OpenAPI、领域模型、Prompt、工具注册、冻结测试断言。

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；复用既有 Redis 与 Lua `EVAL`。
- Redis key：固定 `jianli:aiqa:circuit:{llm|reranker}`，无高基数或用户数据。

## 规范影响评估
- behavior_change：true；architecture/security/test-plan 已批准，SRS/domain/openapi none。

## 功能、安全与性能验收
- 跨实例共享 failure/open/probe/recovery；状态转换原子；key 自动过期。
- Redis 故障退回本地 breaker；LLM 异步路径不得同步阻塞事件循环。
- CI 显式运行 TC-AI-013/014 与评测报告校验；本地完成等价三作业验证。

## 变更预算
- max_files：12
- expected_prod_lines：280
- expected_test_lines：220

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_resilience.py tests/aiqa/test_distributed_resilience.py tests/aiqa/test_semantic_cache.py tests/test_observability.py tests/aiqa/test_agent_tools.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app tests/aiqa/test_resilience.py tests/aiqa/test_distributed_resilience.py tests/aiqa/test_semantic_cache.py tests/test_observability.py && mypy app`
- `python scripts/validate_eval_report.py`
- `pnpm test && pnpm typecheck && pnpm build`
- `git diff --check`

## 回滚方法
- `git revert <实现提交>`；Redis 不可用时自动退回本地实现。

## 强制停止条件
- 需要 DB/API/新依赖/Prompt/权限变化、Redis key 含高基数数据或超 12 文件时停止。

## 交付证据
- commit / PR：核心实现 `b8e973d`；证据收口见后续提交
- 修改文件清单：11 个，均在允许路径内
- 测试命令及结果：绑定验收 37 passed；GitHub backend 等价作业 40 passed；真实 PG/Redis RAG 等价作业 4 passed / 1 expected xfail；Web 1 passed + typecheck/build pass；真实 Redis 分布式测试 5 passed
- lint / typecheck：Ruff pass；Mypy 52 source files / 0 errors；TypeScript pass
- DB 迁移验证：无
- 验收证据：TC-AI-014 6/6；两个 Redis 客户端共享 failure/open，跨实例仅一个 half-open probe；Redis 故障本地 fallback；LLM breaker I/O 不阻塞事件循环；公开评测 79/79
- 变更预算实际值：11 files；核心实现 358 insertions / 16 deletions，低于 500 行合计预估
- 未解决风险：无代码或质量门禁风险；GitHub 远端 run 尚未产生是遵守用户“不完成不得 push”的发布约束，本地三作业等价门禁已通过
- 是否偏离 TASK：否
- spec_sync：clean
- verified_commit：`b8e973d`
