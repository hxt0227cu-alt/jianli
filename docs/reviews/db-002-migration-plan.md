# DB-002 预约域核心表迁移评审包

## 结论

建议批准一份独立、可逆的 `0002_booking_schema` migration，只物化预约域五张核心表：`companies`、`company_booking_exceptions`、`appointments`、`appointment_slots`、`availability_overrides`。通知 Outbox、AuditLog、Repository、API、预约事务和生产部署均不进入本迁移。

本文件是数据库迁移的人审输入。用户已于 2026-08-11 明确批准 commit `437f45c` 中的四项方案；实现仅可在本边界内进行，不执行生产数据库变更。

## 规范依据

- approved 领域模型 v1.1.5：§6.5～§6.9、§6.17
- approved 架构 v0.2：§4.0～§4.7（锁顺序与事务边界，仅约束后续实现，不在 migration 中创建函数或 trigger）
- frozen TC：TC-OPS-002、TC-APT-003、TC-APT-007～011
- 前置 migration：`0001_identity_schema`

## 本批对象

1. PostgreSQL enum `appointment_status`：`active` / `cancelled` / `completed`
2. PostgreSQL enum `slot_status`：`available` / `booked` / `owner_locked` / `unavailable`
3. PostgreSQL enum `availability_override_action`：`force_unavailable` / `force_available`
4. `companies`
5. `company_booking_exceptions`
6. `appointments`
7. `appointment_slots`
8. `availability_overrides`

## 推荐物理决策

| 决策 | 唯一推荐 | 说明 |
|---|---|---|
| 命名 | 未加引号 `snake_case` | 延续 DB-001，不引入 quoted identifier |
| UUID | 应用生成，无 server default | 与 DB-001 和领域模型一致 |
| 时间 | `timestamptz`，无业务 server default | 调用方显式赋 UTC 时间；migration 不隐式决定业务时间 |
| 密文 | `bytea` | 公司名与预约详情密文不落明文列 |
| 指纹 | `text` | HMAC-SHA256 结果由应用生成；不在数据库计算 |
| FK 删除 | 默认 `NO ACTION` | 不新增级联删除语义 |
| enum | PostgreSQL 原生 enum | 稳定集合由数据层约束，downgrade 显式删除 |
| 跨表规则 | 不新增 trigger / function | 锁顺序、三格连续、Override 重物化由后续 BOOKING service + 真实并发测试实现 |

## 字段与空值策略

### companies

- `id uuid PK NOT NULL`
- `normalized_name_fingerprint text NOT NULL UNIQUE`
- `raw_name_ciphertext bytea NOT NULL`

### company_booking_exceptions

- `id uuid PK NOT NULL`
- `interviewer_user_id uuid NOT NULL FK users(id)`
- `company_fingerprint text NOT NULL`
- `approved_by uuid NOT NULL`、`revoked_by uuid NULL`：按领域模型保留 actor 标识，不擅自新增未声明 FK
- `reason text NOT NULL`
- `expires_at timestamptz NOT NULL`
- `consumed_at timestamptz NULL`
- `revoked_at timestamptz NULL`
- `created_at timestamptz NOT NULL`

### appointments

- `id uuid PK NOT NULL`
- `user_id uuid NOT NULL FK users(id)`
- `company_id uuid NOT NULL FK companies(id)`
- `dedupe_exception_id uuid NULL FK company_booking_exceptions(id)`
- `start_at/end_at timestamptz NOT NULL`
- `status appointment_status NOT NULL`
- `company_name_ciphertext bytea NOT NULL`
- `company_name_fingerprint text NOT NULL`
- `meeting_platform_ciphertext` / `meeting_number_ciphertext` / `contact_ciphertext` / `notes_ciphertext`：`bytea NULL`，允许预约创建后补会议详情和可选备注
- `version integer NOT NULL`
- `created_at timestamptz NOT NULL`
- `cancelled_at/completed_at/deleted_at/purge_after timestamptz NULL`

### appointment_slots

- `id uuid PK NOT NULL`
- `start_at/end_at timestamptz NOT NULL`
- `status slot_status NOT NULL`
- `appointment_id uuid NULL FK appointments(id)`
- `version integer NOT NULL`

### availability_overrides

- `id uuid PK NOT NULL`
- `start_at/end_at timestamptz NOT NULL`
- `action availability_override_action NOT NULL`
- `reason text NULL`
- `created_by uuid NOT NULL FK users(id)`
- `created_at timestamptz NOT NULL`

以上 NOT NULL/NULL 选择是本评审包需要人工批准的物理裁定；不反写领域模型，不改变用户行为。

## 约束与索引

```sql
UNIQUE companies(normalized_name_fingerprint);

CREATE UNIQUE INDEX uq_active_company
  ON appointments(company_name_fingerprint)
  WHERE status = 'active' AND dedupe_exception_id IS NULL;

CREATE UNIQUE INDEX uq_active_user
  ON appointments(user_id)
  WHERE status = 'active';

CREATE UNIQUE INDEX uq_exception_open
  ON company_booking_exceptions(interviewer_user_id, company_fingerprint)
  WHERE consumed_at IS NULL;

CREATE UNIQUE INDEX uq_appointment_exception
  ON appointments(dedupe_exception_id)
  WHERE dedupe_exception_id IS NOT NULL;

UNIQUE appointment_slots(start_at, end_at);
CHECK appointment_slots.end_at = appointment_slots.start_at + interval '30 minutes';
CHECK availability_overrides.end_at > availability_overrides.start_at;
```

普通索引仅增加确定的高频 FK/锁定路径：

- `ix_appointments_user_id`
- `ix_appointments_company_id`
- `ix_appointment_slots_appointment_id`
- `ix_company_booking_exceptions_interviewer_user_id`
- `ix_availability_overrides_created_by`

不新增 speculative 时间范围索引、排斥约束、trigger、数据库函数或扩展；性能证据不足时不提前设计。

## 创建与降级顺序

upgrade：创建 3 个 enum → `companies` → `company_booking_exceptions` → `appointments` → `appointment_slots` → `availability_overrides` → 普通/部分唯一索引。

downgrade：按依赖逆序删除 `availability_overrides` → `appointment_slots` → `appointments` → `company_booking_exceptions` → `companies` → 3 个 enum。只允许在一次性测试库验证 downgrade；不执行生产 downgrade。

## 验证矩阵

| 场景 | 预期 |
|---|---|
| DB-001 head → upgrade head | 五表、三 enum、列、FK、UK、CHECK、索引全部存在 |
| head → downgrade `0001_identity_schema` → head | 可逆且身份域六表/数据不受影响 |
| 重复 upgrade head | 幂等到同一 revision，不破坏合法数据 |
| 重复 company fingerprint | UNIQUE 拒绝 |
| 第二个 active appointment（同 user） | `uq_active_user` 拒绝 |
| 第二个 normal active appointment（同 company fingerprint） | `uq_active_company` 拒绝；带不同有效例外的行不受该索引约束 |
| 同一 exception 被两个 appointment 引用 | `uq_appointment_exception` 拒绝 |
| 同 interviewer + fingerprint 的第二个未消费 exception | `uq_exception_open` 拒绝；消费后可新建 |
| 重复 Slot 起止 / 非 30 分钟 Slot | UNIQUE / CHECK 拒绝 |
| Override `end_at <= start_at` | CHECK 拒绝 |
| 非法 enum / 缺失 FK | 拒绝 |
| 冻结测试 | TC-OPS-002 真实 PostgreSQL 零 skip；后续 BOOKING 并发 TC 不在 migration 中用 mock 冒充 |

## 批准记录

用户已批准以下四项：

1. 五表 + 三 enum 的本批范围；
2. 上述字段类型与 NULL/NOT NULL 物理裁定；
3. 四个部分唯一索引、两个 UNIQUE 约束、两个 CHECK 约束和五个普通 FK 索引；
4. `0002_booking_schema` 的可逆顺序与一次性真实 PostgreSQL `up → down → up` 测试方案。
