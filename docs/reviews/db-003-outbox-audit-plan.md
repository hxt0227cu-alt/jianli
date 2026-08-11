# DB-003 预约创建 Outbox 与审计表迁移评审包

## 结论

建议在 `0002_booking_schema` 之后新增一份独立、可逆的 `0003_outbox_audit_schema` migration，只创建 `notification_events` 与 `audit_logs`。这是实现 BOOKING-001 / TC-APT-002 的最小数据库前置，不包含 `notification_deliveries`、通知 Worker、SSE、Repository、API 或外部调用。

本文件仅供人工审批。用户批准前不得写 migration 或执行数据库变更。

## 规范依据

- approved 领域模型 v1.1.5：§6.11、§6.15
- approved 架构 v0.2：§4.0～§4.1
- frozen TC：TC-APT-001～003，尤其 TC-APT-002
- 前置 migration：`0002_booking_schema`

## 本批对象

1. PostgreSQL enum `notification_event_type`：`appointment_created` / `appointment_details_updated` / `appointment_rescheduled` / `appointment_cancelled` / `reminder_due`
2. PostgreSQL enum `notification_event_status`：`pending` / `processing` / `processed` / `cancelled` / `failed`
3. `notification_events`
4. `audit_logs`

## 推荐物理决策

| 决策 | 唯一推荐 | 说明 |
|---|---|---|
| 命名 | 未加引号 `snake_case` | 延续 `0001` / `0002` |
| UUID | 应用生成，无 server default | 业务事务显式生成，便于幂等与测试 |
| 时间 | `timestamptz`，无业务 server default | 调用方显式写 UTC |
| enum | PostgreSQL 原生 enum | 严格约束 approved 状态集合 |
| 删除策略 | 不新增级联 | Outbox 与审计是业务证据，不随预约隐式删除 |
| NotificationDelivery | 本批不创建 | 预约事务只写事件；投递行由后续异步消费者创建 |

## 字段与空值策略

### notification_events

- `id uuid PK NOT NULL`
- `type notification_event_type NOT NULL`
- `biz_id uuid NOT NULL`：逻辑指向业务对象；按领域模型保留通用 UUID，不添加只适用于预约的 FK
- `scheduled_at timestamptz NULL`：仅 `reminder_due` 使用；不新增跨字段 CHECK 或 trigger
- `idempotency_key text NOT NULL UNIQUE`
- `status notification_event_status NOT NULL`
- `cancelled_at timestamptz NULL`
- `superseded_by_event_id uuid NULL`：按领域模型保留事件关联标识；不自行增加未明确的 self-FK
- `created_at timestamptz NOT NULL`

### audit_logs

- `id uuid PK NOT NULL`
- `actor text NOT NULL`
- `action text NOT NULL`
- `target text NOT NULL`
- `masked_detail text NOT NULL`：只允许脱敏摘要，不存预约明文或密钥
- `created_at timestamptz NOT NULL`

## 约束与索引

```sql
UNIQUE notification_events(idempotency_key);

CREATE INDEX ix_notification_events_biz_id
  ON notification_events(biz_id);

CREATE INDEX ix_notification_events_pending_schedule
  ON notification_events(scheduled_at)
  WHERE type = 'reminder_due' AND status = 'pending';
```

- `idempotency_key` UNIQUE：领域模型 §6.11 明确要求。
- `biz_id` 普通索引：预约改期/取消需按业务对象定位并撤销旧 `reminder_due`。
- `pending_schedule` 部分索引：只服务 approved 的临近提醒扫描；不引入额外字段、函数或扩展。
- 本批不为 `audit_logs` 预建无查询证据的索引；Admin 审计查询进入对应任务时再按批准契约评估。

## 创建与降级顺序

upgrade：创建两个 enum → `notification_events` → `audit_logs` → 两个普通/部分索引。

downgrade：删除 `audit_logs` → 两个 notification event 索引 → `notification_events` → 两个 enum。只允许在一次性测试库验证；不执行生产 downgrade。

## 验证矩阵

| 场景 | 预期 |
|---|---|
| DB-002 head → upgrade head | 两表、两个 enum、字段、UK 与索引全部存在 |
| head → downgrade `0002_booking_schema` → head | 可逆且 DB-001/DB-002 表与合法数据不受影响 |
| 重复 `idempotency_key` | UNIQUE 拒绝 |
| 非法 event type / status | enum 拒绝 |
| `scheduled_at` / `cancelled_at` / `superseded_by_event_id` 为空 | 普通创建事件合法 |
| `masked_detail` 为空或缺失 | NOT NULL 拒绝 |
| migration 静态扫描 | 无 trigger/function/extension/server default/新依赖 |

## BOOKING-001 解锁边界

本迁移批准并通过真实 PostgreSQL `up → down 0002 → up` 后，BOOKING-001 才可建立实现任务，并仅覆盖：

- `previewAppointment`
- `createAppointment`
- TC-APT-001～003
- 预约事务内写 `Appointment`、3 个 `AppointmentSlot`、`appointment_created` + `reminder_due` 两个 `NotificationEvent`、一条脱敏 `AuditLog`

通知消费、`NotificationDelivery`、SMTP/飞书、SSE 推送、改期、取消、Owner override 均继续拆分，不进入 BOOKING-001。

## 待用户批准

请明确批准或调整以下四项：

1. 两表 + 两 enum 的本批范围；
2. 上述字段类型与 NULL/NOT NULL 裁定；
3. 一个 UNIQUE 与两个普通/部分索引；
4. `0003_outbox_audit_schema` 的可逆顺序及一次性真实 PostgreSQL `up → down 0002 → up` 验证。
