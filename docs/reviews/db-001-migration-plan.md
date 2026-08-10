# DB-001 迁移内容评审包

## 结论

建议批准“迁移基础设施 + 身份域首批 6 张表”，不把领域模型全部 20 张表塞入一个初始 migration。预约并发、通知 Outbox、对话/知识库具有不同风险和验收方式，应拆成后续独立任务。

本文件是审批输入，不是 migration；用户批准前不生成或执行 DDL。

## 本批对象

1. `users`
2. `auth_sessions`
3. `interviewer_profiles`
4. `owner_contact_configs`
5. `email_verification_tokens`
6. `password_reset_tokens`
7. PostgreSQL enum `user_role`：`interviewer` / `owner_admin`
8. 部分唯一索引 `uq_active_owner_admin`

## 推荐物理决策

| 决策 | 唯一推荐 | 理由 |
|---|---|---|
| 命名 | 未加引号的 `snake_case` 表/列名 | 避免 PostgreSQL quoted identifier 的长期维护成本；领域实体名不要求物理表保留 CamelCase |
| UUID | 由应用生成，migration 不启用 `pgcrypto`/`uuid-ossp` | 不为 UUID 默认值新增未批准扩展；后续应用统一生成 |
| 字符串 | 未规定上限的领域 `string` 落 `text` | 不凭空添加长度限制；邮箱/Token 哈希/设备等业务校验留应用与后续契约 |
| 时间 | 全部使用 `timestamptz` | 与领域模型一致；应用统一传 UTC 时间 |
| 时间默认 | 不设置业务时间 server default | 领域模型没有授权隐式默认；调用方显式赋值，避免时钟语义隐藏 |
| 布尔 | `verified boolean NOT NULL`，无默认值 | 避免 migration 替业务注册流程默选状态 |
| 密文 | `bytea` | 对齐 AES 密文字段，绝不新增明文候选人联系方式 |
| FK 删除 | 默认 `NO ACTION`，不级联 | 软删/留存由领域状态控制；避免物理删除意外扩散 |
| email 唯一 | 原值全局 UNIQUE，不引入 citext/函数索引 | 领域模型只规定全局唯一，大小写归一化属于应用输入策略；不新增扩展或隐含行为 |
| enum | PostgreSQL 原生 `user_role` | role 集合稳定且受数据层约束；downgrade 显式删除 enum |
| owner 约束 | `CREATE UNIQUE INDEX uq_active_owner_admin ON users(role) WHERE role='owner_admin' AND deleted_at IS NULL` | 精确实现领域模型 §6.1；只保证至多一个，“正常运行恰一”由初始化/运行监控保证 |
| FK 普通索引 | 本批只为高频关联列 `auth_sessions.user_id`、两类 token 的 `user_id` 建普通索引 | PostgreSQL 不自动索引 FK；这些表按 user 查询/吊销。1:1 表的 PK/UK 已覆盖，无重复索引 |

## 表级字段清单

### users

`id uuid PK`；`email text NOT NULL UNIQUE`；`password_hash text NOT NULL`；`role user_role NOT NULL`；`verified boolean NOT NULL`；`deletion_requested_at/deleted_at/purge_after timestamptz NULL`。

### auth_sessions

`id uuid PK`；`user_id uuid NOT NULL FK users(id)`；`session_token_hash text NOT NULL`；`device text NULL`；`ip inet NULL`；`expires_at timestamptz NOT NULL`；`revoked_at timestamptz NULL`；普通索引 `ix_auth_sessions_user_id`。

### interviewer_profiles

`user_id uuid PK/FK users(id)`；`display_name text NULL`。角色必须为 interviewer 的跨表不变量不能用普通 CHECK 表达，留后续 service/trigger 方案评审；本迁移不偷偷加 trigger。

### owner_contact_configs

`id uuid PK`；`user_id uuid NOT NULL UNIQUE FK users(id)`；`candidate_phone_ciphertext bytea NULL`；`candidate_feishu_open_id_ciphertext bytea NULL`；`updated_at timestamptz NOT NULL`。其 user 必须为唯一活跃 owner_admin 是跨表运行不变量，由 service 与集成测试保证；本迁移不新增未批准 trigger。

### email_verification_tokens / password_reset_tokens

每表：`id uuid PK`；`user_id uuid NOT NULL FK users(id)`；`token_hash text NOT NULL`；`expires_at timestamptz NOT NULL`；`consumed_at timestamptz NULL`；分别建立 `user_id` 普通索引。

## 依赖提案

- `SQLAlchemy` 2.x：ORM/metadata 与连接层。
- `Alembic`：迁移编排。
- `psycopg` 3：PostgreSQL 驱动。
- 不在本任务安装 `pgvector`：首批表不含 vector 列，知识库迁移再引入并审批扩展。
- Windows 本地与 CI 建议锁定 `psycopg[binary]`；生产镜像是否改用系统 `libpq` 构建必须随基础设施任务单独审批，不能从本地便利性推断生产方案。
- 最终精确版本与全部传递依赖由批准后的隔离解析生成，必须与 `pip freeze` 集合一致；不得手写猜测 lock。

## Alembic 结构提案

- `apps/api/alembic.ini`
- `apps/api/migrations/env.py`
- `apps/api/migrations/script.py.mako`
- `apps/api/migrations/versions/0001_identity_schema.py`
- migration 使用显式 `upgrade()` / `downgrade()`，不依赖 autogenerate 作为验收依据。
- 数据库 URL 仅从环境变量读取，不写入仓库；日志不得输出密码。

## 验证矩阵

| 场景 | 预期 |
|---|---|
| 空库 upgrade → head | 6 表、1 enum、约束和索引全部存在 |
| head downgrade → base | 先子表后 users，最后删除 enum；无残留对象 |
| base 再 upgrade → head | 可重复成功 |
| 合法基线库 upgrade | 数据保留、schema 到 head |
| 重复 email | UNIQUE 拒绝 |
| 两个未删除 owner_admin | `uq_active_owner_admin` 拒绝 |
| 第一个 owner soft-delete 后创建新 owner | 允许 |
| 非法 role | enum 拒绝 |
| 不存在 user 的 session/profile/config/token | FK 拒绝 |
| 密文字段 | schema 仅 `bytea`，无候选人明文字段 |

## 已知边界

- “恰好一个活跃 owner_admin”、profile/config 与 User.role 的跨表关系无法由普通 CHECK 完整表达。本批采用领域模型明确给出的部分唯一索引保证“至多一个”，其余由后续 service 初始化与集成测试保证；不擅自新增 trigger。
- 本地真实 PostgreSQL 测试需要一个可丢弃实例。Docker Compose 属 ADR 已接受的本地交付方式，但创建 compose 配置仍是基础设施变更；建议 DB-001 仅使用用户提供的测试库 URL，或另建最小 `TASK-INFRA-LOCAL-001` 审批可逆容器配置。
- migration downgrade 会删除数据，只允许对一次性测试库执行；任何含真实数据环境都需另行确认。

## 请求批准

请批准或调整以下四项后再执行：

1. 首批范围：迁移基础设施 + 上述 6 张身份域表。
2. 物理决策：snake_case、应用生成 UUID、text、timestamptz、bytea、NO ACTION、原生 user_role enum。
3. 索引范围：领域唯一索引 + 3 类高频 user_id FK 索引，不给 1:1 FK 重复建索引。
4. 依赖与测试：SQLAlchemy/Alembic/psycopg 3；本批不装 pgvector；真实 PostgreSQL 测试库方案在执行前明确。

