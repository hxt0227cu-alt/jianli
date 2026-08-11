# TASK-DB-002 预约域核心表迁移

## 任务类型
- migration

## 当前阶段
- 状态：Closed
- 用户批准：2026-08-11 用户明确批准 `docs/reviews/db-002-migration-plan.md`（commit `437f45c`），授权按评审包实施；仅限一次性测试库，不含生产迁移。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.2 / test_plan 0.2（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`99be39a`

## 精确规范引用
- `docs/design/domain-model.md` §6.5～§6.9、§6.17
- `docs/design/architecture.md` §4.0～§4.7
- `docs/test/test-plan.md` TC-OPS-002、TC-APT-003、TC-APT-007～011
- `docs/reviews/db-002-migration-plan.md`

## 需求来源
- BOOKING-001 的预约域持久化前置条件；R8～R12、R14b、UC-22。

## 目标
- 以一份可逆 migration 创建预约域五张核心表、三组 enum 及 approved 约束，为 BOOKING-001 提供持久化基础。

## 非目标
- 不实现 Repository、API、预约事务、SSE、通知 Outbox、AuditLog、日历生成器或外部服务。
- 不执行生产 migration，不修改身份域既有 schema，不新增 trigger/function/extension。

## 允许修改路径
- `apps/api/migrations/versions/0002_booking_schema.py`
- `apps/api/tests/migrations/test_booking_schema.py`
- `docs/reviews/db-002-migration-plan.md`
- `tasks/TASK-DB-002.md`
- `tasks/TASK-REVIEW-DB-002.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/api/app/**`、`apps/web/**`、`infra/**`
- approved PRD/SRS/domain/architecture/security/OpenAPI/test-plan 正文
- `apps/api/migrations/versions/0001_identity_schema.py`
- `sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB：新增 PostgreSQL enum `appointment_status`、`slot_status`、`availability_override_action`。
- DB：新增 `companies`、`company_booking_exceptions`、`appointments`、`appointment_slots`、`availability_overrides` 五表及评审包列明的字段、NULL/NOT NULL、FK 和 `NO ACTION` 删除策略。
- DB：新增 `uq_active_company`、`uq_active_user`、`uq_exception_open`、`uq_appointment_exception` 四个部分唯一索引；`companies.normalized_name_fingerprint` 与 `appointment_slots(start_at,end_at)` 两个 UNIQUE；Slot 30 分钟与 Override 正向范围两个 CHECK；五个评审包列明的普通 FK 索引。
- DB：新增可逆 `0002_booking_schema`，down revision=`0001_identity_schema`；不新增 trigger/function/extension/server default。
- API/SSE/依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：仅物化 approved 领域模型，不改变用户可观察行为。

## 功能验收
- DB-001 head 上可 `upgrade → downgrade 0001 → upgrade`。
- 五表、三 enum、全部列、FK、UK、CHECK、部分唯一索引与批准清单逐项一致。
- 身份域六表及合法基线数据在 down/up 循环中保持不变。

## 安全与隐私验收
- 公司名和预约详情仅提供 `bytea` 密文列；不新增候选人/公司明文列。
- 测试夹具、migration 日志不包含真实 PII、密钥、Cookie 或 token。

## 性能验收
- 仅创建评审包批准的 FK/锁定路径索引；不添加无证据的范围索引。

## 变更预算
- max_files：6
- expected_prod_lines：260
- expected_test_lines：320

## 必须运行的测试命令
- 一次性真实 PostgreSQL：`alembic upgrade head` → `alembic downgrade 0001_identity_schema` → `alembic upgrade head`
- `python -m pytest tests/migrations -q -ra`，TC-OPS-002 零 skip
- Ruff check/format、mypy、pip check

## 回滚方法
- 仅在一次性测试库执行 `alembic downgrade 0001_identity_schema`；生产 downgrade 另行人工批准。

## 强制停止条件
- 用户尚未批准迁移评审包；需要未列明表/列/索引/enum/trigger/function/extension/依赖；冻结测试失败；超过预算。

## 交付证据
- commit / PR：评审包 `437f45c`；用户批准登记 `5e49d48`；实现 `280ba83`；回归补齐 `2fd1199`
- 修改文件清单：`docs/reviews/db-002-migration-plan.md`、`apps/api/migrations/versions/0002_booking_schema.py`、`apps/api/tests/migrations/test_booking_schema.py`、`tasks/TASK-DB-002.md`、`tasks/TASK-REVIEW-DB-002.md`、`PROJECT_STATE.md`
- 测试命令及结果：真实 PostgreSQL `python -m pytest tests/migrations -q -ra` → 22 passed / 0 skipped；全套 → 38 passed / 1 skipped（仅 AUTH 需要 Redis 的环境门禁，与 DB-002 无关）
- lint / typecheck：Ruff check/format pass；mypy 16 source files / 0 issues；pip check pass
- DB 迁移验证：`upgrade head → downgrade 0001_identity_schema → upgrade head` 通过；最终 revision=`0002_booking_schema`
- 验收证据：五表、三 enum、六 FK、四部分唯一索引、两个 UNIQUE、两个 CHECK、五普通索引逐项通过；身份域数据在 down/up 中保留；独立审查 P0/P1/P2=0
- 变更预算实际值：6/6 文件；生产 166/260 行；结构测试 206/320 行；约束与 enum/FK 测试按独立任务拆分
- 未解决风险：无任务阻塞风险；全套测试的 1 个 AUTH skip 已由 AUTH 最终快照 `b8c7fc5` 在 PostgreSQL+Redis 环境独立验证
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`2fd1199`
- 状态：Closed

## 关联
- 独立审查：TASK-REVIEW-DB-002
- 后续：TASK-BOOKING-001
