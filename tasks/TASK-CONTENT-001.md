# TASK-CONTENT-001 页面二项目内容基线

## 任务类型
- documentation

## 基线版本与基线 commit
- PRD 2.3.3 / SRS 1.1 / UI 1.0 / architecture 0.2（approved）
- 基线 commit：`1c3d3bb`

## 精确规范引用
- SRS §3.1 / §3.2 / §5.7 / §9
- PRD §1.1-§1.3 / §4.1 / R1-R7 / R22 / R25
- sleep202603-an：README、`.harness/wiki/architecture.md`、service-catalog、Agent evaluation、career evidence（只读）

## 需求来源
- 用户要求页面二先展示 jianli 与 sleep202603-an，并面向 AI 全栈开发工程师（AI Agent 方向）取舍内容。

## 目标
- 产出可直接用于页面二实现的项目叙事、证据、信息层级和推荐追问。

## 非目标
- 不修改 sleep202603-an；不把设计/模拟/本地验证写成生产事实；不写页面代码。

## 允许修改路径
- docs/content/project-showcase.md
- tasks/TASK-CONTENT-001.md
- PROJECT_STATE.md

## 禁止修改路径
- sleep202603-an 全部路径
- 已批准规范、代码、OpenAPI、测试计划

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：页面二既定项目展示内容的数据准备，不改变功能行为。

## 验收
- 两个项目均回答问题、角色、方案、证据、边界、可追问点。
- 所有数字有真实仓库证据；jianli 未实现能力不得写成已实现。
- 文案适合 AI 全栈/Agent 招聘阅读顺序。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 事实来源与措辞边界人工复核；Git 验证 sleep202603-an 无写入。

## 回滚方法
- `git revert` 本任务提交。

## 交付证据
- commit / PR：`a09fa5d`
- 修改文件清单：docs/content/project-showcase.md / tasks/TASK-CONTENT-001.md / PROJECT_STATE.md
- 测试命令及结果：事实来源、证据等级、禁止夸大边界复核 → pass；sleep202603-an 保持原有只读工作树状态
- lint / typecheck：不适用
- DB 迁移验证：无
- 验收证据：docs/content/project-showcase.md §1-§4
- 变更预算实际值：max_files=3，实际 3 文件，未超预算
- 未解决风险：jianli 的实现数字须在开发完成后按源码和测试更新
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`a09fa5d`
- 状态：Closed（2026-08-09）

## 关联
- 下游：页面二前端实现任务
