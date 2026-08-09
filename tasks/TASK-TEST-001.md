# TASK-TEST-001 测试计划与冻结验收用例 review 草案

## 任务类型
- test

## 基线版本与基线 commit
- domain-model 1.1.5 / UI 1.0 / architecture 0.2（approved）
- SRS 1.2 / security 0.1 / OpenAPI-SSE 0.1（review）
- 基线 commit：`7916e8a`

## 精确规范引用
- SRS §3-§9；architecture §4-§9；security §2-§12；OpenAPI 全 operationId；SSE §1-§4

## 需求来源
- R1-R26 / UC-01-UC-23

## 目标
- 产出测试策略、冻结验收用例、并发/安全/性能/迁移/部署门禁与证据格式。

## 非目标
- 不实现测试代码；不批准 test_plan；不修改任何上游契约或验收阈值。

## 允许修改路径
- docs/test/test-plan.md
- docs/baseline.yml
- tasks/TASK-TEST-001.md
- PROJECT_STATE.md

## 禁止修改路径
- 上游规范、代码、迁移、CI、外部环境

## 已批准的 DB / API / 依赖变更
- 无。测试实现依赖须在 implementation/test TASK 中列明并在上游获批后执行。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：冻结既有验收，不改变行为或阈值。

## 验收
- 每个 R/UC 与 OpenAPI 关键 operationId 至少有一个 TC。
- 覆盖正常、权限、并发、幂等、恢复、安全、性能、迁移和部署。
- 模拟/本地/staging/production 证据严格分级。

## 变更预算
- max_files：4
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- TC ID 唯一、需求映射完整、阈值未降低、baseline review 状态检查。

## 回滚方法
- `git revert` 本任务提交。

## 交付证据
- commit / PR：`204c2b8`（测试计划 v0.1 review 草案）
- 修改文件清单：`docs/test/test-plan.md`、`docs/baseline.yml`、`tasks/TASK-TEST-001.md`、`PROJECT_STATE.md`
- 测试命令及结果：结构校验 → 69 个 TC 声明全部唯一；R1-R26 缺失 0；33 个 OpenAPI operationId 缺失映射 0；`git diff --check` 通过
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：`docs/test/test-plan.md` §2 冻结用例矩阵、§3 需求与 operationId 映射、§5 开发准入判定
- 变更预算实际值：4/4 文件；生产代码 0 行；测试代码 0 行
- 未解决风险：上游三项 review，实际测试尚未实现
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：dirty
- verified_commit：`204c2b8`
- 状态：Review

## 关联
- 上游：TASK-SRS-003 / TASK-SEC-001 / TASK-API-001
- 下游：实现与独立审查任务
