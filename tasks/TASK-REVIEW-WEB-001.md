# TASK-REVIEW-WEB-001 前端展示壳独立审查

## 任务类型
- test

## 基线版本与基线 commit
- PRD 2.3.3 / SRS 1.2 / UI 1.0 / security 0.1 / OpenAPI 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`c1fb262`

## 精确规范引用
- TASK-IMPL-WEB-001；UI U1-U12 / A1-A8；test-plan TC-UI-001/002/003/005；security §8-§9

## 目标
- 独立检查 WEB-001 是否越界、是否真实覆盖冻结 TC、是否泄露敏感信息、是否与 UI/SRS 冲突。

## 非目标
- 不修改实现代码；不放宽测试；不审查后端或 sleep202603-an 的内部实现。

## 允许修改路径
- `docs/reviews/web-shell-review.md`
- `tasks/TASK-REVIEW-WEB-001.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/web/**`、配置、依赖 lockfile、后端、迁移、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- 无；审查只读实现与测试结果。

## 验收
- 覆盖越界、新依赖、重复实现、UI/SRS 偏差、异常路径、测试真实覆盖和隐私边界。
- 任何 P0/P1 阻塞都必须在实现任务关闭前修正。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 读取 WEB-001 交付证据；复跑 `pnpm lint`、`pnpm typecheck`、`pnpm test --run`、Playwright 与构建结果。

## 回滚方法
- `git revert` 审查报告提交。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待审查
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open
