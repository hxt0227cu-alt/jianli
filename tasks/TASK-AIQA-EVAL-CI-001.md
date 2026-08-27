# TASK-AIQA-EVAL-CI-001 评测证据板与 GitHub Actions 门禁实现

> **状态：Closed（2026-08-27）**

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / UI 1.0.3 / OpenAPI-SSE 0.9 / test-plan 0.8
- 基线 commit：`f65c7db`

## 精确规范引用
- `docs/requirements/SRS.md §3.1–§3.2`
- `docs/design/ui-wireframe.md U2`
- `docs/test/test-plan.md TC-AI-011`
- `TASK-CR-AIQA-EVAL-CI-001`

## 需求来源
- 已批准 `TASK-CR-AIQA-EVAL-CI-001`。

## 目标
以版本化机器报告展示真实评测结果/失败边界，并让 push/PR 自动执行 Agent、RAG 和交付质量门禁。

## 非目标
- 不新增 API、DB、依赖、工具权限、鉴权或 Prompt。
- 不修改既有评测断言，不伪造 GitHub run 状态。
- 不实现 OTel/Prometheus/Grafana、Reranker、K8s 或在线 A/B。

## 允许修改路径
- `tasks/TASK-AIQA-EVAL-CI-001.md`
- `.github/workflows/agent-quality-gate.yml`
- `apps/web/evals/latest.json`
- `scripts/validate_eval_report.py`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/app/**`、`apps/api/tests/**`、migrations、依赖清单、规范工件。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无；CI 只安装仓库现有依赖并使用官方 GitHub Actions / pgvector / Redis 服务镜像。

## 规范影响评估
- behavior_change：true
- affected_specs：SRS/UI/test-plan 已由上游 CR 更新；domain/openapi/security none。
- reason：本任务只实现批准态。

## 功能验收
- jianli 页面展示套件通过数/总数、验证 commit/日期、CI 状态和失败/边界案例。
- 报告为版本化 JSON；校验器检查 schema、总数、枚举、大小和敏感字段名。
- workflow 在 push/PR 分别执行 backend-agent、rag-integration、web-delivery 三类硬门禁。

## 安全与隐私验收
- 报告不含 question/answer/prompt/knowledge/PII/secret 等字段或原文。
- workflow 不依赖仓库 Secret 即可运行确定性/本地 hash 评测；测试密钥只写 workflow 临时环境。

## 性能验收
- JSON ≤50KB；前端无额外运行时请求。

## 变更预算
- max_files：8
- expected_prod_lines：360
- expected_test_lines：40

## 必须运行的测试命令
- `python scripts/validate_eval_report.py`
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_agent_lab.py tests/aiqa/test_agent_tools.py tests/aiqa/test_aiqa.py -q`
- `cd apps/api && ruff check app tests/aiqa/test_agent_lab.py && mypy app`
- `pnpm test && pnpm typecheck && pnpm build`
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`；无迁移。

## 强制停止条件
- 需要新增依赖/API/DB/权限或超 8 文件时停止拆分；冻结测试失败不得改宽断言。

## 交付证据
- commit / PR：`d8d1fde`
- 修改文件清单：本任务允许的 8 个路径，未修改 API/DB/依赖/权限/Prompt
- 测试命令及结果：报告校验 `61/61 checks, 4 boundary cases, 1966 bytes`；API Agent 回归 `22 passed`；Web shell `1 passed`；production build 1793 modules 成功
- lint / typecheck：`ruff`（app + 报告校验器）通过；`mypy app` 48 files / 0 errors；`pnpm typecheck` 通过；`git diff --check` 通过
- DB 迁移验证：无
- 验收证据：本地 UI 冒烟通过——61/61、三个套件、commit/日期和诚实 CI 状态可见；4 个边界案例可展开；控制台 0 error
- 变更预算实际值：8 文件 / 424 新增行 / 1 删除行，文件数未超预算
- 未解决风险：GitHub remote 未配置，首次远端 run 需仓库推送后产生；本机 Docker Redis 未运行，未在本机复刻 `rag-integration` 容器作业，真实 BGE-M3/pgvector 的既有 38/38 证据仍保留在版本化报告中
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`d8d1fde`

## 关联
- Change Request：`TASK-CR-AIQA-EVAL-CI-001`
- 验收：TC-AI-011
