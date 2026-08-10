# TASK-TEST-INFRA-001 Alembic 后日志隔离修复

## 任务类型
- implementation / test infrastructure

## 当前阶段
- 状态：In Progress
- 授权来源：AUTH-001 全套冻结测试发现既有跨测试日志污染；用户已授权主窗口持续执行并自动处理主线阻塞。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.1 / test_plan 0.1（均 approved）
- 基线 commit：`66399a8`

## 精确规范引用
- `AGENTS.md §7` 冻结测试不得绕过
- `apps/api/tests/test_worker.py::test_worker_smoke_logs_one_safe_structured_event`

## 目标
- 修复 Alembic `fileConfig` 禁用既有 `jianli.*` logger 后，应用日志重配置不能恢复 logger 的测试隔离缺陷。

## 非目标
- 不改变日志字段、公开 API、鉴权、数据库、迁移或业务行为。

## 允许修改路径
- `apps/api/app/logging_config.py`
- `tasks/TASK-TEST-INFRA-001.md`

## 禁止修改路径
- 测试断言、migration、AUTH 实现、approved 规格与其他任务文件。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：仅恢复既有应用 logger 的可重复配置语义。

## 功能、安全与性能验收
- migration 测试后 Worker smoke 仍输出唯一一条既定 JSON 日志。
- 不输出环境变量或敏感值；不新增依赖；无性能口径变化。

## 变更预算
- max_files：2
- expected_prod_lines：10
- expected_test_lines：0（复用冻结测试）

## 必须运行的测试命令
- `python -m pytest -q -ra`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy app`

## 回滚方法
- 回退本任务实现提交。

## 强制停止条件
- 需要修改测试断言、日志契约、依赖、数据库、API 或超出预算时停止。

## 交付证据
- commit / PR：`5489b92`（实现与验证快照）
- 修改文件清单：`apps/api/app/logging_config.py`、`tasks/TASK-TEST-INFRA-001.md`
- 测试命令及结果：真实 PostgreSQL/Redis 环境执行 `python -m pytest -q -ra` → 25 passed / 0 failed / 0 skipped（4 条 Alembic 配置弃用 warning）
- lint / typecheck：Ruff check pass；Ruff format check pass；mypy pass；pip check pass
- DB 迁移验证：无迁移
- 验收证据：迁移测试先执行后，`test_worker_smoke_logs_one_safe_structured_event` 仍通过并输出既定单条 JSON 日志。
- 变更预算实际值：2/2 文件；生产代码 +4 行；测试代码 +0 行，未超预算
- 未解决风险：Alembic `path_separator` 存在既有弃用 warning，不影响本任务行为
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`5489b92`
- 状态：Closed
