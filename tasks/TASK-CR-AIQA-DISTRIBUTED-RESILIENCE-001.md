# TASK-CR-AIQA-DISTRIBUTED-RESILIENCE-001 多副本熔断变更请求

> **状态：Approved / In Progress（2026-08-27，用户要求 push 前解决全部已知问题）**

## 任务类型
- architecture
- security
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / architecture 0.5 / security 0.4 / test-plan 1.1
- 基线 commit：`1a970dd`

## 精确规范引用
- `docs/adr/ADR-RESILIENCE-001.md`
- `docs/design/architecture.md §9.4`
- `docs/design/security.md §9`
- `docs/test/test-plan.md §2.2`

## 目标
- 批准 Redis 共享的 LLM/Reranker 熔断状态，使多 API 副本共享失败计数、open 窗口与原子 half-open 探针。
- Redis 不可用时退回既有进程内熔断，不让韧性组件成为新的单点故障。

## 非目标
- 不 push、不新增 DB/API/依赖/Prompt/工具/权限，不引入独立协调服务。

## 允许修改路径
- `tasks/TASK-CR-AIQA-DISTRIBUTED-RESILIENCE-001.md`
- `tasks/TASK-AIQA-DISTRIBUTED-RESILIENCE-001.md`
- `docs/adr/ADR-RESILIENCE-001.md`
- `docs/design/architecture.md`
- `docs/design/security.md`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`

## 禁止修改路径
- 应用代码、迁移、OpenAPI、领域模型、Prompt、工具注册。

## 已批准的 DB / API / 依赖变更
- DB/API/依赖：无；复用既有 Redis 客户端与 `redis==8.1.0`。
- 内部实现：Redis Lua 原子状态转换；固定低基数 key 仅含组件名，不含用户数据。

## 功能、安全与性能验收
- TC-AI-014：两个独立 breaker 实例共享失败计数；恢复窗口只允许一个跨实例探针；成功/失败转换原子。
- Redis 故障时调用链继续使用本地 breaker；日志、指标、key 不含用户/会话/问题/回答/候选内容。
- 本地执行 GitHub Actions 三作业的等价命令并输出真实结果；不得执行 push。

## 变更预算
- max_files：8
- expected_prod_lines：180
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`

## 回滚方法
- `git revert <本任务提交>`。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- spec_sync：待回填
- verified_commit：待回填
