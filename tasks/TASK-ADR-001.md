# TASK-ADR-001 实现技术栈 ADR

## 任务类型
- design

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 review / architecture 0.2 approved
- 基线 commit：`009e3a0`

## 精确规范引用
- architecture §1-§3、§9-§10；security §2-§12；test-plan §1、§4-§5

## 需求来源
- 开发准入门禁；AGENTS.md §2-§4

## 目标
- 给出 MVP 实现语言、框架、关键依赖和工程布局的唯一推荐，供用户接受后约束代码任务。

## 非目标
- 不写业务代码；不安装依赖；不批准安全/接口/测试计划；不购买或创建云资源。

## 允许修改路径
- docs/adr/ADR-IMPL-001.md
- tasks/TASK-ADR-001.md
- PROJECT_STATE.md

## 禁止修改路径
- 上游规范、baseline、代码、迁移、lockfile、外部环境

## 已批准的 DB / API / 依赖变更
- 无。本任务只提出依赖清单，`accepted` 前不得安装或使用。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：实现选型不改变已批准产品行为。

## 验收
- 单体模块化且不引入 deferred 的 LangGraph/MCP/Mem0/微服务/消息队列。
- 支持 OpenAPI/SSE、PostgreSQL/pgvector、Redis 限频、独立 Worker 与冻结测试。
- 列清运行时、开发与系统级依赖；付款/基础设施仍需用户确认。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- `git diff --check`
- 依赖边界 Grep：不得出现 LangGraph/MCP/Mem0/Kafka/RabbitMQ 作为采纳项。

## 回滚方法
- `git revert` 本任务提交。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：ADR 待用户接受；生产入口与云资源待上线前确认
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Review

## 关联
- 下游：开发准入评审、implementation TASK
