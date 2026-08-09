# TASK-ARCH-003 架构 v0.2 批准与阶段收口

> 用户于 2026-08-09 明确批准 architecture v0.2，并授权按主线进入安全设计。本任务只承载状态推进与架构阶段收口，不修改架构正文，不代替后续安全设计的人类审批。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.1 / UI 线框 1.0（均 approved）/ architecture 0.2（review）
- 待批准内容快照：`3a18b7f`

## 精确规范引用
- `docs/design/architecture.md` v0.2 §1-§12（评审快照 `3a18b7f`）
- `docs/baseline.yml` artifacts / development_gate

## 需求来源
- 用户明确指令："我批准 architecture v0.2，并授权你按上述顺序开始执行"

## 目标
- 生成 architecture v0.2 单一用途批准锚点，关闭 TASK-ARCH-001 / TASK-ARCH-002，并同步 PROJECT_STATE。

## 非目标
- 不修改 architecture.md 内容。
- 不批准安全设计、OpenAPI、测试计划，不写业务代码。
- 不追修不影响产品行为、实现正确性、数据一致性、安全边界或门禁真实性的历史措辞。

## 允许修改路径
- docs/baseline.yml
- tasks/TASK-ARCH-001.md
- tasks/TASK-ARCH-002.md
- tasks/TASK-ARCH-003.md
- PROJECT_STATE.md

## 禁止修改路径
- docs/design/architecture.md
- 已批准的 PRD / use-cases / SRS / domain-model / ui-wireframe
- 安全设计、OpenAPI、测试计划和任何代码

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：srs/domain_model/openapi/security/test_plan 均为 none
- reason：仅执行用户批准后的状态推进与任务收口。

## 功能、安全、性能验收
- baseline 中 architecture=0.2/approved，其他工件版本与状态不变。
- approval_commit 只修改 baseline 的 architecture 状态。
- TASK-ARCH-001 / TASK-ARCH-002 均保留历史并标记 Closed。
- 不产生运行时、安全或性能行为变化。

## 变更预算
- max_files：5
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 校验 baseline 状态、批准提交文件清单、任务关闭状态与 Git 工作树。

## 回滚方法
- `git revert` 本任务提交链；不重写历史。

## 强制停止条件
- 批准提交夹带 baseline 状态之外的文件；改动架构正文或其他已批准规范；推进安全设计批准或编码。

## 交付证据
- approval_commit：待生成
- verified_commit：待生成
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：不适用
- DB 迁移验证：无
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- 状态：Open

## 关联
- 上游：TASK-ARCH-001 / TASK-ARCH-002
- 下游：安全设计任务
