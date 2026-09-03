# TASK-HARNESS-DB-GUARD-015 测试 fixture 隔离与迁移目标精确守卫

> 状态：In Progress（2026-08-31）。发布门禁复核发现集中 fixture 仅凭库名包含 `test` 即执行迁移，现从合并门禁任务拆出独立收口。

## 任务类型
- test infrastructure / safety bug fix

## 基线与引用
- baseline：PRD 2.3.6 / SRS 1.9 / OpenAPI-SSE 1.0 / test-plan 1.4
- 基线 commit：`0b65de38ee4b840233af9951dbc0dc26f2f2fabf`
- `docs/test/test-plan.md` §1、§2.9；`AGENTS.md` §7、§9

## 目标
- 每个测试前中和 `jianli.*` logger 的进程级 handler/filter/level，测试后恢复已有 logger；测试中新增 logger 也不得污染后续用例。
- `conftest` 的 autouse 自动迁移只允许 `postgresql+psycopg`、loopback、CI/开发 Compose 端口及精确库名 `jianli_test`。
- 显式 `harness_setup_db.py` 只允许 `jianli_test`、`jianli_auth_001_db` 与三套 `jianli_tc_*` 数据库；同名远端、异端口、异协议、近似库名与非 Redis db15 均 fail closed。

## 非目标
- 不修改 migration、业务测试断言、数据库 schema、API、依赖或生产配置。

## 允许修改路径
- `apps/api/tests/conftest.py`
- `apps/api/scripts/harness_setup_db.py`
- `apps/api/tests/scripts/test_harness_safety.py`
- `tasks/TASK-HARNESS-DB-GUARD-015.md`

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；只收紧测试迁移入口。API：无。依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：测试安全缺陷修复，不改变产品行为。

## 验收
- `conftest` 仅接受 loopback `jianli_test` 的 CI 5432 / 本地 55432；其他目标不触发 autouse 迁移或明确非零失败。
- 显式 setup 仅接受五个精确测试库与 Redis db15；远端、异端口、异协议、query/fragment 与近似库名均拒绝。
- 嵌套验证 logger fixture：进入时中和状态，退出时恢复旧 logger，并清理测试中新增 logger。
- `ruff check`、`ruff format --check` 及相关 pytest 通过。

## 变更预算
- max_files：4
- expected_test_lines：≤250
- expected_doc_lines：≤55

## 回滚
- 回退 fixture 与本任务单；不触达任何数据库。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
