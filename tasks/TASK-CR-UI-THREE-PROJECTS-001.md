# TASK-CR-UI-THREE-PROJECTS-001 页面二三项目冻结验收对齐

> 状态：Approved / Implemented（2026-08-31）。用户此前已明确要求页面二展示 Jianli、Sleep、Litchi 三个项目，并要求后两个项目与 Jianli 一样具备三个完整大板块；本轮再次要求修复上线门禁。该人工决策早于本任务存在，现补齐独立规范入口，不与测试实现混在同一提交。

## 任务类型
- Change Request / test specification
## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8 / SRS 1.9 / UI 1.0.3 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
## 精确规范引用
- `docs/requirements/SRS.md` §3.1
- `docs/design/ui-wireframe.md` U2
- `docs/test/test-plan.md` §1、§2.1 / TC-UI-003、§4
- `tasks/TASK-AIQA-PAGE2-SLEEP-LITCHI-017.md`
## 需求来源与批准决策
- 用户明确要求页面二保留 Jianli、Sleep、Litchi 三个项目。
- 用户明确指出三个项目应具有相同的完整度：核心价值主卡、工程/可靠性过程板块、版本化证据板块。
- 用户本轮要求修复上线前测试阻塞，批准将上述既有决定写回冻结验收。
## 目标
- 将过期的 TC-UI-003 从“两项目”校正为“三项目、每项目三大实质板块”的真实浏览器验收。
- 保留桌面尺寸、证据等级和真实 Playwright 依赖，不降低既有门禁。
## 非目标
- 不修改前端实现、产品文案、公开 API、DB、依赖、权限或其他冻结 TC。
- 不把静态 Playwright 宣称为浏览器 + API + DB + Worker 的 L4 全链路。

## 允许修改路径
- `docs/baseline.yml`
- `docs/test/test-plan.md`
- `tasks/TASK-CR-UI-THREE-PROJECTS-001.md`
## 禁止修改路径
- `apps/**`、`tests/**`、CI workflow、需求/SRS/UI 正文、API、迁移和依赖清单。
## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无。
- 依赖：无。
- 测试规范：TC-UI-003 对齐三项目与三板块，证据等级不变。
## 规范影响评估
- behavior_change：test specification alignment
- affected_specs：test_plan 1.2 → 1.3
- reason：产品实现与用户验收早已是三项目，旧冻结文字发生漂移。
## 验收
- baseline 与测试计划版本一致。
- TC 总数仍为 78；只修改 TC-UI-003 一行验收内容。
- `git diff --check` 通过。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：≤8
- expected_doc_lines：≤70

## 回滚
- 回退本任务三个文档路径；不得单独保留与实现不一致的旧 Playwright 断言。

## 交付证据
- commit / PR：待独立规范提交后回填
- 修改文件：`docs/baseline.yml`、`docs/test/test-plan.md`、本任务单
- 测试命令及结果：待回填
- lint / typecheck：文档任务不适用
- DB 迁移验证：无
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：待回填
