# TASK-CR-RERANKER-001 Cross-Encoder Reranker 变更请求

> **状态：Approved / Closed（2026-08-27，用户已显式全权批准）**

## 任务类型
- architecture
- security
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.3 / security 0.2 / test-plan 0.9
- 基线 commit：`e90565b`

## 精确规范引用
- `docs/design/architecture.md §8.3`
- `docs/design/security.md §9/§11`
- `docs/test/test-plan.md §2.2`
- `docs/adr/ADR-RERANK-001.md`

## 需求来源
- 用户要求唯一公开作品具备 Agent 开发岗竞争力，并全权批准 Reranker 对照实验主线。

## 目标
- 批准在现有 vector + BM25 + RRF 后增加可关闭的 Cross-Encoder 重排，并形成可复现对照证据。

## 非目标
- 不改变工具权限、Prompt、DB、公开 API、召回阈值或无依据拒答规则。
- 不把 PyTorch/模型权重打进 API 镜像，不新增本地模型服务。

## 允许修改路径
- `tasks/TASK-CR-RERANKER-001.md`
- `tasks/TASK-AIQA-RERANKER-001.md`
- `docs/adr/ADR-RERANK-001.md`
- `docs/design/architecture.md`
- `docs/design/security.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用代码、数据库迁移、OpenAPI、领域模型、Prompt、工具注册。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无公开 API 变化。
- 依赖：无新增依赖；复用已锁定 `httpx==0.28.1` 调用 OpenAI 风格 `/rerank`。
- 外部集成：可选 Cross-Encoder rerank endpoint；默认未配置即保持原 RRF 顺序。

## 批准决策
- 流水线固定为 vector top10 + BM25 top10 → RRF 候选集 → Cross-Encoder top6。
- Reranker 仅接收当前请求问题和已经通过租户/页面域过滤的候选片段，不得扩大召回范围。
- 网络超时、429、5xx、畸形响应均 fail-open 回退原 RRF 顺序；不得把已有 grounded 请求变成服务错误。
- 仅记录 fixed status、候选数、耗时和模型配置名；不得记录问题或片段原文。
- 对照报告必须区分 deterministic protocol test 与真实 provider run，不得伪造质量提升。

## 功能/安全/性能验收
- TC-AI-012：成功重排、失败回退、索引校验、低基数观测与对照报告校验。
- 默认关闭零网络调用；开启后每次 KB 检索最多一次 rerank 请求，超时独立且不超过 5 秒。
- 发送内容严格限于已授权候选，日志/指标不含输入正文。

## 变更预算
- max_files：8
- expected_prod_lines：190
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`。

## 强制停止条件
- 需要 DB/公开 API/新依赖/Prompt 或工具权限变化，或超 8 文件时停止。

## 交付证据
- commit / PR：`5d2f934`
- 修改文件清单：本任务允许的 8 个路径
- 测试命令及结果：`git diff --check` → pass
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：ADR-RERANK-001 accepted；architecture 0.4 / security 0.3 / test-plan 1.0 / baseline approved 同步
- 变更预算实际值：8/8 文件，216 新增、9 删除
- 未解决风险：无
- 是否偏离 TASK：否
- spec_sync：clean
- verified_commit：`5d2f934`
