# TASK-DB-001 数据库迁移基础与身份域首批表

## 任务类型
- migration

## 当前阶段
- 状态：In Progress
- 用户已于 2026-08-11 明确批准 `docs/reviews/db-001-migration-plan.md` 中的首批范围、物理决策、索引范围、依赖与测试方案；开始实现。迁移 SQL 仍只在一次性测试库验证，不执行生产迁移。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / architecture 0.2 / security 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`2c22ac1766dd8477a0b3c54fbcb9b19e9cafe719`

## 精确规范引用
- `docs/design/domain-model.md` §6.1–§6.4
- `docs/adr/ADR-IMPL-001.md` §1 数据层、§2 仓库布局、§5 人工审批边界
- `docs/test/test-plan.md` TC-OPS-002
- `docs/design/security.md`：仅密码哈希存储、敏感字段密文和访问控制相关既有约束

## 需求来源
- 领域模型 §6.1–§6.4 的身份、会话、个人资料、owner 联系配置和令牌实体。
- ADR-IMPL-001 的 SQLAlchemy 2 / Alembic / psycopg 3 / pgvector 数据栈决策。

## 目标
- 建立 Alembic 迁移基础设施，并以一份可逆初始 migration 创建身份域首批 6 张表及其已批准约束。

## 非目标
- 不创建 Appointment、AppointmentSlot、Company、AvailabilityOverride、Notification、Conversation、Knowledge、Audit 或推荐问题相关表。
- 不实现 Repository、ORM 业务模型、API、鉴权、密码哈希、Cookie/CSRF、加密解密、Redis 或业务事务。
- 不启动 PostgreSQL/Redis 容器，不修改云资源或执行生产迁移。
- 不启用 pgvector 扩展；该扩展随知识库迁移单独审批。

## 允许修改路径（用户批准后）
- `apps/api/pyproject.toml`
- `apps/api/requirements.lock`
- `apps/api/alembic.ini`
- `apps/api/migrations/**`
- `apps/api/tests/migrations/**`
- `tasks/TASK-DB-001.md`（交付证据）
- `docs/reviews/db-001-migration-plan.md`（只更新审批结论）
- `PROJECT_STATE.md`（只更新任务态与证据）

## 禁止修改路径
- `apps/api/app/**`、`apps/web/**`
- 已批准 PRD/SRS/domain/security/OpenAPI/test-plan/architecture 正文
- `infra/**`、`.github/**`、生产配置与云资源
- `C:\Users\hxt02\Desktop\sleep202603-an\**`

## 已批准的 DB / API / 依赖变更

> 用户已于 2026-08-11 批准以下范围与决策；仅限本任务，不扩展到后续业务表。

- DB：新增 `user_role` enum；新增 `users`、`auth_sessions`、`interviewer_profiles`、`owner_contact_configs`、`email_verification_tokens`、`password_reset_tokens` 6 张表。
- DB：新增唯一约束 `users.email`、`owner_contact_configs.user_id`；新增部分唯一索引 `uq_active_owner_admin`；新增全部 §6.1–§6.4 FK 与 NOT NULL 约束。
- DB：迁移采用应用生成 UUID、`timestamptz`、`bytea` 密文字段、无级联删除、显式可逆 downgrade；不设置业务字段的隐式 server default。
- API/SSE：无。
- 直接依赖：SQLAlchemy 2、Alembic、psycopg 3（binary extra 仅用于本地/CI 是否采用，见评审包待审批）；pgvector 本任务不安装，留知识库迁移任务。
- 所有直接与传递依赖必须精确锁定，并与实际隔离环境安装集合一致。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：仅把已批准领域模型的身份域部分物化为数据库 schema，不改变用户可观察行为。

## 功能验收
- Alembic 可在空 PostgreSQL 数据库执行 upgrade 到 head、downgrade 到 base、再次 upgrade 到 head。
- 6 张表、枚举、PK/FK/UK/部分唯一索引与领域模型 §6.1–§6.4 一致。
- 在含一个活跃 owner_admin 的基线库重复 upgrade 不破坏数据；创建第二个活跃 owner_admin 被 `uq_active_owner_admin` 拒绝。
- downgrade 按依赖逆序删除表、索引和 enum，不遗留对象。

## 安全与隐私验收
- `password_hash` 只保存哈希字符串；migration 不生成、记录或打印密码。
- `candidate_phone_ciphertext`、`candidate_feishu_open_id_ciphertext` 使用 `bytea`，不新增明文联系方式列。
- migration 日志、测试夹具和错误输出不含真实邮箱、Token、Cookie、密钥或 PII。
- 不改变 security v0.1 的算法、密钥、鉴权或会话策略。

## 性能验收
- TC-OPS-002 为迁移正确性门禁；本批 6 张空表 migration 不新增产品运行时性能承诺。
- 所有 FK 列是否增加普通索引按评审包明确裁定，不由 Alembic 自动猜测。

## 变更预算
- max_files：12
- expected_prod_lines：450
- expected_test_lines：260

## 必须运行的测试命令
- 使用锁文件在全新 Python 3.12 隔离环境安装并执行 `pip check`
- `alembic upgrade head`（空库）
- `alembic downgrade base`（空库升级后的库）
- `alembic upgrade head`（down 后重建）
- `alembic upgrade head`（预置合法基线数据的基线库）
- schema introspection：表、列、类型、nullable、PK/FK/UK/index 与批准清单逐项一致
- 约束测试：重复 email、第二个活跃 owner_admin、非法 role、缺失 FK 均失败
- `python -m pytest apps/api/tests/migrations`
- `python -m ruff check .`、`python -m ruff format --check .`、`python -m mypy app`

## 回滚方法
- 先在一次性测试库验证 `alembic downgrade base`；生产环境实际 downgrade 另行人工审批。
- 本任务仅允许删除由首批 migration 新建且无下游依赖的 6 张表、索引和 enum；存在数据或下游 FK 时立即停止，不强制删除。

## 强制停止条件
- 用户尚未明确批准 `docs/reviews/db-001-migration-plan.md` 中的 DDL 决策与依赖方案。
- 需要新增本任务未列明的表、字段、索引、enum、扩展、依赖或外部服务。
- 领域模型字段/约束不足以无歧义生成 DDL，且评审包未获用户裁定。
- 空库或基线库任一 up/down、约束测试、冻结 TC-OPS-002 失败。
- 超出 `max_files` 或代码行预算。

## 交付证据
- commit / PR：`da8dc7f0e5c0be5ec81a23e114b9dcd6e915a234`
- 修改文件清单：`apps/api/pyproject.toml`、`apps/api/requirements.lock`、`apps/api/alembic.ini`、`apps/api/migrations/env.py`、`apps/api/migrations/script.py.mako`、`apps/api/migrations/versions/0001_identity_schema.py`、`apps/api/tests/migrations/test_identity_schema.py`
- 测试命令及结果：`python -m ruff check .` → pass；`python -m ruff format --check .` → 13 files formatted；`python -m mypy app` → 0 issues；`python -m pytest` → 5 passed / 2 skipped（缺 `JIANLI_TEST_DATABASE_URL`）；`alembic upgrade head --sql` → pass；`pip check` → pass
- lint / typecheck：Ruff check/format 与 mypy 均通过
- DB 迁移验证：**未完成**；本机无 PostgreSQL、Docker 或 `psql`，因此真实 `upgrade head` / `downgrade base` / 再 upgrade 与 TC-OPS-002 约束测试未执行
- 验收证据：offline DDL 生成包含 6 表、`user_role`、`uq_active_owner_admin`、FK/UK/索引；无生产连接或敏感值输出
- 变更预算实际值：7 个实现文件；迁移生产代码 255 行；迁移测试代码 80 行；未超 `12 / 450 / 260`
- 未解决风险：必须在一次性 PostgreSQL 测试库完成 TC-OPS-002；在此之前不得关闭任务、执行生产迁移或开始依赖该 schema 的业务实现
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`da8dc7f0e5c0be5ec81a23e114b9dcd6e915a234`（实现快照，非关闭快照）
- 状态：Open（等待 PostgreSQL 集成验证）
- 关闭结论：未关闭。静态门禁通过，但测试条件①尚未满足；不得以 skipped 测试代替 TC-OPS-002。

## 关联
- 冻结验收：TC-OPS-002
- 后续：预约核心表迁移、通知 Outbox 迁移、对话/知识库迁移分别建 TASK
