# TASK-GOV-AIQA-TYPE-AUTH-E2E-001 全量类型门禁与认证真栈复验

> 状态：Closed（2026-08-26，verified_commit=`142d680`）

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.5
- 基线 commit：`12ead54`

## 精确规范引用
- `tasks/TASK-AIQA-AGENT-CRUD-001.md`：既有多轮工具追踪与 `BookingService` 注入。
- `tasks/TASK-M4-APPOINTMENTS.md`：既有 TC-AUTH-REG/VERIFY/RESET 真栈验收。
- `tasks/TASK-HARNESS-001.md`：隔离测试库 `jianli_test` 与 Redis DB 15 约定。

## 需求来源
- 用户要求解决 `TASK-AUTH-EMAIL-DELIVERY-001` 交付时披露的两项风险：全量
  `mypy app` 的 3 个 AIQA 错误，以及真实认证账户生命周期未在本轮复验。

## 目标
- 以显式类型收窄消除 3 个 AIQA mypy 错误，不改变运行行为。
- 使用隔离真实 PostgreSQL/Redis 复跑注册、验证码验证、登录与密码找回生命周期。

## 非目标
- 不改 AIQA Prompt、工具白名单、RBAC、RAG/Agent 分支或 SSE 事件。
- 不改认证邮件交付、验证码生成/存储/TTL、API、数据库、迁移、依赖或前端。
- 不修改、skip 或放宽任何现有测试。

## 允许修改路径
- `tasks/TASK-GOV-AIQA-TYPE-AUTH-E2E-001.md`
- `apps/api/app/aiqa/service.py`（仅工具追踪类型声明）
- `apps/api/app/aiqa/runtime.py`（仅 `TYPE_CHECKING` 类型导入）
- `PROJECT_STATE.md`

## 禁止修改路径
- 上述允许路径之外的所有业务代码、测试、迁移、规范和依赖文件。
- 当前工作区中与本任务无关的既有未提交改动。

## 已批准的 DB / API / 依赖变更
- DB：无；仅使用 harness 隔离测试库执行既有迁移与测试清理。
- API：无。
- 依赖：无。
- 鉴权/加密/Prompt/工具权限：无变化。

## 规范影响评估
- behavior_change：false
- affected_specs：srs/domain_model/openapi/security/test_plan 均为 none。
- reason：仅补充静态类型信息并复跑既有验收，不改变运行路径或用户可观察行为。
- 分类：代码重构（行为未变）。

## 功能、安全与性能验收
- `mypy app` 为 0 error；不得用 ignore 绕过。
- 现有 AIQA DB-free 测试无回归。
- 真实 PG/Redis 认证生命周期测试无 skip、无失败；测试数据仅进入隔离测试库并由 fixture 清理。
- 不输出或记录真实邮箱、验证码、凭据；真栈自动测试继续使用保留域名测试地址与内部令牌查询。
- 无新增运行时开销。

## 变更预算
- max_files：4
- expected_prod_lines：约 12
- expected_test_lines：0

## 必须运行的测试命令
- `cd apps/api && mypy app`
- `cd apps/api && ruff check app/aiqa/service.py app/aiqa/runtime.py`
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa tests/test_app.py -q`
- 在 harness 隔离数据库环境运行 `tests/auth/test_account_lifecycle.py` 与 Auth API 真栈用例，要求 0 skip。
- `git diff --check`（仅本任务文件）。

## 回滚方法
- `git revert` 本任务提交；无迁移或外部状态需要回滚。

## 强制停止条件
- 需要改变运行行为、Prompt/工具权限、API、DB、依赖、鉴权或冻结测试时立即停止。
- 真实栈测试失败时不得修改断言或跳过；先报告根因。
- 超过 4 文件或生产代码 12 行时拆任务。

## 交付证据
- commit / PR：`fd8e611`（首轮类型修复）+ `142d680`（收敛到任务预算内的最终实现）。
- 修改文件清单：本任务单、`PROJECT_STATE.md`、`app/aiqa/service.py`、
  `app/aiqa/runtime.py`，共 4 文件；`service.py` 其他既有未提交改动未纳入提交。
- 测试命令及结果：
  - `PYTHONPATH=. python3 -m pytest tests/aiqa tests/test_app.py -q`
    → 62 passed、23 skipped（均为未提供 AIQA 真栈变量的既有条件测试）、0 failed。
  - Docker 同会话启动 PG/Redis，迁移隔离库 `jianli_auth_001_db` 后运行
    `tests/auth/test_account_lifecycle.py tests/auth/test_auth.py -q`
    → 17 passed、0 skipped、0 failed。
  - 首轮误用 `jianli_test` 时冻结测试按预期拒绝错误库名；未修改断言，改用其规定的
    `jianli_auth_001_db` 后全绿。
- lint / typecheck：`ruff check app/aiqa/service.py app/aiqa/runtime.py` → pass；
  `mypy app` → 46 source files、0 error。
- DB 迁移验证：既有迁移对隔离库 `alembic upgrade head` → `0008` 成功；本任务无迁移，
  不需要 down 验证。
- 验收证据：工具追踪结果显式声明为 `dict[str, Any]`，`BookingService` 注解可解析；
  无 ignore、无测试 skip/放宽、无运行分支变化。任务文件 `git diff --check` 通过。
- 变更预算实际值：4 文件；相对任务基线的最终生产代码净差异为 3 insertions / 2 deletions
  （5 changed lines），测试代码 0 行，未超预算。
- 未解决风险：本任务目标范围内无。测试环境会在终端调用结束后停止 compose 容器，已通过
  同一会话内完成启动、迁移和测试解决；不影响仓库或生产部署。
- 是否偏离 TASK：否。
- 规范影响结论：none。
- spec_sync：clean（无规范、API、DB、依赖、鉴权、Prompt 或工具权限变化）。
- verified_commit：`142d680`。
- 关闭门禁：通过。
