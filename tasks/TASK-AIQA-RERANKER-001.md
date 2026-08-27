# TASK-AIQA-RERANKER-001 Cross-Encoder Reranker 与对照实验

> **状态：Closed（2026-08-27）**

## 任务类型
- implementation
- test
- evaluation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.4 / security 0.3 / test-plan 1.0
- 基线 commit：`5d2f934`

## 精确规范引用
- `docs/adr/ADR-RERANK-001.md`
- `docs/design/architecture.md §8.3`
- `docs/design/security.md §9/§11`
- `docs/test/test-plan.md TC-AI-012`

## 目标
- 实现可选 Cross-Encoder gateway、RRF 后置重排、失败回退、低基数观测和公开版本化对照证据。

## 非目标
- 不改 DB、公开 API、Prompt、工具权限、召回阈值，不安装本地模型框架。

## 允许修改路径
- `tasks/TASK-AIQA-RERANKER-001.md`
- `apps/api/app/config.py`
- `apps/api/app/aiqa/reranker.py`
- `apps/api/app/aiqa/runtime.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/app/observability.py`
- `apps/api/tests/aiqa/test_reranker.py`
- `apps/api/tests/test_observability.py`
- `apps/api/scripts/evaluate_reranker.py`
- `apps/api/.env.prod.example`
- `deploy/observability/grafana/dashboards/agent-overview.json`
- `apps/web/evals/latest.json`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `scripts/validate_eval_report.py`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、OpenAPI、领域模型、Prompt、工具注册、冻结验收测试断言。

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；复用运行时 `httpx==0.28.1`。
- 配置：新增 `JIANLI_RERANK_BASE_URL/API_KEY/MODEL/TIMEOUT_SECONDS/TOP_N`。

## 规范影响评估
- behavior_change：true（仅 KB 候选排序）。
- affected_specs：architecture/security/test-plan 已由 CR 更新；SRS/domain/openapi none。

## 功能、安全与性能验收
- 成功按 provider index/score 重排；失败完整保留 RRF 顺序；不扩大域过滤候选。
- 默认关闭不发网络请求；每次 KB 查询最多一次调用，超时≤5s。
- 指标/报告不含问题、候选、密钥或高基数 ID；真实 provider 证据与 deterministic 测试明确区分。

## 变更预算
- max_files：17
- expected_prod_lines：430
- expected_test_lines：180

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_reranker.py tests/test_observability.py tests/aiqa/test_agent_tools.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app tests/aiqa/test_reranker.py tests/test_observability.py scripts/evaluate_reranker.py && mypy app`
- `cd apps/web && pnpm test -- --run && pnpm typecheck && pnpm build`
- `python scripts/validate_eval_report.py apps/web/evals/latest.json`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；清空 Reranker 配置即运行时回退 RRF。

## 强制停止条件
- 需要 DB/公开 API/新依赖、改变拒答门槛或超 17 文件时停止。

## 交付证据
- commit / PR：核心实现 `64b5799`；公开对照证据 `c8f0e46`
- 修改文件清单：17 个允许路径（后端/配置/运维 7、测试/评测 4、公开证据/UI 4、任务与项目状态 2）
- 测试命令及结果：任务范围 API 27 passed / 1 既有 StarletteDeprecationWarning；Web Vitest 1 passed；真实 `Qwen/Qwen3-Reranker-8B` 组件对照 5 cases，MRR 0.3333→1.0000、Hit@1 0/5→5/5；报告校验 65/65
- lint / typecheck：Ruff pass；Mypy 50 source files / 0 errors；Web TypeScript pass；Vite production build pass
- DB 迁移验证：无
- 验收证据：成功重排、外部失败原序回退、索引/响应严格校验、默认关闭零外调；Prometheus/Grafana 新增 rerank outcome/P95；浏览器确认 65/65 与真实 provider 对照卡可见且控制台无错误
- 变更预算实际值：17/17 个允许路径；实现与证据约 575 新增、16 删除，未超行数预算合计
- 未解决风险：公开数值为 5 条人工构造候选集的真实 provider 组件评测，不宣称端到端生产质量；生产启用需配置独立 Reranker 凭证
- 是否偏离 TASK：否
- spec_sync：clean
- verified_commit：`c8f0e46`
