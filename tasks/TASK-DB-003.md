# TASK-DB-003 预约创建 Outbox 与审计表迁移评审

## 任务类型
- migration / review package

## 当前阶段
- 状态：Waiting for Human Approval
- 说明：仅产出 migration 评审包；数据库迁移必须经用户批准后另行实施。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.2 / test_plan 0.2（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`37430e6`

## 精确规范引用
- `docs/design/domain-model.md` §6.11、§6.15
- `docs/design/architecture.md` §4.0～§4.1
- `docs/requirements/SRS.md` §3.5、§5.1～§5.3、§8
- `docs/test/test-plan.md` TC-APT-001～003
- OpenAPI operationId：`previewAppointment`、`createAppointment`

## 需求来源
- BOOKING-001 的冻结前置条件：TC-APT-002 要求预约事务同时写 Appointment、3 Slot、NotificationEvent、AuditLog。

## 目标
- 产出两张已批准领域实体的最小可逆 migration 评审包，解除 BOOKING-001 的持久化阻塞。

## 非目标
- 不写 migration、Repository、API、预约事务、SSE、NotificationDelivery、Worker、外部通知或生产部署。
- 不修改已批准规范，不执行任何数据库变更。

## 允许修改路径
- `docs/reviews/db-003-outbox-audit-plan.md`
- `tasks/TASK-DB-003.md`
- `PROJECT_STATE.md`（仅任务态与阻塞）

## 禁止修改路径
- `apps/**`、`infra/**`、approved 规范正文
- `sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- 本任务仅为评审包，DB/API/依赖实际变更：无。
- 用户批准评审包前，禁止创建表、enum、索引或 migration。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只把 approved 领域实体整理为待人工批准的物理迁移方案。

## 验收
- 方案只含 `notification_events` 与 `audit_logs`，逐字段对齐领域模型。
- 明确 enum、约束、索引、upgrade/downgrade 顺序、真实 PostgreSQL 验证矩阵。
- 明确不把 NotificationDelivery、通知发送或外部调用并入本批。

## 变更预算
- max_files：3
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 文档一致性检查、`git diff --check`

## 回滚方法
- 回退评审包与任务状态；无数据库变更。

## 强制停止条件
- 需要新增领域模型未声明字段/状态/依赖/API，或用户未批准即要求实施 migration。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：N/A（纯评审包）
- DB 迁移验证：未执行，等待用户批准
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：等待用户批准物理迁移方案
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open

## 关联
- 前置：TASK-DB-002（Closed，verified_commit=`2fd1199`）
- 后续：TASK-BOOKING-001
