# TASK-ARCH-IMPACT-001 architecture v0.2 同步收口

## 任务类型
- documentation

## 基线版本与基线 commit
- architecture 0.2 / approved；SRS 1.2 / approved；domain-model 1.1.5 / approved
- 基线 commit：`ab4b94e`

## 精确规范引用
- architecture 文档头、§11.1、§11.2、§12.1、§12.3、文档尾；SRS §8；docs/baseline.yml artifacts

## 需求来源
- 用户 2026-08-10 architecture impact-sync 指令

## 目标
- 将 architecture v0.2 正文与已批准 SRS v1.2 的状态、based_on、错误码语义同步，并记录 `spec_sync=clean`。

## 非目标
- 不改变事务、SSE、Outbox、部署、数据库结构或公开 API；不批准 security/OpenAPI/test_plan；不写代码。

## 允许修改路径
- docs/design/architecture.md
- tasks/TASK-ARCH-IMPACT-001.md
- PROJECT_STATE.md

## 禁止修改路径
- docs/baseline.yml、SRS、security、OpenAPI、test-plan、领域模型、UI、代码、迁移

## 已批准的 DB / API / 依赖变更
- 无；本任务只做文字同步。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：同步已批准 SRS v1.2 的错误语义，不改变架构行为。

## 验收
- 正文不再把 approved architecture 写成 review/未批准。
- `based_on` 为 SRS v1.2 / domain-model v1.1.5 / UI 1.0。
- `AUTH_EXPIRED`、`RATE_LIMITED`、`OVERRIDE_NOT_FOUND`、`OVERRIDE_RANGE_EMPTY` 与 SRS v1.2 §8 一致。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 旧状态/错误码矛盾文本 Grep；`git diff --check`。

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
- 未解决风险：无；下游 security/OpenAPI/test-plan 仍按各自任务推进
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Review

## 关联
- 上游：TASK-SRS-003
- 下游：TASK-SEC-001 / TASK-API-001 / TASK-TEST-001
