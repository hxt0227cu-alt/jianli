# TASK-DB-002 预约域核心表迁移

## 任务类型
- migration

## 当前阶段
- 状态：Awaiting Approval

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
- 待用户批准 `docs/reviews/db-002-migration-plan.md` 后，逐项抄入；批准前本节无 DB 变更授权，不得写 migration。
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
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open

## 关联
- 独立审查：TASK-REVIEW-DB-002
- 后续：TASK-BOOKING-001
