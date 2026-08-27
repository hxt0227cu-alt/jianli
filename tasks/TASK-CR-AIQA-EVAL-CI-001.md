# TASK-CR-AIQA-EVAL-CI-001 评测证据板与 CI 门禁变更请求

> **状态：Approved / Closed（2026-08-27，用户已显式全权批准）**

## 任务类型
- documentation
- design

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.8 / UI 1.0.2 / OpenAPI-SSE 0.9 / test-plan 0.7
- 基线 commit：`01a367b`

## 精确规范引用
- `docs/requirements/SRS.md §3.1–§3.2`
- `docs/design/ui-wireframe.md U2`
- `docs/test/test-plan.md §2.2` / TC-AI-011

## 需求来源
- 用户要求唯一可体验作品具备 Agent 开发岗竞争力，并批准“真实评测结果 + CI 门禁 + 失败案例”。

## 目标
批准在 jianli 项目页增加公开、可追溯的评测证据板，并增加 GitHub Actions 自动质量门禁。

## 非目标
- 不新增公开 API、DB、依赖、工具权限或模型 Prompt。
- 不实现 OTel/Prometheus/Grafana、Reranker、K8s、在线 A/B 或模型微调。
- 不伪造实时 CI 状态；没有远端仓库时只展示已验证报告与工作流配置状态。

## 允许修改路径
- `tasks/TASK-CR-AIQA-EVAL-CI-001.md`
- `docs/requirements/SRS.md`
- `docs/design/ui-wireframe.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用代码、测试代码、CI workflow、API 契约、领域模型、安全设计。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无。

## 批准决策
- U2 的 jianli 项目允许展示评测证据板：总体通过数、分套件指标、验证时间/commit、CI 门禁状态及失败/边界案例。
- 展示数据必须来自版本化机器可读报告；指标必须带样本数与来源，不得只展示百分比。
- 失败案例区分 `expected_block`、`known_limitation`、`regression`；不得把预期安全阻断伪装为系统故障。
- GitHub Actions 在 push/PR 运行后端 Agent/安全回归、RAG 集成评测、ruff/mypy、前端 test/typecheck/build；任何硬门禁失败必须返回非零。
- 报告不得包含问题原文、模型完整回答、Prompt、知识原文、PII 或密钥。

## 功能验收
- 规范明确真实数据来源、验证锚点、样本数和失败分类。
- TC-AI-011 冻结评测证据板与 CI 工作流验收。

## 安全与隐私验收
- 公开报告只含聚合指标、无敏感信息的案例标题/分类和复现测试 ID。

## 性能验收
- 前端读取单个静态 JSON，≤50KB；不新增运行时后端调用。

## 变更预算
- max_files：6
- expected_prod_lines：130
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`
- `python -c` 解析 baseline YAML 与报告契约文字一致性（实现任务执行）

## 回滚方法
- `git revert <本任务提交>`。

## 强制停止条件
- 若需要新增 API/DB/依赖、暴露敏感数据或超 6 文件，停止并拆分。

## 交付证据
- commit / PR：`465968c`
- 修改文件清单：本任务允许的 6 个路径
- 测试命令及结果：`git diff --check` 通过；版本锚点与 TC-AI-011 检索一致
- lint / typecheck：文档任务不适用
- DB 迁移验证：无
- 验收证据：SRS 1.9 / UI 1.0.3 / test-plan 0.8 / baseline approved 同步完成
- 变更预算实际值：6 文件，约 116 行，未超预算
- 未解决风险：GitHub 远端尚未配置，workflow 只能本地静态校验，首次 push 后才产生远端 run
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：`465968c`

## 关联
- 上游：`TASK-RAG-EVAL-001`、`TASK-HARNESS-001`、`TASK-AIQA-AGENT-LAB-001`
- 下游：`TASK-AIQA-EVAL-CI-001`
