# 架构设计与 ADR（v0.6）

> **文档状态**：v0.6 · `status = approved`（用户于 2026-08-27 批准 ADR-RESILIENCE-001：多副本共享 Provider 熔断）。
> **依据基线（based_on，引用 `docs/baseline.yml`）**：PRD v2.3.6 / 用例规约 v1.7.4 / 领域模型 **v1.1.8** / SRS **v1.9** / UI 线框 **v1.0.3** / AI 治理 1.0.1。
> **v0.2 修正范围（TASK-ARCH-002）**：SSE 可靠传播（消除双写丢事件窗口）、预约四条流程的事务与统一锁顺序、Outbox Worker 领取/超时/投递语义/幂等、退信回调入口边界、核心 ADR 明确推荐；**2026-08-09 补充三项实现正确性修正**：① `NotificationDelivery` 投递级原子领取（queued→sending，事务内 RETURNING、提交后才调外部）；② Slot 释放统一改为按 `AvailabilityOverride` 与日历规则**重新物化**（不再无条件写 available），含 `AvailabilityOverride` 变更的 Slot 行锁串行化；③ Sweeper 区分 `queued`（未发送）/`sending`（结果未知）两类超时，不同 `last_error` 口径；**2026-08-09（续）两项并发竞态修正**：④ `AvailabilityOverride` 变更事务重写为「先读旧范围、统一锁全部 Slot（含 booked）、锁后复检冲突、无冲突才写」；⑤ 投递 `created_at` 仅表创建时间（非领取时刻）、`Txn D` 仅领剩余租约充足的 `queued` 行、`Txn W` 回执 CAS 写回 + 迟到 Worker 不覆盖回收状态；**2026-08-09（续二）两项 Schema/并发收口**：⑥ §6.4.1 `Txn W` SQL 删除幻列 `version`、`provider_message_id` 写独立列、`channel_metadata` 改 JSONB 合并（bounce 键仍只由 §7 回写），并附逐字段核对表对齐领域模型 v1.1.5 §6.12；⑦ §4.7 补齐同一 override 的并发更新——新增锁层级 **L2.5**（UPDATE/DELETE 先 `SELECT ... FOR UPDATE` 锁自身行取真实 `old_range`，先于 L3）、CREATE/UPDATE 范围须命中现存 Slot 否则拒绝。逐项差异见 §12.3 条目 20–23。
> **范围边界（硬约束）**：本文档定义系统边界、模块划分、部署与调用关系、关键事务边界、SSE 与通知可靠性机制、知识库索引切换、部署运维与 ADR。**不定义** REST URL、请求/响应 Schema、SSE 事件载荷字段、物理表结构（以领域模型 §6 为准）、密码哈希算法（留《安全设计》ADR）、错误码增删（SRS §8 为唯一权威）。
> **留待《安全设计》裁定、本文不得提前假定具体实现的三项**：① 退信（Bounce）接入方式（回调 or 定时拉取）；② 会话存储介质；③ 限频实现机制。本文对这三项只写"与实现无关的边界约束"。
> **模型边界**：本文全部方案仅使用领域模型 v1.1.5 已批准的实体、字段与索引，**未新增任何实体 / 表 / 字段 / 索引 / 外部依赖**（详见 §5.6、§6.10）。

---

## 1. 系统边界与上下文

### 1.1 系统范围
| 边界 | 包含 | 不包含（延后/外部） |
|------|------|---------------------|
| 前端 | 页面1 简历问答页 / 页面2 项目展示页 / 页面3 动态面试表页 / admin 后台 / 登录注册 | 移动端竖屏（<1024px 阻断）、微信助理（deferred） |
| 后端 | 认证、时段/预约、通知 Outbox 消费者、知识库管理、飞书同步、临近提醒调度、退信回执处理 | 混元 Fallback（deferred）、LangGraph/MCP（deferred） |
| 数据 | PostgreSQL（关系数据 + 知识库向量，见 ADR-ARCH-002） | 数据仓库、OLAP |
| 缓存/中间件 | **MVP 的 SSE 路径不使用任何消息中间件**（见 §5）；是否部署 Redis 取决于《安全设计》对会话存储与限频实现的裁定 | 消息队列（Kafka/RabbitMQ 等）不引入 |
| 外部集成 | SMTP（邮件）、飞书开放 API（多维表格 + 提醒）、托管 LLM（DeepSeek） | 微信 WorkBuddy（deferred） |

### 1.2 外部依赖（PRD §8.2，待确认，不阻塞设计）
- 邮箱与 SMTP 账号/授权码、域名/备案；飞书多维表格授权；人格素材与知识库文件；腾讯云资源。

### 1.3 运行环境约束（SRS §2.3）
- 云端部署（腾讯云），本机不搭服务；大模型经托管 LLM API。
- 浏览器：Chrome/Edge/Firefox 最新稳定版；最低视口 1280×720；平板横屏可用；<1024px 阻断提示。
- 时区 UTC+8；时段以 `start_at`/`end_at` 时间戳存储。

---

## 2. 模块划分

| 模块 | 职责 | 对应领域实体 | 进程形态 |
|------|------|--------------|----------|
| Web 前端（静态 + SSE 客户端） | 三大页面 + admin 后台 + 登录注册；SSE 接收状态推送并按 §5.3 算法收敛 | — | 静态资源（CDN/对象存储） |
| API 网关 / BFF | 统一鉴权、限频挂载点、路由 | — | 无状态应用实例（可 1..N 副本） |
| Auth 服务 | 注册/登录/记住我/找回；账号域隔离 | User / AuthSession / EmailVerificationToken / PasswordResetToken | 同 API 进程 |
| Slots/Appointments 服务 | 时段查询、预约创建/改期/取消（§4 原子事务） | AppointmentSlot / Appointment / Company / CompanyBookingException / AvailabilityOverride | 同 API 进程 |
| **SlotStateReader + SSE Hub** | 周期性从**已提交的数据库状态**派生变更集，推送给本实例持有的 SSE 连接；维护连接级序号；**不订阅任何消息中间件、不把中间件消息当事件源** | AppointmentSlot / Appointment（只读） | 同 API 进程（每实例一份） |
| Notifications Outbox 消费者 | 领取 NotificationEvent → 投递 NotificationDelivery（重试/死信/人工重发），见 §6 | NotificationEvent / NotificationDelivery | 独立 Worker（可多实例） |
| Outbox Sweeper | 回收租约超时的非终态投递，见 §6.4 | NotificationDelivery | 定时任务（可与 Worker 同进程） |
| Reminder Scheduler | 扫描 `reminder_due` 事件触发临近提醒 | NotificationEvent(type=reminder_due) | 定时任务 |
| Feishu Sync | 预约变更同步飞书多维表格；同步失败告警 | — | 同 Notifications |
| Knowledge 服务（admin） | 知识库上传/删除/热更新；索引版本原子切换 | KnowledgeDocument / KnowledgeIndexVersion | 同 API 进程 |
| RAG 检索 + 生成 | 切片检索 + L1 人格层生成（调用托管 LLM） | Conversation / Message / RecommendedQuestionCache | 同 API 进程 |
| 退信回执处理 | 接收/拉取 SMTP 服务商退信 → 幂等回写 `channel_metadata`，见 §7 | NotificationDelivery.channel_metadata | 端点或定时任务（接入方式留《安全设计》裁定） |

> 模块边界与领域模型 §2 实体清单一一对应；MVP 采用**单体模块化**（同进程多模块），非微服务（`complex_agent_infra` 为 deferred）。Outbox 消费者/Sweeper/Reminder Scheduler 可独立进程部署以隔离可靠性。

---

## 3. 部署与调用关系

### 3.1 逻辑部署图（文字描述）
```
[浏览器]──HTTPS──▶[API 网关/BFF](无状态 ×N)
                        │
   ┌────────────────────┼──────────────────────┬──────────────────────┐
   ▼                    ▼                      ▼                      ▼
[Auth/Slots/     [SlotStateReader        [Notifications         [Knowledge/RAG]
 Appointments/    + SSE Hub]              Outbox 消费者 +        (admin + 检索生成)
 Knowledge/RAG]        │                   Sweeper/Reminder]            │
   │  读写事务          │ 周期读取已提交状态         │ SKIP LOCKED 领取     │ 检索
   ▼                   ▼                          ▼                      ▼
        ┌──────────────────────────────────────────────────────────────┐
        │  PostgreSQL（关系数据 + 知识库向量：pgvector，见 ADR-ARCH-002）│
        └──────────────────────────────────────────────────────────────┘
                                     ▲
                     ┌───────────────┴────────────────┐
     [SMTP]◀──投递───┤ Notifications                  ├──同步/提醒──▶[飞书 API]
     [SMTP]──退信回执─▶[退信处理 §7]──幂等回写 channel_metadata
[托管 LLM API]◀──生成──[RAG]

[API / AIQA]──OTLP/HTTP──▶[OTel Collector]
     │                         │
     └──/internal/metrics──▶[Prometheus]──▶[Grafana]
```
> **SSE 路径上没有消息中间件**：每个实例独立从 PostgreSQL 派生状态（§5.1），不存在跨实例事件投递环节，也就不存在该环节的丢失/乱序问题。

### 3.2 调用关系要点
- **写路径（预约创建/改期/取消）**：浏览器 → API 网关 → Appointments 服务 → 单 DB 事务（按 §4.0 统一锁顺序加锁 + 业务写 + 同事务写 `NotificationEvent` + 同事务写 `AuditLog`）→ 提交；事务外由 Outbox 消费者异步投递。
- **读路径（面试表）**：浏览器 → API 网关 → Slots 服务返回带资源版本的快照；SSE 由本实例 SlotStateReader 从已提交状态派生并推送（§5）。
- **通知路径**：业务事务 → `NotificationEvent`（Outbox）→ 消费者按通道建 `NotificationDelivery` → SMTP/飞书（§6）。
- **RAG 路径**：问答 → 向量检索 → 托管 LLM 生成（L1 人格层）→ 流式返回；登录用户会话持久化。
- **外部失败解耦**：预约成功事务**不依赖** SMTP/飞书成功（SRS §4.3）；确认函失败 `CONFIRM_MAIL_FAIL` 不回滚预约。
- **事务内禁止外部调用**：任何数据库事务内不得调用 SMTP / 飞书 / LLM / HTTP，以保证预约提交 P95 ≤1.5s（SRS §5.1）且不长时间持有行锁。

---

## 4. 关键事务边界与统一锁顺序

> 所有关键写在单一 PostgreSQL 事务内完成；`NotificationEvent`（Outbox）与 `AuditLog` 与业务写**同事务**（SRS §3.8/§4.3，领域模型 §6.11/§6.15）。隔离级别 **READ COMMITTED** 即可——所有参与判定的行均被显式加锁，不依赖 SERIALIZABLE。

### 4.0 统一锁顺序（全流程唯一，防死锁）

```
L0  Company                   —— 按 normalized_name_fingerprint（仅创建流程 upsert 时）
L1  Appointment               —— 按 id（改期 / 用户取消 / owner 强制取消）
L2  CompanyBookingException   —— 按 id（仅创建流程消费例外时）
L2.5 AvailabilityOverride     —— 按 id（仅 override 变更事务：UPDATE / DELETE 须先锁自身行，§4.7）
L3  AppointmentSlot           —— 把本事务将要触碰的【全部】Slot 合并去重后，
                                 按 (start_at ASC, id ASC) 一次性升序加锁
```

强制规则：

1. **任何事务不得在已持有 L3 之后回头去取 L0/L1/L2**。
2. **改期必须把「旧 3 格 + 新 3 格」合并成一个集合后统一升序加锁**，禁止「先锁新段、再锁旧段」——两个并发改期互为对方的新旧段时必然死锁。
3. **`FOR UPDATE` 语句不得带 `status` 过滤**。过滤发生在加锁之前，会跳过正被并发事务修改的行，并让应用读到陈旧状态。一律写成
   `... WHERE start_at = ANY(:starts_sorted) ORDER BY start_at FOR UPDATE`，**加锁成功之后再校验 `status`**。
   （v0.1 的 `WHERE ... AND status='available' FOR UPDATE` 属此类缺陷，已修正。）
4. PostgreSQL 执行计划中 `LockRows` 节点位于 `Sort` 之上，`ORDER BY ... FOR UPDATE` 即按排序结果依次加锁；若实现改为逐行加锁，必须保持同一升序。
5. **`AvailabilityOverride` 变更事务（§4.7）必须在取 L3 之前先取 L2.5**（`SELECT ... FOR UPDATE` 锁自身 override 行），禁止「先锁 Slot 再回头锁 override 行」——否则两个并发 UPDATE 会各自基于陈旧 `old_range` 计算出不同的 Slot 锁集合，行锁串行化失效。
5. 锁后校验一律以**服务端**为权威，不信任前端传入的格子集合（领域模型 §6.8）。

### 4.1 预约创建（SRS §3.5，领域模型 §6.5/§6.6/§6.8/§6.17）

```
-- 事务前（只读预解析，不加锁）：公司名归一化 → fingerprint；
--   判断是否存在可用一次性例外（consumed_at/revoked_at IS NULL AND expires_at>now()）
BEGIN;                                   -- READ COMMITTED
  -- L0 公司 upsert（唯一约束幂等）
  INSERT INTO Company(normalized_name_fingerprint, raw_name_ciphertext)
    VALUES (:fp, :enc) ON CONFLICT (normalized_name_fingerprint) DO NOTHING;
  SELECT id FROM Company WHERE normalized_name_fingerprint=:fp FOR UPDATE;

  -- L2 例外授权（仅当本次拟消费；同事务行锁 + 校验 + 消费）
  SELECT id FROM CompanyBookingException
   WHERE id=:exc AND interviewer_user_id=:uid AND company_fingerprint=:fp
     AND consumed_at IS NULL AND revoked_at IS NULL AND expires_at > now()
   FOR UPDATE;                           -- 未命中 → 视为无例外，继续受 uq_active_company 拦截

  -- L3 锁 3 格（不带 status 过滤，按 start_at 升序）
  SELECT id, start_at, end_at, status, version FROM AppointmentSlot
   WHERE start_at = ANY(:starts_sorted) ORDER BY start_at FOR UPDATE;

  -- ★ 锁后校验（全部服务端判定，任一不满足 → ROLLBACK）
  --   ① 命中行数 = 3                                        → 否则 SLOT_TAKEN
  --   ② 三格 status 全 = 'available'                         → booked/unavailable → SLOT_TAKEN；owner_locked → OWNER_LOCKED
  --   ③ 同一自然日（UTC+8）
  --   ④ 连续：s2.start_at = s1.end_at 且 s3.start_at = s2.end_at（各 30min）
  --   ⑤ end_at = s1.start_at + 90min；且满足展示窗口与最短提前量（面试日前一自然日 22:00）

  INSERT INTO Appointment(..., dedupe_exception_id)          -- 唯一索引强制：
      VALUES (..., :exc_or_null);                            --   uq_active_user / uq_active_company / uq_appointment_exception
  UPDATE CompanyBookingException SET consumed_at=now() WHERE id=:exc;      -- 仅当消费例外
  UPDATE AppointmentSlot SET status='booked', appointment_id=:aid, version=version+1
   WHERE id = ANY(:slot_ids);
  INSERT INTO NotificationEvent(type='appointment_created', biz_id=:aid,
                                idempotency_key=:k1, status='pending');
  INSERT INTO NotificationEvent(type='reminder_due', biz_id=:aid,
                                scheduled_at = :start_at - interval '10 minutes',
                                idempotency_key=:k2, status='pending');
  INSERT INTO AuditLog(action='appointment.created', masked_detail=...);
COMMIT;
-- 事务后：Outbox 消费者异步生成 NotificationDelivery（双通道提醒 + 飞书同步 + 确认函）
```

- **唯一约束 → 错误码映射**（SRS §8，不新增码）：`uq_active_user` 冲突 → `DUP_ACCOUNT`；`uq_active_company` 冲突 → `DUP_COMPANY`；`uq_appointment_exception` 冲突 → 该例外已被并发预约消费 → 按 `DUP_COMPANY` 返回（**不得静默放行**）。
- **二次确认不预占**（UC-19）：黄格不落库；确认提交才进入本事务；3 分钟超时 `CONFIRM_EXPIRED` 仅作废前端态、无持久化。
- 并发抢占：另一人先提交 → 本事务在锁后校验②失败 → `SLOT_TAKEN`（领域模型 §6.8）。

### 4.2 原子改期（SRS §3.6，领域模型 §6.6/§6.7）

```
BEGIN;
  -- L1 先锁预约本体并校验
  SELECT id, user_id, status, version, start_at FROM Appointment
   WHERE id=:aid FOR UPDATE;
  --   status='active'          → 否则 ROLLBACK（已取消/已完成）
  --   user_id = 当前登录用户    → 否则 PERM_DENIED（SRS §7：仅归属人可改）
  --   version = 客户端携带版本  → 否则乐观锁冲突，要求刷新后重试

  -- L3 旧 3 格 + 新 3 格【合并去重】后按 start_at 升序一次性加锁
  SELECT id, start_at, end_at, status, appointment_id, version FROM AppointmentSlot
   WHERE start_at = ANY(:union_starts_sorted) ORDER BY start_at FOR UPDATE;

  -- ★ 锁后重新校验
  --   旧 3 格：status='booked' AND appointment_id=:aid
  --            → 否则说明已被 owner 强制取消或并发变更 → ROLLBACK（原预约状态以库为准）
  --   新 3 格：命中 3 行；status='available'，或该格当前正被本预约占用（新旧重叠时可复用）；
  --            同日、连续、90min、窗口与提前量校验同 §4.1
  --   任一不满足 → ROLLBACK，原预约保持 active（禁止先释旧格再重选）

  UPDATE AppointmentSlot SET status='booked', appointment_id=:aid, version=version+1
   WHERE id = ANY(:new_ids);                               -- 先占新
  -- 后释旧（排除与新段重叠的格）：释放后按 §4.6 重新物化，不得无条件写 available
  UPDATE AppointmentSlot s SET status = (
      CASE
        WHEN EXISTS (SELECT 1 FROM AvailabilityOverride o
                     WHERE o.action='force_unavailable'
                       AND o.start_at < s.end_at AND o.end_at > s.start_at)
          THEN 'unavailable'
        WHEN EXISTS (SELECT 1 FROM AvailabilityOverride o
                     WHERE o.action='force_available'
                       AND o.start_at < s.end_at AND o.end_at > s.start_at)
          THEN 'available'
        ELSE calendar_auto_status(s.start_at, s.end_at)    -- 日历自动规则（§4.6 / 领域模型 §6.9）
      END),
    appointment_id=NULL, version=version+1
   WHERE id = ANY(:old_ids_except_overlap);
  UPDATE Appointment SET start_at=:n1, end_at=:n1 + interval '90 minutes',
                         version=version+1 WHERE id=:aid;

  -- 提醒随生命周期：先建新提醒，再把旧提醒置 cancelled 并指向新事件
  INSERT INTO NotificationEvent(type='reminder_due', biz_id=:aid,
                                scheduled_at=:n1 - interval '10 minutes',
                                idempotency_key=:k_new, status='pending')  RETURNING id AS :new_ev;
  UPDATE NotificationEvent SET status='cancelled', cancelled_at=now(),
                               superseded_by_event_id=:new_ev
   WHERE biz_id=:aid AND type='reminder_due' AND status='pending' AND id <> :new_ev;
  INSERT INTO NotificationEvent(type='appointment_rescheduled', biz_id=:aid,
                                idempotency_key=:k_rs, status='pending');  -- 含改期重发确认函
  INSERT INTO AuditLog(action='appointment.rescheduled', masked_detail=...);
COMMIT;
```
- 不变量：新段不可用 → 原预约完全不变；≥50 并发重复≥10 次仅一人成功（SRS §3.6 验收）。
- **改会议号 = 原地改字段**，不触碰 Slot，仅锁 L1 + 写 `appointment_details_updated` 事件 + AuditLog。

### 4.3 用户取消（归属人，SRS §3.6）

```
BEGIN;
  -- L1
  SELECT id, user_id, status, version FROM Appointment WHERE id=:aid FOR UPDATE;
  --   status='active'（已 cancelled → 幂等返回成功，不重复写事件）
  --   user_id = 当前登录用户 → 否则 PERM_DENIED
  -- L3 本预约占用的格，按 start_at 升序
  SELECT id, start_at FROM AppointmentSlot
   WHERE appointment_id=:aid ORDER BY start_at FOR UPDATE;

  UPDATE Appointment SET status='cancelled', cancelled_at=now(),
                         purge_after=now() + interval '30 days', version=version+1
   WHERE id=:aid;
  -- 释放：本预约占用的格已在 L3 锁集合内；释放后按 §4.6 重新物化，不得无条件写 available
  UPDATE AppointmentSlot s SET status = (
      CASE
        WHEN EXISTS (SELECT 1 FROM AvailabilityOverride o
                     WHERE o.action='force_unavailable'
                       AND o.start_at < s.end_at AND o.end_at > s.start_at)
          THEN 'unavailable'
        WHEN EXISTS (SELECT 1 FROM AvailabilityOverride o
                     WHERE o.action='force_available'
                       AND o.start_at < s.end_at AND o.end_at > s.start_at)
          THEN 'available'
        ELSE calendar_auto_status(s.start_at, s.end_at)    -- 日历自动规则（§4.6 / 领域模型 §6.9）
      END),
    appointment_id=NULL, version=version+1
   WHERE appointment_id=:aid;
  UPDATE NotificationEvent SET status='cancelled', cancelled_at=now()
   WHERE biz_id=:aid AND type='reminder_due' AND status='pending';   -- 撤销未执行提醒
  INSERT INTO NotificationEvent(type='appointment_cancelled', biz_id=:aid,
                                idempotency_key=:k, status='pending'); -- 取消告知函（必须）
  INSERT INTO AuditLog(action='appointment.cancelled', actor='归属人', masked_detail=...);
COMMIT;
```

### 4.4 owner 强制取消（SRS §3.7，领域模型 §6.7/§6.15）

```
BEGIN;
  -- L1（actor 必须 role='owner_admin'，SRS §7）
  SELECT id, status, version FROM Appointment WHERE id=:aid FOR UPDATE;
  --   status='active'；已 cancelled → 幂等返回成功（SRS §3.7「重复操作幂等」）
  -- L3
  SELECT id, start_at FROM AppointmentSlot
   WHERE appointment_id=:aid ORDER BY start_at FOR UPDATE;

  UPDATE Appointment SET status='cancelled', cancelled_at=now(),
                         purge_after=now() + interval '30 days', version=version+1
   WHERE id=:aid;
  UPDATE AppointmentSlot SET status='owner_locked', appointment_id=NULL, version=version+1
   WHERE appointment_id=:aid;                                  -- 转 owner_locked（红，优先级高于自动规则）
  UPDATE NotificationEvent SET status='cancelled', cancelled_at=now()
   WHERE biz_id=:aid AND type='reminder_due' AND status='pending';
  INSERT INTO NotificationEvent(type='appointment_cancelled', biz_id=:aid,
                                idempotency_key=:k, status='pending');  -- 告知函（主题「（已取消）」）
  INSERT INTO AuditLog(action='appointment.cancelled', actor='owner_admin',
                       masked_detail='取消原因（脱敏）');
COMMIT;
-- 告知函投递失败 CONFIRM_MAIL_FAIL：不回滚释放，可经失败中心手动重发
```
- 后台**不提供直接修改/删除预约入口**；仅「锁定已约时段触发取消」这一受审计操作（SRS §3.7/§7）。

### 4.5 并发竞态判定矩阵

| 并发组合 | 结果 | 保证机制 |
|---|---|---|
| 两人同抢同 3 格创建 | 仅一人成功，另一人 `SLOT_TAKEN` | L3 行锁 + 锁后 status 校验 |
| 同一面试官并发创建两个预约 | 仅一个成功，另一个 `DUP_ACCOUNT` | `uq_active_user`（例外绝不绕过） |
| 两个预约并发消费同一例外 | 仅一个成功，另一个按 `DUP_COMPANY` 拒绝 | L2 `FOR UPDATE` + `uq_appointment_exception` |
| 改期 vs owner 强制取消（同一预约） | 串行化：先到者胜；后到者在锁后校验发现 `status≠active` 或旧格 `appointment_id≠aid` → 回滚 | L1 先锁 Appointment |
| 用户取消 vs 改期（同一预约） | 同上，L1 串行化 | L1 先锁 Appointment |
| 两个改期互为对方新/旧段 | 不死锁 | §4.0 规则 2：新旧合并后统一升序加锁 |
| 创建 vs 改期抢同一空格 | 先到者占用，后到者锁后校验失败 → `SLOT_TAKEN` | 二者对 Slot 的加锁顺序一致（升序） |
| **两事务并发 UPDATE / DELETE 同一 override** | 串行化：后到者等前者提交后**重读真实 `old_range`** 重算 `affected_range`；行已被删则 `OVERRIDE_NOT_FOUND` 回滚 | §4.7 步骤 1：L2.5 `SELECT ... FOR UPDATE` 锁自身行，**先于** L3 |
| **override 变更 vs 改期 / 取消（同一时段）** | 串行化：二者都须锁该时段全部 Slot（含 `booked`），最终 `status` 由最后提交者按 §4.6 物化 | §4.7 步骤 4：L3 锁范围内全部 Slot |
| 创建 / 修改范围不命中任何 Slot 的 override | 拒绝 `OVERRIDE_RANGE_EMPTY` | §4.7 步骤 3：无锁定载体的 override 会使冲突复检失去串行化基础 |

---

### 4.6 Slot 释放 / 覆盖后的状态重新物化（rematerialize）

无论是改期释放旧格（§4.2）、用户取消释放格（§4.3），还是 `AvailabilityOverride` 的创建 / 修改 / 删除（§4.7），**释放 / 解除锁定后都不得无条件写 `available`**——`AppointmentSlot.status` 只是供网格查询的**物化状态**，owner 人工意图（`AvailabilityOverride`，领域模型 §6.9）与日历自动规则才是真相源。释放后必须按以下优先级**重新物化**该格的 `status`：

1. **生效 `force_unavailable`**（存在覆盖该格时间范围、当前存在的 `AvailabilityOverride(action='force_unavailable')`）→ 物化为 `unavailable`；
2. **生效 `force_available`**（存在覆盖该格的 `AvailabilityOverride(action='force_available')`）→ 物化为 `available`；
3. **无人工覆盖** → 按**日历自动规则**（周末 / 节假日 / 用餐系统规则，领域模型 §6.9 的自动规则）重新计算：受规则约束的格 → `unavailable`，其余 → `available`。

> `calendar_auto_status(start_at, end_at)` 为本草案的**应用层纯函数示意**（非新增数据库对象）：输入时段起止，按领域模型 §6.9 的日历自动规则返回 `available` / `unavailable`；具体节假日清单与用餐窗口属配置数据，沿用既有模型、不新增实体 / 字段。
> `owner` 强制取消（§4.4）**不属于「释放」**——它主动锁定，写 `owner_locked`（红，优先级高于自动规则与 `force_available`），**不进入上述重新物化**。
> 重新物化在**持有该 Slot 行锁的事务内**完成（见 §4.0 统一锁顺序：相关 Slot 已在本事务 L3 锁集合内），与原本的释放 / 写回同事务提交，保证原子性。
> 创建 `AvailabilityOverride` 时已校验「不与另一冲突 override 同时覆盖同一时段」（领域模型 §6.9），故重新物化时同一格至多被一个 `force_*` override 覆盖，无需处理 override 间冲突。

### 4.7 AvailabilityOverride 变更事务（创建 / 修改 / 删除，统一冲突串行化）

owner_admin 维护 `AvailabilityOverride`（领域模型 §6.9）时，其事务须遵循 §4.0 锁顺序（本场景不触及 Company / Appointment，实际从 **L2.5** 起锁）。**与 v0.2 早前版本「先写 Override、再只锁未占用 Slot」不同，本流程改为「锁自身 override 行取真实旧范围（L2.5）→ 算 affected_range → 校验范围命中 Slot → 统一锁范围内【全部】Slot 含 booked（L3）→ 锁后复检冲突 → 无冲突才写 Override → 仅物化未占用 Slot」**，以同时消除两类竞态：① 「override 已提交、但并发事务仍按旧 override 集合物化 Slot」；② 「**同一 override 被两个事务并发 UPDATE/DELETE**，各自基于陈旧旧范围算出不同 Slot 锁集合而互不串行化」：

1. **L2.5：先锁 `AvailabilityOverride` 自身行，取得当前真实旧范围**（**必须早于任何 Slot 锁**）：
   - **创建**：无既有行可锁，跳过本步（新行的行锁在第 5 步 `INSERT` 时自然获得）；
   - **修改 / 删除**：
     ```sql
     -- L2.5：锁自身 override 行，读取【当前真实】旧范围
     SELECT id, start_at, end_at, action
       FROM AvailabilityOverride
      WHERE id = :self_id
        FOR UPDATE;              -- ★ 早于 L3 Slot 锁
     ```
     - **命中 0 行** → 该 override 已被并发事务删除 → **ROLLBACK**，返回冲突（`OVERRIDE_NOT_FOUND`）；
     - **命中** → 以本次锁后读到的 `[start_at, end_at)` 作 `old_range`。**禁止**使用请求体携带的旧范围或事务外预读值——两个并发 UPDATE 若各自基于陈旧 `old_range` 计算 `affected_range`，会锁到不同的 Slot 集合，行锁无法串行化它们，最终物化结果与 override 真相源撕裂。
2. **计算影响范围 `affected_range`**：
   - **创建**：`affected_range = new_range`（本次 `INSERT` 的 `[start_at, end_at)`）；
   - **修改**：`affected_range = old_range ∪ new_range`（`old_range` 取自第 1 步**锁后读到的真实值**）；
   - **删除**：`affected_range = old_range`（同上）。
   - 并集若不连续（新旧范围不相交）按**两段区间**处理；两段命中的 Slot 合并去重后，仍按统一 `(start_at ASC, id ASC)` **一次性**升序加锁，不得分两次加锁。
3. **范围对齐与命中校验（仅 CREATE / UPDATE，强制）**：`[start_at, end_at)` 必须对齐现存 `AppointmentSlot` 的时段边界，且 `affected_range` 至少命中 1 个现存 Slot：
   ```sql
   SELECT count(*) FROM AppointmentSlot
    WHERE start_at < :end_at AND end_at > :start_at;   -- 半开区间重叠
   ```
   **命中 0 个 → ROLLBACK，拒绝本次变更（`OVERRIDE_RANGE_EMPTY`），不得创建无锁定载体的 override。** 理由：本流程的并发正确性**完全依赖 Slot 行锁**做串行化；若某 override 的范围不命中任何 Slot，两个并发事务都锁不到任何行，第 4 步的冲突复检退化为可同时通过，能在同一时段并存两个相互冲突的 `force_*` override，直接违反领域模型 §6.9 的冲突约束。
   > **DELETE 不适用本校验**——允许清理历史上因日历变动而失配的 override；但删除仍须完成第 1 步（锁自身行）与第 4 步（锁命中的 Slot，可能为空集）。
4. **按统一顺序锁 `affected_range` 内【全部】`AppointmentSlot`**：把命中的 Slot 合并进 L3 锁集合，**按 `(start_at ASC, id ASC)` 一次性升序 `FOR UPDATE`**（不带 `status` 过滤，§4.0 规则 3），且**包含 `booked` 格**——`booked` 格在此处**不物化、保持 `booked`**，但必须参与范围锁，使任何并发改期 / 取消 / 另一 override 变更被行锁串行化。
5. **锁后复检冲突 `AvailabilityOverride`**：在**已持有 L2.5 + L3 锁**的前提下，扫描与 `affected_range` 重叠、且**当前存在**的其他 `AvailabilityOverride`；**修改 / 删除时须排除自身 `id`**（`WHERE id <> :self_id`），避免把本次变更当成冲突。存在与本次意图冲突（同范围 `force_*` 覆盖）的其他 override → **ROLLBACK**，拒绝本次变更（领域模型 §6.9 的冲突约束在事务内以已加锁数据为准复核，不信任前端传入）。
6. **无冲突才执行写 Override**：`INSERT` 创建 / `UPDATE` 修改 / `DELETE` 删除（删除即物理删除，模型无软删列）。
7. **仅对 `appointment_id IS NULL` 的 Slot 重新物化**：对锁集合内 `appointment_id IS NULL` 的格调用 §4.6 重新物化 `status` 并**同事务写回**；`booked` 格（及其 `appointment_id` 指向的预约）**不动**，其状态在预约释放时由 §4.2 / §4.3 的重新物化决定。
8. 提交；SSE 由 §5 的提交派生机制自然推送新状态（仅 `appointment_id IS NULL` 的格可见变化）。

> **并发最终状态由「override 行锁 + Slot 行锁」双层串行化**：
> - **同一 override 的并发变更**由 L2.5 行锁串行化：后到者必须等前者提交，然后**重新读到已更新的真实 `old_range`**（或读到 0 行而回滚），因此不可能出现两个 UPDATE 各自按不同旧范围锁到不相交 Slot 集合、彼此看不见的情形；
> - **不同 override / 改期 / 取消之间**由 L3 Slot 行锁串行化：本流程在写 Override **之前**已对 `affected_range` 内全部 Slot（含 `booked`）持 `FOR UPDATE`，且冲突复检在持锁后基于已锁数据完成，故**不存在「override 已生效但 Slot 仍显示旧状态」或「两个并发 override 各自读 stale 后都提交」的竞态窗口**；
> - 第 3 步的「范围必须命中 Slot」是上述第二层串行化成立的**前提条件**——无载体的 override 没有可锁的行，故在创建/修改时直接拒绝。
>
> 被预约占用的 `booked` 格不在此处变更，但因其已被锁定，任何依赖该格的并发写都会被串行化，不会与本次 override 产生状态撕裂。**本节的 L2.5 顺序、范围命中校验与锁后复检须由《测试计划》覆盖**：用例须模拟「两事务并发 UPDATE 同一 override 至不同新范围」→ 断言串行化、后到者基于新真实 `old_range` 重算范围；以及「创建不命中任何 Slot 的 override」→ 断言 `OVERRIDE_RANGE_EMPTY` 拒绝。

## 5. SSE 实时传播、一致性与恢复

> 对应 SRS §4.3（事件带版本/序列号、按序应用、断线重拉全量快照、丢失事件经全量刷新恢复、多实例一致与有序恢复、≤2s 到达）与 §5.4（降级）。SRS 明确「具体机制由架构 ADR 决定」。

### 5.1 传播模型：提交派生（commit-derived），不依赖消息中间件的可靠性

**v0.1 缺陷（如实登记，已修正）**：
1. v0.1 称「发布到 Redis Pub/Sub …保证多实例下事件一致、有序到达」。**这是错误的**：Redis Pub/Sub 是 fire-and-forget、至多一次投递，不持久化、不重放、不保证跨频道有序；订阅者断开或消费慢导致缓冲区溢出时消息**永久丢失**且发布方无感知。它**不提供**可靠性、有序性或可恢复性。
2. v0.1「提交写事务后发布事件」构成 **DB commit 与 Redis publish 的双写**：进程在 commit 之后、publish 之前崩溃 → 该事件永久消失，且**没有任何组件能察觉**（无重放源、无水位、无对账）。

**v0.2 模型（ADR-ARCH-003 推荐方案）**：

- **唯一事件来源 = 已提交的 PostgreSQL 状态**。每个 API 实例内置 `SlotStateReader`，以固定周期 **T = 1s**（可配）在 READ COMMITTED 下读取「当前展示窗口」的
  `AppointmentSlot(id, start_at, status, appointment_id, version)`（本周 + 下周共 14 天 × 25 行 ≈ **350 行**，SRS §3.4 网格规则），与该实例内存中的上一轮基线比对，得到变更集，推送给本实例持有的 SSE 连接。
- 因为事件由**已提交状态派生**，不存在「事务已提交但事件没发出去」的窗口：进程崩溃后，新实例或下一轮读取仍会看到该状态并推送。最坏影响是**延迟 ≤ T**，而不是**永久丢失**。
- **MVP 的 SSE 路径不使用 Redis Pub/Sub 或任何消息中间件**。若后续为压低延迟引入「唤醒提示（wake hint）」，其语义严格限定为「提示实例提前执行一次读取」：**不携带业务载荷、不作为事件来源、丢失只影响延迟不影响正确性**。架构层**禁止**把中间件消息当作真相源。

### 5.2 每个事件携带的单调标识

| 标识 | 来源 | 单调性 | 用途 |
|------|------|--------|------|
| `resource_version` | 既有列 `AppointmentSlot.version` / `Appointment.version`（领域模型 §6.6/§6.7 乐观锁，每次写 +1） | **按资源单调递增** | 客户端「仅应用更高版本」；判定版本跳跃 |
| `stream_seq` | SSE Hub 为**每条连接**分配的连续整数（写入 SSE `id:` 字段） | **按连接连续 +1** | 客户端检测漏序 |
| 快照内各资源自带的 `version` | 快照读返回 | 同第一行 | 快照与增量对齐的**水位** |

- `stream_seq` 是**连接级内存态**，不跨重连、不需持久化 → 不新增任何表或列。
- 事件为**自包含全量**（携带该资源变更后的完整可见状态），不是增量补丁 → 重复投递或乱序不会污染状态，「高版本覆盖低版本」即收敛。

### 5.3 先订阅、再拉带水位的快照（消除快照与增量的竞态）

```
C1  客户端 open SSE          → 服务端立即回 stream_seq=0 的 ready 帧（不含业务数据）
C2  客户端【开始缓冲】收到的所有事件，暂不应用
C3  客户端拉快照（网格 + 本人预约）→ 每个资源附带其 version 作为水位
C4  客户端应用快照 → 建立本地 version map
C5  客户端重放缓冲区：仅当 event.resource_version > local[resource].version 才应用，否则丢弃
C6  进入稳态：同样按「高版本覆盖低版本」应用
```

- **竞态为何被消除**：C2 先于 C3，保证「拉快照期间发生的任何变更」一定落在缓冲区里，不会掉进「快照已读、订阅未建」的缝隙；快照与事件对同一资源携带**同一个 `version` 域**，可直接比较，**因此不需要额外的全局水位或新增序列表**。
- 等价实现（允许）：由 SSE 流本身作为第 1 个事件下发快照（snapshot-on-stream），此时快照与增量天然处于同一有序流内，强度等价或更强。两种实现的具体载荷字段留《接口契约》。

### 5.4 强制重拉快照的触发条件

出现以下任一情形，客户端**丢弃本地状态、从 C1 重走全流程**（SRS §8 `SSE_RECONNECT`，SRS §4.3「断线后重新拉取全量快照恢复」）：

1. SSE 连接断开 / 超时 / 服务端重启；
2. `stream_seq` 不连续（漏序）；
3. 事件的 `resource_version` 相对本地发生**跳跃**（> local + 1），或本地无该资源记录且事件非首版本；
4. 超过 `2×T + 心跳周期` 未收到任何数据帧（服务端定期发 `:keepalive` 注释帧保活）；
5. 服务端下发 `resync` 指令（部署切换、展示窗口滚动、实例基线重建时）。

另设**周期性静默对账**：客户端每 5 分钟重拉一次快照并按版本比较自愈，用于覆盖「最后一个事件丢失且此后长期无变更」这一静默不一致场景。

### 5.5 多实例一致性

- 各实例**各自独立**从同一个 PostgreSQL 派生状态 → 实例之间**没有事件传递环节**，也就不存在「实例 A 收到、实例 B 没收到」的分叉。实例间最大偏差 = 一个轮询周期 T。
- **不需要粘性会话**：客户端可以从实例 A 拉快照、从实例 B 收流，因为对齐依据是**资源版本**而非实例本地序号。
- 延迟预算：T = 1s + 推送与网络 ≪ SRS §5.1 的 ≤2s。

### 5.6 适用边界与升级触发（如实登记，不隐藏）

- 本方案是**窗口全量比对**，成立前提是展示窗口行数小（≈350 行 / 实例 / 秒）。领域模型 v1.1.5 的 `AppointmentSlot` **没有 `updated_at` 列**，因此无法做「按时间戳增量拉取」——这是选择全量比对的直接原因，不是疏忽。
- **升级触发条件**：窗口行数 > 5,000，或应用实例数 > 4，或轮询占 DB 负载 > 20%，或 T 需压到 < 200ms。
- 届时的候选方案（**均需扩模型或新增依赖，故本轮不采纳**）：新增持久化事件日志表（全局 `bigserial` 序列）、为 `AppointmentSlot` 增 `updated_at` 列做增量拉取、PostgreSQL 逻辑复制 CDC（需 `wal_level=logical` + 复制槽，且未消费的复制槽会撑爆 WAL）。**采纳前必须先走 Change Request 修改领域模型并重新批准，不得在实现阶段自行引入。**
- **本轮结论：未新增任何领域实体 / 表 / 字段 / 索引 / 外部依赖 → 未触发 Stop & Report。**

### 5.7 连接约束与降级
- 同账号 SSE 并发 ≤2（SRS §5.6）；断线重连指数退避。
- SSE 不可用 → 轮询降级（SRS §5.4 / UC-07 4a）；降级路径与 §5.3 的收敛规则相同（周期性拉快照 + 按版本收敛），行为一致，无需第二套逻辑。

---

## 6. 通知可靠性：Outbox 消费、投递语义与状态转换

### 6.1 投递语义：**至少一次（at-least-once）**
- 外部发送（SMTP / 飞书）与本地状态提交**无法原子**，「已发出但状态未提交」的窗口在任何无分布式事务的架构中都必然存在。因此本系统**明确承诺至少一次，不承诺 exactly-once**。
- 重复由 §6.5 的**稳定幂等键**在服务商侧或接收端消解；残留风险如实登记于 §6.5，须由《测试计划》覆盖。
- SRS §4.3 要求的是「不重复产生**业务后果**」——业务后果（预约状态、Slot 状态、AuditLog）全部在 §4 的业务事务内一次性完成，通知重投**不会**二次改变业务状态。

### 6.2 Outbox 写入（与业务同事务）
- 业务事件在业务事务内写入 `NotificationEvent`（带唯一 `idempotency_key`），见 §4.1–§4.4。事务提交 = 事件必然存在；事务回滚 = 事件必然不存在。**不存在业务与事件的双写窗口。**

### 6.3 多 Worker 原子领取（claim）

```
-- Txn C：短事务，内部不得有任何外部调用
UPDATE NotificationEvent SET status='processing'
 WHERE id IN (
   SELECT id FROM NotificationEvent
    WHERE status='pending'
      AND (scheduled_at IS NULL OR scheduled_at <= now())    -- reminder_due 到点才领
    ORDER BY created_at, id
    FOR UPDATE SKIP LOCKED
    LIMIT :batch)
 RETURNING id, type, biz_id, idempotency_key;

-- 同一事务内为每个目标通道插入本次尝试记录（既是工作单元，也是互斥凭据）
INSERT INTO NotificationDelivery(event_id, delivery_purpose, channel, event_version, attempt_no, status)
     VALUES (:eid, :purpose, :ch, 1, 1, 'queued');  -- :purpose 由「事件类型→投递目的」映射（领域模型 §6.12）确定；受 uq_delivery_attempt 保护
COMMIT;
```

**双重互斥（仅作用于「建行」，不作用于「发送」）**：
1. `FOR UPDATE SKIP LOCKED` 保证并发 Worker 不会领取同一事件（跳过已被锁定的行，不阻塞）；
2. `uq_delivery_attempt(event_id, delivery_purpose, channel, event_version, attempt_no)`（领域模型 §6.12 调整后的索引）**只负责防止重复建行**——保证即使第一层失效（例如 Sweeper 与 Worker 并发、或事件被重复领取），也**不可能**产生第二条相同 `(event_id, delivery_purpose, channel, event_version, attempt_no)` 的尝试记录，唯一冲突的一方直接放弃。不同 `delivery_purpose` 可并存多行，各自独立记录尝试 / 状态 / 退信 / 重试 / 手动重发。
3. **`uq_delivery_attempt` 不防止「同一行被发送两次」**：该索引约束的是「重复建行」，不是「重复发送」。进程在 `queued → sending` 之后、提交 `sending → succeeded` 之前崩溃，该行仍停留在 `sending`，Sweeper 按 §6.4「结果未知」回收后**必然可能重复发送**。`uq_delivery_attempt` 对这类重复发送**无任何约束力**——重复发送由 §6.5 稳定幂等键 + 服务商幂等尽力去重，如实登记为至少一次语义的残留风险（§6.1）。真正把「同一事件只发一次」的语义边界划在「行级互斥防建行、幂等键防重复送达」两层，而非误以为唯一索引能防重复发送。

### 6.3.1 投递目的（delivery_purpose）与收件人解析

- **目的由事件类型决定**（映射见领域模型 §6.12，本草案不重复罗列）：同一 `appointment_cancelled` 事件须**同时**产生① 候选人 `candidate_notification`（`email` + `feishu` 两行）与② 面试官 `interviewer_cancellation`（`email` 一行）；三者各自独立 `INSERT` 一条 `NotificationDelivery`，互不影响重试/退信/重发。
- **单活跃 owner 收件人解析（candidate_notification）**：`candidate_notification` 的收件人须解析为**唯一活跃 owner_admin**——由 `User` 上的部分唯一索引 `uq_active_owner_admin`（`WHERE role='owner_admin' AND deleted_at IS NULL`，领域模型 §6.1）保证至多一个未删除的 owner_admin。解析链路固定为：`活跃 owner_admin User` → 其 `User.email`（邮箱）→ 同一 `user_id` 的 `OwnerContactConfig` → `candidate_phone_ciphertext`（手机）/ `candidate_feishu_open_id_ciphertext`（飞书）。**不存在活跃 owner_admin 时**，该解析**必须失败并触发运维告警**，**不得**任意挑选某 `User` 顶替（运行不变量见领域模型 §6.1）。
- **飞书接收标识缺失（candidate_notification 的 `feishu` 通道）**：当 `OwnerContactConfig.candidate_feishu_open_id_ciphertext` 为 NULL（未配置飞书接收标识）时，`feishu` 通道投递**直接置 `failed` 并触发告警**；但**不影响**同事件的 `email` 通道——`email` 通道（`User.email` 始终存在）照常投递。两通道独立重试、不相互兜底（与 §6.8 一致）。`interviewer_*` 目的仅走 `email`，不受此影响。

### 6.3.2 投递原子领取（NotificationDelivery：queued → sending）

`Txn C`（§6.3）领取 `NotificationEvent` 并建好 `NotificationDelivery(queued)` 后，真正「调用外部通道」前还需一次**投递级原子领取**：把 `queued` 行安全地翻转为 `sending` 并取走投递数据。这一步与「建行」分离，是避免「同一行被发送两次」的关键边界。

> 注意：`created_at` 是**投递行创建时间**，**不是** Worker 真实领取时刻——`queued` 行可能在创建后很久才被本 `Txn D` 领取；隐式租约据此 `created_at` 计算（详见 §6.4）。

```
-- Txn D：短事务，内部【禁止】任何外部调用（SMTP / 飞书 / HTTP）
-- created_at 是「投递行创建时间」，不是「真实领取时间」；租约 = created_at + 5min（见 §6.4）
-- 只领「剩余租约足以覆盖（最大外部调用超时 + 安全余量）」的 queued 行；
--   剩余租约不足者不领，留待 Sweeper 在租约满 5min 时按「未发送」回收（§6.4），避免落入 sending 超时（结果未知）的误重发。
-- claim_horizon = now() - (5min - 外呼超时 - 安全余量)
UPDATE NotificationDelivery SET status='sending'
 WHERE id IN (
   SELECT id FROM NotificationDelivery
    WHERE status='queued'
      AND created_at >= now() - (interval '5 minutes'
                                 - interval '30 seconds'   -- 最大外部调用超时（§6.4）
                                 - interval '10 seconds')  -- 安全余量
    ORDER BY created_at, id
    FOR UPDATE SKIP LOCKED
    LIMIT :batch)
 RETURNING id, event_id, channel, delivery_purpose, event_version,
           attempt_no, channel_metadata;     -- 取走本次要发送的投递数据
COMMIT;   -- ★ 提交之后，才在事务【外】调用 SMTP / 飞书
```

- **事务内只改状态 + RETURNING，不碰外部**：`queued → sending` 与取数在同一短事务内原子完成；SMTP / 飞书调用在 `COMMIT` **之后**进行，**绝不在持有行锁的事务内发起**（与 §3.2「事务内禁止外部调用」一致，保证预约提交 P95 与 Slot 行锁不被外部延迟拖住）。
- **`queued` 不得长驻**：Worker 必须「领即发」——领取到 `queued` 行后立即在事务外调用通道，不把行留成 `queued` 长时间等待；`queued → sending` 必须**立即**发生（见 §6.4 超时区分：只有「领后未发」才落入 `queued` 超时）。
- **`Txn D` 领取范围受剩余租约约束**：只领取 `created_at >= claim_horizon` 的 `queued` 行（`claim_horizon = now() - (5min - 外呼超时 - 安全余量)`）。剩余租约不足以覆盖「外呼超时 + 余量」的 `queued` 行**不领取**，继续留在 `queued`，由 Sweeper 在 `created_at` 满 5min 后按「未发送」回收并重投——**不会**因「领了却来不及发」而落入 `sending` 超时（结果未知）分支，从而消除一类不必要的重复发送。
- **与外部调用超时的关系**：通道调用超时阈值须远小于 5 分钟隐式租约（如 10–30s），否则 `sending` 行尚未回执就会被 Sweeper 误回收（§6.4）。
- **与 `uq_delivery_attempt` 的边界**：本领取只翻转已存在行的 `status`，不新建行，故不受 `uq_delivery_attempt` 约束；该索引防的是「重复建行」（§6.3），本步骤防的是「同一行被重复发送」——二者职责不同，后者由「事务外调用 + 至少一次重投 + 幂等键去重」共同保证（§6.4/§6.5）。

### 6.4 处理超时恢复（Sweeper）——区分「未发送」与「结果未知」，用既有列构成隐式租约

`NotificationDelivery` 处于非终态（`queued` / `sending`）即表示「已建行、未回执」。`created_at` 是**投递行创建时间**，**并非** Worker 真实领取时刻——`queued` 行可能在创建后很久才被 `Txn D`（§6.3.2）领取。隐式租约仍以 `created_at` 为锚点计算：`lease_expire = created_at + 5 分钟`（5min 远大于 SRS §5.1 的邮件 P95 ≤10s 与飞书调用超时上限，避免误回收）。**外部通道调用超时阈值须远小于 5 分钟（如 10–30s）**——否则 `sending` 行尚未拿到回执就会被 Sweeper 抢先回收，造成「发了又被重发」的误判。

> **关键约束（`Txn D` 领取范围，§6.3.2）**：`Txn D` 只领取 `created_at >= claim_horizon` 的 `queued` 行，其中 `claim_horizon = now() - (5min - 外呼超时 - 安全余量)`。剩余租约不足以覆盖「外呼超时 + 余量」的 `queued` 行**不领取**，继续留在 `queued`，由 Sweeper 在其 `created_at` 满 5min 后按「未发送」回收（见下），**不会**因「领了却来不及发」而落入 `sending` 超时（结果未知）分支。

`queued → sending` 必须**立即发生**（见 §6.3.2 原子领取）：`queued` 长驻的两类情形——① Worker 在发送前崩溃（领前崩）；② `Txn D` 因剩余租约不足跳过、等待 Sweeper 按「未发送」回收。`sending` 长驻只可能是「已调用外部、等待回执时崩溃 / 进程被回收」。两类中间态的失败语义不同，Sweeper 必须按 `status` 分别处理，并使用不同 `last_error` 口径**：

```
-- Txn S：每 60s 执行
SELECT id, event_id, channel, delivery_purpose, event_version, attempt_no, status
  FROM NotificationDelivery
 WHERE status IN ('queued','sending')
   AND created_at < now() - interval '5 minutes'
 ORDER BY created_at
 FOR UPDATE SKIP LOCKED LIMIT :n;
```
- **`queued` 超时（= 领后未发，Worker 崩溃在发送前）**：外部**根本没被调用过** → 按「**未发送**」回收，`last_error='queued_lease_expired'`；直接重投即可，**不担心外部重复发送**。
- **`sending` 超时（= 已调用外部、未回执，Worker 崩溃在等待回执）**：外部**可能已发出** → 按「**结果未知**」回收，`last_error='sending_lease_expired_unknown'`；按 §6.1 至少一次语义**重投**，并**显式登记重复风险**（在 `last_error` 已区分的基础上触发运维告警，由《测试计划》覆盖该重投幂等场景）——服务商侧可能已收到一封相同的信。
- 两类回收后续分支相同：`attempt_no < 3 → 同行改 'retry_scheduled' + next_retry_at（指数退避）`；`attempt_no = 3 → 'dead_letter' + 后台高优先级告警`；回写 `NotificationEvent`：出现 `dead_letter → status='failed'`。

> **租约到期不等于外部未送达**——尤其 `sending` 超时，进程可能已把邮件交给 SMTP 才崩溃。因此回收后的动作是「再投一次」，这是至少一次语义的既定后果，由 §6.5 的幂等键消解，而不是假装没发生过。`queued` 超时风险低（未发过）、`sending` 超时风险高（可能重复），二者在 `last_error` 与告警上刻意区分，便于运维与《测试计划》分别处理。

### 6.4.1 回执写回必须使用 CAS，处理迟到 Worker（late receipt）

SMTP / 飞书调用**返回后**，无论成功或失败，Worker 写回状态都必须使用**条件更新（CAS）**，以 `status='sending'` 为前置条件：

```sql
-- Txn W：Worker 回执写回（成功 / 失败均走此路径）
UPDATE NotificationDelivery
   SET status              = :next,                 -- succeeded / failed
       last_error          = :err,                  -- 失败原因；成功为 NULL
       provider_message_id = :provider_message_id,  -- ★ 独立列，不得塞进 channel_metadata
       channel_metadata    =                        -- ★ JSONB 合并，不整体覆盖
         COALESCE(channel_metadata, '{}'::jsonb) || :meta
 WHERE id = :id AND status = 'sending'              -- ★ CAS 前置：仅当仍是 sending 才写
 RETURNING id;                                      -- 命中返回 1 行；被回收则 0 行
```

**逐字段核对已批准领域模型 v1.1.5 §6.12**（`NotificationDelivery` 全部列，Txn W 只允许写其中 4 列）：

| 列 | v1.1.5 是否存在 | Txn W 写? | 说明 |
|---|---|---|---|
| `id` / `event_id` / `delivery_purpose` / `channel` | ✅ | 否 | 建行时确定，终身不变 |
| `event_version` | ✅ | 否 | **事件版本，非乐观锁**；手动重发经其有意区分（§6.5），不由回执递增 |
| `attempt_no` | ✅ | 否 | 重试 = 新建尝试行（`attempt_no+1`），不在原行自增 |
| `status` | ✅ | **是** | `sending → succeeded / failed` |
| `last_error` | ✅ | **是** | 失败原因；成功写 `NULL` |
| `provider_message_id` | ✅（**独立列** `string NULL`） | **是** | **必须写独立列**；`§7` 退信按该列 + `channel='email'` + `event_version` 反查投递行，写进 JSONB 会使退信匹配失效 |
| `channel_metadata` | ✅ `jsonb` | **是（合并）** | 见下方合并规则 |
| `next_retry_at` | ✅ | 否 | 仅由 §6.4 Sweeper / 重试调度写 |
| `created_at` | ✅ | 否 | 投递行创建时间（§6.3.2：非领取时刻） |
| ~~`version`~~ | ❌ **不存在** | — | **v0.2 早前草案的 `version = version + 1` 是幻列，已删除**。领域模型中乐观锁 `version` 仅存在于 `Appointment` / `AppointmentSlot` / `KnowledgeDocument` / `KnowledgeIndexVersion`；本表的并发保护由 CAS 前置条件 `status='sending'` 承担，不需要也不存在版本列 |

**`channel_metadata` 合并规则（禁止整体覆盖）**：

- 写法固定为 `COALESCE(channel_metadata, '{}'::jsonb) || :meta`（PostgreSQL JSONB **顶层浅合并**，同名键以 `:meta` 为准，未出现的键原样保留）。整体覆盖（`channel_metadata = :meta`）会**抹掉 §7 退信处理已写入的 `bounced_at` / `bounce_reason`**——退信可能先于迟到回执落库，覆盖即造成退信证据丢失。
- `:meta` 的**允许键**按通道判别联合（领域模型 §5 / §6.12）：
  - `channel='email'` → 仅 `smtp_accepted_at`；
  - `channel='feishu'` → 仅 `provider_request_id` / `feishu_record_id` / `response_code`。
- **`bounced_at` / `bounce_reason` 仍只由 §7 退信处理回写**，Txn W **禁止**写入这两个键；`:meta` 中出现 bounce 键视为实现缺陷，须在集成测试中断言拒绝。§7 的幂等回写同样使用 JSONB 合并语义（`bounced_at` 仅在为空时写首次时间），与本处互不覆盖。

- **命中 1 行**：本 Worker 仍是该尝试的拥有者，正常写回终态（`succeeded` / `failed`）。
- **命中 0 行**：表示该 `sending` 行**已被 Sweeper 回收**（§6.4：租约超时 → `retry_scheduled` / `dead_letter`）。**迟到 Worker 不得覆盖** `retry_scheduled` / `dead_letter` / `next_retry_at` 等后续状态——它只记录一条「迟到回执」告警（含 `provider_message_id` / `attempt_no`），由 §6.5 幂等键在重投时消解可能的重复送达。
  - 0 行的原因只可能是 Sweeper 回收：`sending` 只能由 `Txn D` 置位、只能由 `Txn W`（CAS）或 Sweeper 离开。因此「回执命中 0 行」是**预期内的迟到竞态**，不是 bug；禁止用无条件 `UPDATE` 兜底覆盖回收后的状态。
- **CAS 与 §6.3.2 的衔接**：`Txn D` 已保证进入 `sending` 的行只被一个 Worker 领取（`SKIP LOCKED`），但进程崩溃后 Sweeper 会回收——CAS 写回是「崩溃回收」与「正常回执」之间的唯一正确仲裁点。
- **该 CAS 规则与迟到回执处理须由《测试计划》覆盖**：用例须模拟「Worker A 发送后崩溃被 Sweeper 回收为 `retry_scheduled` / `dead_letter`，Worker B（迟到回执）再写回」→ 断言命中 0 行、`retry_scheduled`/`dead_letter` 不被覆盖、仅产生迟到告警。

### 6.5 稳定幂等键与「外部成功、DB 提交失败」的重复投递

```
delivery_idempotency_key = H( NotificationEvent.idempotency_key || ':' || delivery_purpose || ':' || channel || ':' || event_version )
```

- **键中不含 `attempt_no`** —— 这是关键。若把 `attempt_no` 放进键，每次重试都会生成新键，服务商无法把它识别为同一封信，重复送达就变成必然。
- **手动重发有意 bump `event_version`**（领域模型 §6.12 / SRS §4.3：手动重发 = 新建尝试记录、`attempt_no`+1、幂等键含新 `event_version`）→ 产生**新键** → 属于「用户明确要求再发一次」，不是故障重复。
- 落地方式：
  - **邮件**：把该键确定性地映射为 `Message-ID`（同键 → 同 Message-ID），并记入 `channel_metadata.smtp_accepted_at` / `provider_message_id`。**SMTP 协议本身不提供服务商级幂等**；若所选服务商不按 `Message-ID` 去重，则「已成功投递但本地状态未提交」在重试后会**真实重复送达一封邮件**。这是至少一次语义下的**可接受残留风险**（邮件不产生业务后果），已登记，须由《测试计划》覆盖。
  - **飞书**：优先使用服务商提供的幂等令牌承载该键；多维表格写入以 `channel_metadata.feishu_record_id` 做「存在即更新」的幂等写，避免重复建记录。**飞书具体 API 是否提供幂等令牌须在集成验证清单中确认，本文不假定。**

### 6.6 重试驱动（避免旧尝试行反复触发）

```
SELECT d.* FROM NotificationDelivery d
 WHERE d.status='retry_scheduled' AND d.next_retry_at <= now()
   AND NOT EXISTS (SELECT 1 FROM NotificationDelivery x
                    WHERE x.event_id=d.event_id AND x.delivery_purpose=d.delivery_purpose
                      AND x.channel=d.channel
                      AND x.event_version=d.event_version
                      AND x.attempt_no > d.attempt_no)          -- 每个 (投递目的) 只有最新一次尝试才驱动重试
 ORDER BY d.next_retry_at
 FOR UPDATE SKIP LOCKED LIMIT :n;
-- 为每行插入 attempt_no+1 的新尝试记录（status='queued'）；uq_delivery_attempt 兜底防重
```
> 用「不存在更高 `attempt_no`」这一既有数据的判定，替代新增「是否已消费」标志列，因此**不扩模型**。

### 6.7 状态转换（逐条对齐 SRS §6.2 / 领域模型 §5，不新增任何状态）

**NotificationEvent**（枚举：`pending` / `processing` / `processed` / `cancelled` / `failed`）

| 转换 | 触发 | 约束 |
|---|---|---|
| `pending → processing` | Txn C 领取成功 | 仅 `SKIP LOCKED` 领取者；批量原子 |
| `processing → processed` | 该事件**所有目标通道**的最新尝试均 `succeeded` | 终态 |
| `processing → failed` | 任一通道进入 `dead_letter` | 触发后台高优先级告警；**不回滚业务** |
| `pending → cancelled` / `processing → cancelled` | 改期 / 取消 / owner 强制取消撤销未执行的 `reminder_due`（§4.2–§4.4） | 填 `cancelled_at`；改期时经 `superseded_by_event_id` 指向新事件 |

**NotificationDelivery**（枚举：`queued` / `sending` / `succeeded` / `failed` / `retry_scheduled` / `dead_letter`；每行 = 一次尝试）

| 转换 | 触发 |
|---|---|
| （建行）`queued` | Txn C 领取 / 重试驱动 / 手动重发，在事务内建行 |
| `queued → sending` | Txn D 原子领取（§6.3.2）：短事务 `FOR UPDATE SKIP LOCKED` 置 `sending` 并 `RETURNING` 投递数据；**提交后**才在事务外调用外部通道 |
| `sending → succeeded` | 服务商接受（记 `provider_message_id`、`channel_metadata.smtp_accepted_at` 或 `feishu_record_id`/`response_code`）；**必须经 `Txn W` CAS（`WHERE id=:id AND status='sending'`，§6.4.1）写回**；命中 0 行 = 已被 Sweeper 回收，迟到 Worker 不得覆盖 `retry_scheduled`/`dead_letter`，仅记迟到告警 |
| `queued|sending → failed` | 发送异常、外部调用超时（须远小于 5min），或 §6.4 租约回收（`queued`→`queued_lease_expired` / `sending`→`sending_lease_expired_unknown`）；`sending` 分支的失败写回同样经 `Txn W` CAS（§6.4.1），命中 0 行不覆盖后续状态 |
| `failed → retry_scheduled` | `attempt_no < 3`，写 `next_retry_at`（指数退避） |
| `failed → dead_letter` | `attempt_no = 3`（≤3 次已用尽） |
| `succeeded` + 退信回执 | **不改 `status`**，仅写 `channel_metadata.bounced_at` / `bounce_reason`（SRS §4.3/§6.2：退信不属 `DeliveryStatus` 枚举） |

行级终态：`succeeded` / `dead_letter` / `retry_scheduled`（该行已排程后继尝试，本行不再变更）。UI 失败中心（UI 线框 v1.0 A6）筛选的 `failed` / `retry_scheduled` / `dead_letter` 与本表一致。

### 6.8 通道独立、死信与告警（SRS §3.8 失败矩阵，不变）
- 通道**独立重试，不相互兜底**：飞书失败 → 重试飞书 + 邮件告警；邮箱失败 → 重试邮件 + 飞书告警；均失败 → 后台高优先级告警持续重试。
- 飞书同步失败 `FEISHU_SYNC_FAIL` → 邮件告警候选人 + 飞书任务重试；部分失败 `NOTIFY_PARTIAL`。
- **飞书接收标识缺失（candidate_notification 的 `feishu` 通道，§6.3.1）**：当 `OwnerContactConfig.candidate_feishu_open_id_ciphertext` 为 NULL 时，`feishu` 通道投递**直接失败并触发告警**；同事件 `email` 通道（`User.email` 始终存在）照常投递，二者独立、不相互兜底。`interviewer_*` 目的仅走 `email`，不受此影响。

### 6.9 人工重发（SRS §3.8/§3.9，UC-21）
- 失败中心手动重发 = 新建 `NotificationDelivery` 尝试记录（`delivery_purpose` 不变、`attempt_no`+1、`event_version`+1 → 新幂等键），受 `uq_delivery_attempt(event_id, delivery_purpose, channel, event_version, attempt_no)` 约束防重复；入 `AuditLog`。
- 限频：同账号每 10 分钟 ≤5 次、每小时 ≤20 次（SRS §5.6）。**限频实现机制留《安全设计》，本文只记阈值来源。**

### 6.10 模型边界声明
§6 全部机制仅使用领域模型 v1.1.5 既有结构：`NotificationEvent(status, scheduled_at, created_at, idempotency_key, cancelled_at, superseded_by_event_id)`、`NotificationDelivery(delivery_purpose, status, attempt_no, event_version, created_at, next_retry_at, last_error, provider_message_id, channel_metadata)` 与既有索引 `uq_delivery_attempt`（已调整为 `(event_id, delivery_purpose, channel, event_version, attempt_no)`）。`delivery_purpose` 为 v1.1.5 已批准字段，本草案仅使用、未新增。**未新增列、表或外部依赖。**

---

## 7. 退信（Bounce）回执入口：公网不可信边界约束

> 若《安全设计》裁定采用**服务商回调**接入，该端点是本系统**唯一暴露给外部服务商的公网写入口**，必须按**不可信输入**处理。若裁定采用**定时拉取**，则不存在该入口，§7.2 的业务约束仍然适用。**本文不预设采用哪一种。**

### 7.1 交由《安全设计》规定的必答项（架构层不裁定、不实现）
1. **请求验签**：服务商签名算法、签名覆盖范围（含 body 与时间戳）、验签失败即拒绝；
2. **防重放**：时间戳窗口 + 一次性随机数/消息 ID 去重，过期或重复请求拒绝；
3. **来源校验**：服务商源 IP 白名单 / mTLS / 专用路径与令牌，三选一或组合；
4. **密钥轮换**：回调密钥的存放（Secret Manager）、轮换周期与双密钥并行验证的过渡策略；
5. 入口独立限频与异常告警阈值。

### 7.2 架构层现在就规定的边界约束（与接入方式无关，强制）
1. **幂等回写**：同一退信回执重复到达任意次，效果与一次相同——`bounced_at` 只在为空时写入首次时间，`bounce_reason` 覆盖为最新值，不追加、不累计、不产生第二条记录。
2. **未知消息一律拒绝**：必须能按 `provider_message_id`（+ `channel='email'` + `event_version`）唯一匹配到**已存在**的 `NotificationDelivery` 行。匹配不到 → **拒绝请求**，记审计与告警，**不创建任何记录、不新建投递、不新建事件**。
3. **回调不得改变预约状态**：退信处理**只允许**写 `NotificationDelivery.channel_metadata.bounced_at` / `bounce_reason`。**禁止**改动 `Appointment`、`AppointmentSlot`、`NotificationEvent` 的任何状态，**也禁止**改动 `NotificationDelivery.status`（退信不属 `DeliveryStatus` 枚举，SRS §4.3/§6.2）。不回滚预约（与 `CONFIRM_MAIL_FAIL` 语义一致）。
4. **权限与角色**：该入口不携带任何用户身份，不得复用面试官/admin 的鉴权上下文，不得访问加密字段明文。
5. **后果**：退信触发飞书候选人告警 + 后台高优先级告警，并在失败中心按「退信 是/否」筛选呈现（UI 线框 v1.0 A6、SRS §3.8/§3.9）。

---

## 8. 知识库热更新与索引原子切换

### 8.1 版本化索引（SRS §3.2 R24，领域模型 §6.14）
- 上传/删除 → 创建 `KnowledgeIndexVersion`（`building`）；切片 + 嵌入构建向量。
- 完成后置 `ready` 并**原子切换** `active_index_version_id`；旧索引继续服务至切换完成（无服务中断）。
- 删除 → `retrieval_disabled_at` **立即置位**（禁止命中）；旧索引继续服务至切换。
- 任一文档新增/删除/索引切换 → 将 `invalidated_at IS NULL` 的 `RecommendedQuestionCache` 行置 `invalidated_at`，异步重建（领域模型 §6.16）。

### 8.2 分档 SLA（SRS §5.1）
- 纯文本 P95≤60s / 扫描不可复制 PDF P95≤120s / OCR PDF 异步 P95≤5min / 删除 P95≤5s。
- 索引失败 → 回滚旧索引继续服务（`INDEX_FAIL`）。

### 8.3 RAG 检索质量（SRS §3.2）
- 检索不到明确告知「资料未涵盖」不编造；冲突以最新/权威源为准；注入拦截率 = 100%；删除后相关缓存答案失效；合理推断须标注「推测」；模型不可用 → `MODEL_UNAVAILABLE`，不切换第二模型。
- 检索排序采用 `vector top10 + BM25 top10 → RRF 候选集 → 可选 Cross-Encoder top6`（ADR-RERANK-001）。重排只处理已经过页面/项目域过滤且通过相关性门槛的候选；未配置时保持 RRF，网络/协议失败时回退原顺序，不改变 grounded/拒答判定。
- 可选 Semantic Cache 只复用匿名公共 grounded 回答：按 page/project 域隔离，以 embedding 相似度命中，Redis 保存 embedding 与公开回答但不保存问题原文；知识库上传/删除后失效。Cache 故障旁路，登录态与工具路径禁止命中（ADR-RESILIENCE-001）。

---

## 9. 腾讯云部署 / 备份恢复 / 日志监控 / 故障降级

### 9.1 部署拓扑（SRS §2.3/§5.7，ADR-ARCH-001）
- **单 Region 腾讯云**；MVP 形态见 ADR-ARCH-001（推荐单台轻量应用服务器 + Docker Compose，应用单实例；设计保持无状态，可随时扩为多副本——§5 的 SSE 方案在单实例与多实例下同构，扩容不需要改设计）。
- 云数据库 PostgreSQL（含向量扩展，ADR-ARCH-002）+ 对象存储（静态前端 / 知识库原文件）。
- **应用无状态**：应用进程**不得在本地内存持有会话状态或限频计数**（否则扩副本即破功）；**具体存放介质由《安全设计》裁定**，本文不预设。

### 9.2 备份与恢复（SRS §5.5）
- 数据库每日自动**加密**备份；**RPO ≤ 24h、RTO ≤ 4h**；至少每月一次恢复演练。
- 知识库向量与关系数据同库 → **一次备份即覆盖两者**，无跨存储一致性问题（ADR-ARCH-002 的主要收益之一）。
- 知识库原文件存对象存储多副本；向量索引可由原文件重建。

### 9.3 日志与监控（SRS §5.2/§5.4/§6.3）
- 集中日志，写入前脱敏（会议号/电话等）；健康检查端点。
- 关键指标：SSE 派生延迟与推送延迟、强制重拉快照频次（衡量 §5.4 触发是否异常）、Outbox 领取延迟与积压量、租约回收次数、通知成功率 / 死信率 / 退信率、限频触发次数、RAG 首字延迟。
- 凭证（SMTP / 飞书 / LLM / 回调密钥）存 Secret Manager，不进代码、前端与日志。
- ADR-OBS-001：API 以 OpenTelemetry SDK 产生 HTTP/AIQA/tool Span，经 OTLP/HTTP 异步导出；Prometheus 从容器私网 `/internal/metrics` 抓取固定低基数指标，Grafana 读取 Prometheus 展示请求量、P95、AIQA outcome、token 与工具调用。未配置 OTLP 时 no-op；采集失败不影响业务。
- `/internal/metrics` 不进入公开 OpenAPI，Nginx 对公网请求显式返回 404；Prometheus 必须绕过 Nginx 直连 API 容器。

### 9.4 故障降级（SRS §5.4）
- LLM 与 Reranker provider 使用独立 Circuit Breaker：Redis 共享失败/open 状态并以 Lua 原子声明跨副本单探针，Redis 故障退回进程内 breaker；open 时直接走既有 `MODEL_UNAVAILABLE` 或 RRF 回退，不切换第二模型（ADR-RESILIENCE-001）。
- SSE 不可用 → 轮询降级（§5.7）；数据库短暂不可用 → 读路径返回上次快照并标注「数据可能延迟」，写路径直接失败不做本地排队（避免产生无法回滚的影子状态）。
- 飞书/邮件失败 → 失败通道独立重试告警，**不切换其他通道**。
- 模型不可用 → `MODEL_UNAVAILABLE`，不切换第二模型、不编造。
- 上线后 SLO：月度可用性 ≥ 99.5%（自然月度量）。

---

## 10. ADR：本轮明确推荐（proposed，待用户裁定 ratify）

> 以下四项按用户要求给出**唯一推荐方案 + 理由 + 重裁触发条件**。ADR 在被明确接受（accepted）前不对实现产生约束（`docs/baseline.yml` precedence 注）。**本文不自行 ratify。**

### ADR-ARCH-001 部署形态
- **推荐**：单台腾讯云轻量应用服务器 / CVM + Docker Compose，**应用单实例**；PostgreSQL 使用**云数据库**（非自建），对象存储用 COS。
- **理由**：① 使用周期仅面试期 1–2 月，成本上限 ¥130–220/月（SRS §5.7），云数据库 + 单台应用主机是唯一能同时满足成本与 RPO≤24h 自动备份的组合；② SLO 99.5%/月 ≈ 允许 3.6h 停机，单实例 + 自动重启足够；③ 运维人力为个人，容器编排（TKE）的复杂度收益为负；④ **§5 的 SSE 方案在单/多实例下完全同构**，将来加副本不需要重新设计。
- **重裁触发**：需要零中断滚动升级；并发显著上升；项目周期延长 > 6 个月。

### ADR-ARCH-002 向量方案（只选一个 MVP 主方案，不并存）
- **推荐**：**PostgreSQL + pgvector**，作为唯一 MVP 向量方案；**不引入独立向量数据库**。
- **理由**：① 知识库是个人简历与项目文档，切片量级 10²–10³，pgvector 的召回与延迟余量极大；② 与关系数据同库 → 备份/恢复/权限/事务/监控**共用一套**，§9.2 的 RPO/RTO 直接覆盖向量数据，消除「关系库已恢复、向量库未恢复」的不一致故障模式；③ 无额外月费，贴合成本上限；④ 少一个外部依赖与一个故障域。
- **验证项（属选型确认，不是新增依赖）**：确认所选托管 PostgreSQL 实例可启用 `pgvector` 扩展。若不可启用 → **本 ADR 需重裁**（候选：自建 PostgreSQL，或腾讯云向量数据库）。
- **重裁触发**：切片量 > 50 万；检索 P95 > 300ms；需要多租户向量隔离。

### ADR-ARCH-003 SSE 可靠传播方案
- **推荐**：**提交派生轮询（commit-derived polling）+ 资源版本对齐 + 先订阅后快照**（§5 全文）。
- **理由**：① **从根上消除双写丢事件窗口**——事件来源是已提交的数据库状态，而不是「提交后再发一条消息」；② 不需要任何中间件提供可靠性/有序性保证（Redis Pub/Sub 本就不提供，v0.1 的假设是错的）；③ **不需要新增表、列或复制槽 → 零领域模型变更**；④ 窗口约 350 行、T=1s，满足 SRS ≤2s，成本可忽略；⑤ 单实例与多实例同构，无粘性会话要求。
- **明确放弃**：Redis Pub/Sub 作为事件源（不可靠、不可恢复）；PostgreSQL 逻辑复制 CDC（需 `wal_level=logical` + 复制槽运维，未消费槽会撑爆 WAL，且 MVP 无收益）；新增持久化事件日志表（需扩模型）。
- **重裁触发**：见 §5.6 的四项阈值。

### ADR-ARCH-004 Outbox 消费方案
- **推荐**：**数据库轮询 + `FOR UPDATE SKIP LOCKED` 领取 + `uq_delivery_attempt` 二重互斥 + 隐式租约 Sweeper**（§6 全文）。
- **理由**：① 不新增任何列或表（租约由既有 `status` + `created_at` 表达）；② 与 §6.7 状态机天然一致，无需额外协调状态；③ Worker 可水平扩展且天生互斥；④ 通知本就允许秒级延迟，CDC 的近实时优势在此场景无价值，却要付出复制槽运维代价。
- **重裁触发**：事件量 > 10 events/s；领取延迟 P95 > 5s；需要跨系统事件分发。

### 其余 ADR：本轮**不裁定**
| ADR | 议题 | 本轮处理 |
|-----|------|----------|
| ADR-ARCH-005 | 密码哈希算法 | **不裁定**，留《安全设计》。若拟选算法与 PRD §8.7（BCrypt）不一致，须先经 Change Request 更新并批准全部受影响规范，规范同步完成前不得实现（领域模型 v1.1.5 §1 冲突升级条款、SRS §6.3） |
| ADR-ARCH-006 | 退信接入方式（回调 / 定时拉取） | **不裁定**，留《安全设计》。架构正文不假定实现，仅规定 §7.2 的边界约束 |
| ADR-ARCH-007 | 会话存储介质 | **不裁定**，留《安全设计》。架构仅约束「应用进程不得在本地内存持有会话状态」（§9.1） |
| ADR-ARCH-008 | 限频实现机制 | **不裁定**，留《安全设计》。架构仅约束「限频计数不得存于单实例内存」并记录 SRS §5.6 阈值来源 |

---

## 11. 开放问题与遗留裁定

### 11.1 `AUTH_EXPIRED` / `RATE_LIMITED` 语义（已由 SRS v1.2 裁定）
- `AUTH_EXPIRED` 仅表示登录会话过期，处理为重新登录。
- 所有限频场景统一使用 `RATE_LIMITED`，并遵守 SRS §5.6 的独立阈值与 `Retry-After` 约定。
- 架构不再保留 v1.1 的冲突假设；OpenAPI 实现不得将 `AUTH_EXPIRED` 用作限频错误。

### 11.2 其他待定（不阻塞架构评审）
- 飞书多维表格字段映射与是否提供幂等令牌（留《接口契约》+ 集成验证清单）。
- 托管 PostgreSQL 的 `pgvector` 可用性确认（ADR-ARCH-002 验证项）。
- `OVERRIDE_NOT_FOUND`（并发已删）与 `OVERRIDE_RANGE_EMPTY`（范围不命中任何 Slot）现已由 SRS v1.2 §8 正式定义；架构层继续约束两种情形必须 ROLLBACK 拒绝、不得放行，OpenAPI 负责映射统一错误体。

---

## 12. 与基线/下游关系 + v0.1 → v0.2 变更记录

### 12.1 基线关系
- 本文档 based_on SRS v1.2 / 领域模型 v1.1.5 / UI 线框 v1.0（均 approved）。
- 密码哈希算法**显式不在本阶段选择**；退信接入方式、会话存储、限频实现**显式不在本阶段假定**。
- 下游：《安全设计》→《接口契约（OpenAPI/SSE）》→《测试计划》→ 开发准入评审。
- 本文档 approved 前，下游不得据此锁定物理端点；SRS §8 错误码表为唯一权威。

### 12.2 v0.1 → v0.2 变更记录（TASK-ARCH-002）

| # | v0.1 问题 | 影响 | v0.2 修正 |
|---|-----------|------|-----------|
| 1 | 称 Redis Pub/Sub「保证多实例下事件一致、有序到达」 | **一致性**：Redis Pub/Sub 至多一次、不持久、不重放，该保证不成立 | §5.1 撤回该表述并说明其真实语义；SSE 路径不再使用消息中间件 |
| 2 | 「提交写事务后发布事件到 Redis」 | **可靠性**：commit 与 publish 双写，中间崩溃 → 事件永久丢失且无人察觉 | §5.1 事件来源改为**已提交的数据库状态**，双写窗口消失 |
| 3 | 事件无版本/序列，仅靠"重连拉快照" | **一致性**：无法检测漏序；快照与增量之间存在竞态窗口 | §5.2 每事件带 `resource_version`（既有乐观锁列）+ 连接级 `stream_seq`；§5.3 先订阅→缓冲→拉带水位快照→按版本重放 |
| 4 | 未定义强制重拉快照的触发条件 | **一致性**：静默不一致可长期存在 | §5.4 五类强制触发 + 5 分钟周期性静默对账 |
| 5 | `SELECT ... AND status='available' FOR UPDATE` | **一致性**：状态过滤先于加锁，会跳过并发修改行并读到陈旧状态 | §4.0 规则 3：加锁不带 status 过滤，**锁后**校验 |
| 6 | 未定义全流程统一锁顺序 | **可靠性**：并发改期/取消可死锁 | §4.0 定义 L0→L3 唯一锁顺序；改期强制新旧格合并升序加锁 |
| 7 | 改期未先锁 Appointment、未校验 active/归属/version | **一致性**：改期与 owner 强制取消可互相覆盖 | §4.2 先锁 L1 并校验三项，再锁合并 Slot 集合并重新校验 |
| 8 | 创建流程未写 `CompanyBookingException` 的同事务锁定与消费 | **一致性**：例外可被并发重复消费 | §4.1 同事务 `FOR UPDATE` 校验 + 置 `consumed_at` + 写 `dedupe_exception_id`，`uq_appointment_exception` 兜底 |
| 9 | 缺用户取消流程 | 覆盖缺口 | §4.3 补齐（释放 `available` + 撤销提醒 + 取消告知函） |
| 10 | Outbox 只说"异步消费者"，无领取机制 | **可靠性**：多 Worker 会重复投递 | §6.3 `FOR UPDATE SKIP LOCKED` + `uq_delivery_attempt` 二重互斥 |
| 11 | 无处理超时恢复 | **可靠性**：Worker 崩溃后事件永久卡在 `processing` | §6.4 以既有 `status`+`created_at` 构成隐式租约（5min）+ Sweeper 回收 |
| 12 | 未声明投递语义与重复风险 | **可靠性**：「外部已发送、DB 未提交」无处理口径 | §6.1 明确至少一次；§6.5 稳定幂等键（**不含 attempt_no**）+ 残留重复风险如实登记 |
| 13 | 状态转换未成表、与 SRS/领域模型未逐条对齐 | 实现歧义 | §6.7 两张转换表，逐条对齐 SRS §6.2 / 领域模型 §5，不新增状态 |
| 14 | Bounce Webhook 未标注为不可信入口 | **安全边界**：公网写入口无约束 | §7 标为公网不可信入口；架构层规定幂等回写/未知消息拒绝/不得改预约与 `DeliveryStatus`；验签等转《安全设计》 |
| 15 | 正文预设「会话存 Redis/DB」「限频 Redis 令牌桶」「Bounce Webhook 接入」 | 越界预判安全设计 | §1.1/§9.1/§10 全部中性化，仅保留与实现无关的边界约束 |
| 16 | ADR 仅列候选，无推荐 | 无法评审裁定 | §10 对部署形态/向量方案/SSE/Outbox 各给唯一推荐 + 理由 + 重裁触发 |

### 12.3 v0.2 本轮补充修正（2026-08-09：3 项实现正确性 + 2 项并发竞态 + 2 项 Schema/并发收口，仍 review）

| # | 问题 | 修正 |
|---|------|------|
| 17 | Outbox 缺「投递级原子领取」；`uq_delivery_attempt` 被误读为能防同一行重复发送 | §6.3.2 新增 `NotificationDelivery` 投递级原子领取（`queued→sending`，短事务 `FOR UPDATE SKIP LOCKED` + RETURNING，提交后才调外部）；§6.3 明确 `uq_delivery_attempt` **只防重复建行、不防同一行重复发送** |
| 18 | §4.2/§4.3 释放 Slot 无条件写 `available`，破坏 `AvailabilityOverride` 真相源 | §4.6 定义释放后**重新物化**规则（force_unavailable→unavailable / force_available→available / 无覆盖→日历规则）；§4.2 改期旧格、§4.3 用户取消均改走重新物化；§4.7 规定 `AvailabilityOverride` 变更事务须锁受影响 Slot 并重新物化，由 Slot 行锁串行化并发 |
| 19 | §6.4 隐式租约未区分 `queued`（未发送）与 `sending`（结果未知）超时 | §6.4 按 `status` 分两类回收：`queued` 超时→`queued_lease_expired`（未发送，安全重投）；`sending` 超时→`sending_lease_expired_unknown`（结果未知，至少一次重投+登记重复风险）；外部调用超时须远小于 5min；原开放项 §11.2 与待办 §13.1/§13.2 已并入正文，§13 删除 |
| 20 | §4.7 `AvailabilityOverride` 变更「先写 Override、再只锁未占用 Slot」存在竞态：override 提交的瞬间，并发事务仍可按旧 override 集合物化 Slot，产生「override 已生效但 Slot 显示旧状态」窗口 | §4.7 重写为「先读旧范围（更新/删除算 `old_range ∪ new_range`）→ 统一升序锁范围内**全部** `AppointmentSlot`（含 `booked`）→ 锁后复检冲突 override（更新排除自身 `id`）→ 冲突 ROLLBACK、无冲突才 `INSERT`/`UPDATE`/`DELETE` → 仅对 `appointment_id IS NULL` 的 Slot 重新物化（`booked` 保持 `booked` 但参与锁与冲突串行化）」 |
| 21 | 投递 `created_at` 被当作真实领取时刻；`queued` 临近租约仍被领取致落入 `sending` 超时（结果未知）误重发；回执写回无 CAS，迟到 Worker 可覆盖 Sweeper 回收后的状态 | §6.3.2 明确 `created_at` 为创建时间（非领取时刻）、`Txn D` 仅领剩余租约足以覆盖「外呼超时+余量」的 `queued` 行（临近/超租约留 Sweeper 按未发送回收）；§6.4 重写租约锚点说明 + 新增 §6.4.1 `Txn W` 回执 CAS（`WHERE id=:id AND status='sending'`），命中 0 行=已被回收，迟到 Worker 仅记告警、不得覆盖 `retry_scheduled`/`dead_letter`；§6.7 两转换行同步 CAS 约束；CAS 迟到场景登记为《测试计划》待覆盖风险 |
| 22 | §6.4.1 `Txn W` SQL **引用不存在的列** `NotificationDelivery.version`；`provider_message_id` 被写进 `channel_metadata`；`channel_metadata` 整体覆盖会抹掉 §7 已写入的退信键 | §6.4.1 SQL 改为：删除 `version = version + 1`（幻列，本表无乐观锁列，CAS 由 `status='sending'` 前置条件承担）；`provider_message_id = :provider_message_id` **写独立列**（否则 §7 按该列反查投递行失效）；`channel_metadata = COALESCE(channel_metadata,'{}'::jsonb) \|\| :meta` **JSONB 浅合并**；新增**逐字段核对表**（对齐 v1.1.5 §6.12 全 12 列，标明 Txn W 只写 4 列）与 `:meta` 允许键白名单；**`bounced_at`/`bounce_reason` 仍只由 §7 退信处理回写**，Txn W 禁写 |
| 23 | §4.7 未处理**同一 override 的并发 UPDATE/DELETE**：旧范围来自事务外/前端，两个并发事务各自基于陈旧 `old_range` 算出不相交 Slot 锁集合，行锁串行化失效；且允许创建不命中任何 Slot 的 override（无锁定载体，冲突复检可并发通过） | §4.0 锁顺序新增 **L2.5 `AvailabilityOverride`（按 id，先于 L3）** 与强制规则 5；§4.7 重写为 8 步：① UPDATE/DELETE 先 `SELECT ... FOR UPDATE` 锁自身行取**当前真实 `old_range`**（0 行→ROLLBACK），禁用前端传入旧值；② 据真实值算 `affected_range`（不相交则按两段一次性升序加锁）；③ **CREATE/UPDATE 范围须对齐并命中 ≥1 个现存 Slot，命中 0 → ROLLBACK 拒绝**（DELETE 豁免）；④–⑧ 沿用锁全部 Slot（含 `booked`）→ 锁后复检冲突（排除自身 id）→ 无冲突才写 → 仅物化 `appointment_id IS NULL`；§4.5 矩阵增 3 行；两个拒绝语义曾在评审阶段作为占位名，现已由 SRS v1.2 §8 正式定义 |

### 12.4 模型边界结论
本次修正**未新增**任何领域实体、表、字段、索引或外部依赖，全部方案落在领域模型 v1.1.5 已批准范围内 → **未触发 Stop & Report**。已识别但明确放弃的扩模型方案（事件日志表、`updated_at` 增量列、租约列、CDC 复制槽）记录于 §5.6 与 §10，将来采纳须先走 Change Request。

---

---

> **文档结束** · 架构 v0.2（approved） · based_on SRS v1.2 / 领域模型 v1.1.5 / UI 线框 v1.0 · approval_commit=`da3f6fc`。
