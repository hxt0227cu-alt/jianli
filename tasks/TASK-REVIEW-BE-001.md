# TASK-REVIEW-BE-001 FastAPI 后端骨架独立审查

## 任务类型
- test

## 基线版本与基线 commit
- PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / architecture 0.2 / security 0.1 / OpenAPI 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`511b02dd292d0b993bb2257de2109b6447d841cd`

## 精确规范引用
- `tasks/TASK-BE-001.md`
- `docs/adr/ADR-IMPL-001.md` §1、§2、§4、§5
- `docs/api/openapi.yaml`（确认无新增公开 path）
- `docs/test/test-plan.md` TC-OPS-003（确认未虚报完整覆盖）

## 目标
- 独立检查 BE-001 是否越界、是否引入未批准依赖或公开契约、测试是否真实，以及配置和日志边界是否安全。

## 非目标
- 不修改实现代码、不放宽测试、不实现健康检查、数据库、鉴权、加密、通知或业务功能。

## 允许修改路径
- `docs/reviews/backend-scaffold-review.md`
- `tasks/TASK-REVIEW-BE-001.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/api/**`、`apps/web/**`、依赖声明与锁文件、migration、基础设施、已批准规范。

## 已批准的 DB / API / 依赖变更
- 无；审查只读实现、依赖图和测试结果。

## 验收
- 检查允许路径、文件/行数预算、依赖白名单、重复/空壳代码、公开路由、配置泄漏、日志敏感信息和异常路径。
- 复跑 BE-001 的 pytest、Ruff、mypy、API/Worker smoke，并核对锁文件可重复安装。
- 明确 TC-OPS-003 未被本任务完整覆盖，不得把应用 import smoke 冒充部署健康检查。
- 任何 P0/P1 阻塞都必须在 BE-001 关闭前修正。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 按 `tasks/TASK-BE-001.md` 复跑全部命令，并审查完整 diff 与依赖树。

## 回滚方法
- `git revert` 审查报告提交；不涉及实现或外部状态回滚。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open

