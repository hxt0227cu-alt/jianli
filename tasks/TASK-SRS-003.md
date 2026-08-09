# TASK-SRS-003 OpenAPI 前错误语义收口

## 任务类型
- documentation

## 基线版本与基线 commit
- SRS 1.1 / architecture 0.2（approved）；security 0.1（review）
- 基线 commit：`40e0b7d`

## 精确规范引用
- SRS §3.3 / §3.9 / §5.6 / §8
- architecture §4.7 / §11.1 / §11.2

## 需求来源
- OpenAPI 前阻塞：AUTH_EXPIRED 语义冲突；架构中两个 Override 拒绝语义尚无 SRS 错误码。

## 目标
- 产出 SRS v1.2 review 草案，统一限频、会话过期与 Override 拒绝错误语义。

## 非目标
- 不改变限频阈值、认证流程、预约行为或权限；不定义 URL/Schema；不批准 SRS。

## 允许修改路径
- docs/requirements/SRS.md
- docs/baseline.yml
- tasks/TASK-SRS-003.md
- PROJECT_STATE.md

## 禁止修改路径
- PRD/use-cases/domain-model/UI/architecture/security、代码、OpenAPI、测试计划

## 已批准的 DB / API / 依赖变更
- DB/依赖：无。API：仅候选错误语义，须 SRS v1.2 获批后才能进入 OpenAPI。

## 规范影响评估
- behavior_change：false
- affected_specs：OpenAPI/test_plan=update（待下游）；其余 none
- reason：修复内部冲突并给既有拒绝行为稳定标识，不改变成功路径和用户能力。

## 验收
- AUTH_EXPIRED 只用于会话过期；所有限频统一 RATE_LIMITED。
- OVERRIDE_NOT_FOUND / OVERRIDE_RANGE_EMPTY 与 architecture §4.7 行为一致。
- SRS 保持 review，旧 v1.1 approved 快照不重写。

## 变更预算
- max_files：4
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 全文错误码引用一致性检查；baseline 状态检查。

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
- 未解决风险：需用户独立批准 SRS v1.2
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：dirty（待批准与 OpenAPI impact review）
- verified_commit：待回填
- 状态：Review

## 关联
- 下游：OpenAPI/SSE 契约
