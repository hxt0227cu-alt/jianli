# 个人 AI 问答网站 — 领域模型设计（Domain Model）v1.1.2

> 本文档是《需求文档 v2.3.3》与《用例规约 v1.7.2》之后的分析设计工件，属"分析/设计"阶段产物。
> 用途：冻结数据库边界与领域实体关系，作为《接口契约》《测试计划》与架构设计的前置输入。
> 当前版本与评审状态见 `docs/baseline.yml`。编码准入由 baseline `development_gate` 决定。
> **状态机枚举以需求文档 §8.10 为唯一规范源**，本文仅引用，不另立状态名。
> **v1.1.2 整改（第六轮 P0-6~P0-8 + 实现边界）**：`CompanyBookingException` 补 `revoked_at`/`revoked_by` 与并发消费锁（`FOR UPDATE` + `uq_appointment_exception`）；`DeliveryAttempt` 幽灵实体全文改为 `NotificationDelivery` 尝试记录并补唯一约束；`RecommendedQuestionCache` 改为 `page_key/questions_json/generated_at/invalidated_at` + `UNIQUE(page_key) WHERE invalidated_at IS NULL`（取消全局版本字段）；`AvailabilityOverride` 补 NOT NULL 约束与 `CHECK`、明确为 owner 意图真相源；并发抢占补三格连续性服务端校验；逻辑模型与物理 Schema 分离说明；配套 PRD v2.3.3、用例规约 v1.7.2。

---

## 1. 范围与边界

- 纳入：账号与认证会话、问答会话、知识库生命周期、预约/时段/通知三大领域、公告、审计。
- 不纳入（留待架构/接口契约）：具体 REST 路由、SSE 载荷、飞书/邮件 SDK 细节、部署拓扑。
- **存储策略（沿用 PRD v2.3.3 决策）**：
  - 敏感字段**逐列 AES-256-GCM 密文（ciphertext）**，密钥经 KMS；
  - 公司名以 **HMAC-SHA256(normalized_name, site_key)** 生成 `fingerprint` 去重，**不暴露原文**；
  - `start_at/end_at` 业务元数据，**明文存但受访问控制**；
  - `password_hash` 当前按 Argon2id 设计，但**最终算法待《安全设计》ADR 裁定**（PRD §8.7 记为 BCrypt，二者冲突以安全设计为准）；各类 token 仅存哈希；
  - 审计日志写入前对会议号/电话等**脱敏**。

### 1.1 建模粒度（第五轮复评）

v1.0/v1.1 早期曾为每项能力独立建表（共 24+ 概念），对单人多站点 MVP 过重。本版按"最小实现模型"收敛：

- **MVP 建表实体：20 个**（§2.1）。
- **MVP 合并实现的能力：5 项**（不独立建表，§2.2），待真实复杂度出现再拆表。
- 合并与建表边界由本文件唯一界定；任何"延后项"不得预先建表/字段/接口（见 `docs/baseline.yml` `deferred`）。

### 1.2 逻辑领域模型 vs 物理数据库 Schema（分离声明）

本文件是**逻辑领域模型**，不是物理 DDL。两者的冻结时机与责任边界不同：

| 层 | 内容 | 载体 | 冻结时机 |
|----|------|------|----------|
| **逻辑领域模型（本文件）** | 实体、属性语义、关系与基数、状态机引用、业务不变式、唯一性/互斥语义 | `docs/design/domain-model.md` | **SRS 前**评审通过 |
| **物理数据库 Schema** | PostgreSQL 具体类型（`timestamptz`/`JSONB`/`interval`/`bytea`）、部分唯一索引语法、`FOR UPDATE` 锁粒度、分区/膨胀策略、迁移脚本 | 架构阶段 ADR + 迁移目录（尚未创建） | **ADR 接受后**冻结 |

约定：

- 本文件中出现的 SQL 片段（如 `CREATE UNIQUE INDEX ... WHERE ...`、`SELECT ... FOR UPDATE`）为**语义示意**，用于表达"必须由数据库层保证"的不变式，**不构成最终 DDL**；最终类型与索引写法以物理 Schema 冻结版为准。
- 逻辑模型未通过前，不得编写迁移脚本；物理 Schema 未冻结前，不得开始与表结构耦合的编码。
- 若物理实现需要偏离本文件的语义（例如某不变式改由应用层保证），必须回改本文件并重新评审，不得只在代码/迁移中单方面变更。

---

## 2. 领域实体清单

### 2.1 MVP 建表实体（20 个）

| # | 实体 | 对应需求类 / 规则 | 职责 | 基数 |
|---|------|------------------|------|------|
| 1 | User | 类1 账号身份 | 面试官 / owner_admin 统一身份（同物理表，按 `role` 分认证域） | 1 |
| 2 | AuthSession | P0-1 | 认证会话（多设备 / 令牌轮换 / 单设备注销）；中性 `session_token_hash`，不锁死 JWT/Refresh 模式 | 0..* / User |
| 3 | InterviewerProfile | 类1 扩展 | 面试官展示名（仅 interviewer 角色） | 0..1 / User |
| 4 | OwnerContactConfig | 类7 | owner 本人手机号（仅 owner_admin 角色） | 0..1 / User |
| 5 | EmailVerificationToken | P0-7 | 注册邮箱验证 | 0..* / User |
| 6 | PasswordResetToken | P0-7 | 密码找回 | 0..* / User |
| 7 | Company | 类2 | 公司归一化指纹 + 加密原文，去重依据 | 1 |
| 8 | Appointment | 类2/2b | 预约生命周期与加密业务字段（公司名快照） | 0..* / User |
| 9 | AppointmentSlot | 类2b | 课程表网格单元，承载 SlotStatus（timestamptz） | 0..* |
| 10 | AvailabilityOverride | P2-3 / P0-5 | owner 标红 / 节假日覆盖 / **强制可约**（合并 CalendarOverride） | 0..* |
| 11 | PageAnnouncement | P0-7 | 页面 3 顶部公告（单例） | 0..1 |
| 12 | NotificationEvent | P1-5 Outbox | 通知/提醒事件（业务事实），幂等键（合并 ReminderSchedule） | 0..* |
| 13 | NotificationDelivery | P1-5 | 每通道每次尝试（通用 DeliveryStatus + 通道元数据 JSONB） | 1..* / Event |
| 14 | Conversation | 类3 | 跨登录对话线程（R23） | 0..* / User |
| 15 | Message | 类3 | 会话单条消息，含越界标记 | 0..* / Conversation |
| 16 | KnowledgeDocument | 类5 | 上传文档元信息 + 去重/禁检索/索引切换字段 | 0..* |
| 17 | KnowledgeIndexVersion | 类5 | 热更新索引版本与状态 | 0..* / Document |
| 18 | AuditLog | 类4 | 审计（含预约历史事件，合并 AppointmentEvent） | 0..* |
| 19 | RecommendedQuestionCache | P1-3 | 推荐问题异步生成缓存（按 page_key，0..*） | 0..* |
| 20 | CompanyBookingException | P0-4 | 公司去重**一次性例外授权**（被拦截时 Appointment 尚不存在） | 0..* |

### 2.2 MVP 合并实现的能力（不独立建表，共 5 项）

| 原独立表提案 | 合并方式 | 说明 |
|-------------|----------|------|
| EmailDeliveryMetadata | `NotificationDelivery.channel_metadata JSONB`（email 分支） | 存 `smtp_accepted_at` / `bounced_at` / `bounce_reason` |
| FeishuDeliveryMetadata | `NotificationDelivery.channel_metadata JSONB`（feishu 分支） | 存 `provider_request_id` / `feishu_record_id` / `response_code` |
| ExternalSyncBinding | 飞书绑定为单例配置，存配置中心/Secret Manager；状态变更入 `AuditLog` | MVP 仅一个飞书绑定，不建表 |
| AppointmentEvent | `AuditLog`（action=appointment.created/updated/rescheduled/cancelled） | 历史事件即审计条目，不独立表 |
| ReminderSchedule | `NotificationEvent`（type=reminder_due, `scheduled_at`） | 临近提醒由定时任务扫描 `scheduled_at` 触发，不独立表 |

> 注：`CalendarOverride` 已提升为建表实体 `AvailabilityOverride`（§2.1 #10）；`CompanyDedupeOverride` 已提升为建表实体 `CompanyBookingException`（§2.1 #20）。两者不再合并实现。

---

## 3. 类图（Class Diagram，仅 20 建表实体）

```mermaid
classDiagram
    class User {
        +id UUID PK
        +email string UK "全局唯一→单身份单角色"
        +password_hash string "Argon2id"
        +role enum[interviewer, owner_admin]
        +verified bool
        +deletion_requested_at timestamptz NULL
        +deleted_at timestamptz NULL "软删"
        +purge_after timestamptz NULL "硬删时点"
    }
    class AuthSession {
        +id UUID PK
        +user_id UUID FK
        +session_token_hash string "中性，不锁死 JWT/Refresh"
        +device string NULL
        +ip inet NULL
        +expires_at timestamptz NOT NULL
        +revoked_at timestamptz NULL
    }
    class InterviewerProfile {
        +user_id UUID PK,FK
        +display_name string
    }
    class OwnerContactConfig {
        +id UUID PK
        +user_id UUID UK,FK
        +candidate_phone_ciphertext bytes AES
        +updated_at timestamptz
    }
    class EmailVerificationToken {
        +id UUID PK
        +user_id UUID FK
        +token_hash string
        +expires_at timestamptz
        +consumed_at timestamptz NULL
    }
    class PasswordResetToken {
        +id UUID PK
        +user_id UUID FK
        +token_hash string
        +expires_at timestamptz
        +consumed_at timestamptz NULL
    }
    class Company {
        +id UUID PK
        +normalized_name_fingerprint string UK,HMAC
        +raw_name_ciphertext bytes AES
    }
    class Appointment {
        +id UUID PK
        +user_id UUID FK
        +company_id UUID FK
        +dedupe_exception_id UUID FK NULL "→CompanyBookingException"
        +start_at timestamptz
        +end_at timestamptz
        +status enum[active,cancelled,completed]
        +company_name_ciphertext bytes AES "预约时快照"
        +company_name_fingerprint string HMAC "预约时快照"
        +meeting_platform_ciphertext bytes AES
        +meeting_number_ciphertext bytes AES
        +contact_ciphertext bytes AES
        +notes_ciphertext bytes AES
        +version int 乐观锁
        +created_at timestamptz
        +cancelled_at timestamptz NULL
        +completed_at timestamptz NULL
        +deleted_at timestamptz NULL
        +purge_after timestamptz NULL
    }
    class AppointmentSlot {
        +id UUID PK
        +start_at timestamptz
        +end_at timestamptz
        +status enum[available,booked,owner_locked,unavailable]
        +appointment_id UUID FK NULL
        +version int 乐观锁
    }
    class AvailabilityOverride {
        +id UUID PK
        +start_at timestamptz NOT NULL
        +end_at timestamptz NOT NULL
        +action enum[force_unavailable,force_available] NOT NULL
        +reason string NULL
        +created_by UUID NOT NULL FK "owner 意图真相源"
        +created_at timestamptz
    }
    class PageAnnouncement {
        +id UUID PK
        +content text
        +updated_at timestamptz
    }
    class NotificationEvent {
        +id UUID PK
        +type enum "appointment_created/appointment_details_updated/appointment_rescheduled/appointment_cancelled/reminder_due"
        +biz_id UUID
        +scheduled_at timestamptz NULL "仅 reminder_due"
        +idempotency_key string UK
        +status enum[pending,processing,processed,cancelled,failed]
        +cancelled_at timestamptz NULL
        +superseded_by_event_id UUID NULL
        +created_at timestamptz
    }
    class NotificationDelivery {
        +id UUID PK
        +event_id UUID FK
        +channel enum[feishu,email]
        +event_version int
        +attempt_no int
        +status enum[queued,sending,succeeded,failed,retry_scheduled,dead_letter]
        +channel_metadata jsonb "email/feishu 判别联合"
        +provider_message_id string NULL
        +next_retry_at timestamptz NULL
        +last_error text NULL
        +created_at timestamptz
    }
    class Conversation {
        +id UUID PK
        +user_id UUID FK
        +created_at timestamptz
        +updated_at timestamptz
        +deleted_at timestamptz NULL
        +purge_after timestamptz NULL
    }
    class Message {
        +id UUID PK
        +conv_id UUID FK
        +role enum[user,assistant]
        +content text
        +is_offtopic bool
        +created_at timestamptz
    }
    class KnowledgeDocument {
        +id UUID PK
        +name string
        +type enum[md,pdf,docx,txt]
        +size int
        +content_checksum string "SHA-256 解析文本，去重"
        +storage_key string "对象存储路径"
        +status enum[indexing,indexed,failed]
        +parse_mode enum[text,ocr,native] NULL
        +failure_reason text NULL
        +retrieval_disabled_at timestamptz NULL "删除即禁检索"
        +active_index_version_id UUID FK NULL "当前服务索引"
        +version int
        +created_at timestamptz
    }
    class KnowledgeIndexVersion {
        +id UUID PK
        +doc_id UUID FK
        +version int
        +status enum[building,ready,rolled_back]
        +indexed_at timestamptz
    }
    class AuditLog {
        +id UUID PK
        +actor string
        +action string "含 appointment.created/updated/rescheduled/cancelled + 去重例外/手动重发"
        +target string
        +masked_detail text
        +created_at timestamptz
    }
    class RecommendedQuestionCache {
        +id UUID PK
        +page_key string "home_page / project_page"
        +questions_json jsonb
        +generated_at timestamptz
        +invalidated_at timestamptz NULL
    }
    class CompanyBookingException {
        +id UUID PK
        +interviewer_user_id UUID FK
        +company_fingerprint string "HMAC，匹配 Company.fingerprint"
        +approved_by UUID
        +reason text
        +expires_at timestamptz
        +consumed_at timestamptz NULL "消费后一次性失效"
        +created_at timestamptz
    }

    User "1" --> "0..*" AuthSession
    User "1" --> "0..1" InterviewerProfile
    User "1" --> "0..1" OwnerContactConfig
    User "1" --> "0..*" EmailVerificationToken
    User "1" --> "0..*" PasswordResetToken
    User "1" --> "0..*" Appointment : 面试官预约
    Company "1" --> "0..*" Appointment
    User "1" --> "0..*" AvailabilityOverride : owner 标红/覆盖
    User "1" --> "0..*" Conversation
    Appointment "1" --> "0..3" AppointmentSlot : 占 3 格（外键在 Slot）
    Appointment "0..1" --> "1" CompanyBookingException : 消费一次性授权
    Appointment "1" --> "1..*" NotificationEvent : 触发通知/提醒
    NotificationEvent "1" --> "1..*" NotificationDelivery : 每通道每次尝试
    Conversation "1" --> "0..*" Message
    KnowledgeDocument "1" --> "0..*" KnowledgeIndexVersion
    Company "1" --> "0..*" CompanyBookingException : 按 fingerprint
    User "1" --> "0..*" CompanyBookingException : 按 interviewer
    APPOINTMENT ..o{ AUDIT_LOG : "历史事件入审计"
    COMPANY ..o{ AUDIT_LOG
    USER ..o{ AUDIT_LOG
```

---

## 4. ER 关系图（ER Diagram，仅 20 建表实体）

```mermaid
erDiagram
    USER ||--o{ AUTH_SESSION : "多设备"
    USER ||--o| INTERVIEWER_PROFILE : "仅面试官"
    USER ||--o| OWNER_CONTACT_CONFIG : "仅 owner"
    USER ||--o{ EMAIL_VERIFICATION_TOKEN : "注册验证"
    USER ||--o{ PASSWORD_RESET_TOKEN : "找回"
    USER ||--o{ APPOINTMENT : "面试官预订"
    COMPANY ||--o{ APPOINTMENT : "一家公司一时段"
    USER ||--o{ AVAILABILITY_OVERRIDE : "owner 标红/覆盖"
    USER ||--o{ CONVERSATION : "拥有"
    APPOINTMENT ||--o{ APPOINTMENT_SLOT : "占 3 格(外键在Slot)"
    APPOINTMENT |o--o{ COMPANY_BOOKING_EXCEPTION : "消费一次性授权"
    APPOINTMENT ||--o{ NOTIFICATION_EVENT : "触发"
    NOTIFICATION_EVENT ||--o{ NOTIFICATION_DELIVERY : "每通道每次尝试"
    CONVERSATION ||--o{ MESSAGE : "包含"
    KNOWLEDGE_DOCUMENT ||--o{ KNOWLEDGE_INDEX_VERSION : "索引版本"
    COMPANY ||--o{ COMPANY_BOOKING_EXCEPTION : "按 fingerprint"
    USER ||--o{ COMPANY_BOOKING_EXCEPTION : "按 interviewer"

    USER {
        uuid id PK
        string email UK "全局唯一"
        string password_hash "Argon2id"
        enum role "interviewer/owner_admin"
        bool verified
        timestamptz deletion_requested_at NULL
        timestamptz deleted_at NULL
        timestamptz purge_after NULL
    }
    APPOINTMENT {
        uuid id PK
        uuid user_id FK
        uuid company_id FK
        uuid dedupe_exception_id FK NULL "→CompanyBookingException"
        timestamptz start_at "明文/受控"
        timestamptz end_at "明文/受控"
        enum status "active/cancelled/completed"
        bytes company_name_ciphertext "AES,预约时快照"
        string company_name_fingerprint "HMAC,预约时快照"
        bytes meeting_platform_ciphertext "AES"
        bytes meeting_number_ciphertext "AES"
        bytes contact_ciphertext "AES"
        bytes notes_ciphertext "AES"
        int version "乐观锁"
        timestamptz cancelled_at NULL
        timestamptz completed_at NULL
        timestamptz deleted_at NULL
    }
    APPOINTMENT_SLOT {
        uuid id PK
        timestamptz start_at
        timestamptz end_at
        enum status "SlotStatus"
        uuid appointment_id FK "NULL"
        int version "乐观锁"
    }
    NOTIFICATION_DELIVERY {
        uuid id PK
        uuid event_id FK
        enum channel "feishu/email"
        int event_version
        int attempt_no
        enum status "queued/sending/succeeded/failed/retry_scheduled/dead_letter"
        jsonb channel_metadata "通道判别联合"
        string provider_message_id NULL
        timestamptz next_retry_at NULL
        text last_error NULL
        timestamptz created_at
    }
    KNOWLEDGE_DOCUMENT {
        uuid id PK
        string name
        enum type "md/pdf/docx/txt"
        int size
        string content_checksum "SHA-256 去重"
        string storage_key "对象存储路径"
        enum status "indexing/indexed/failed"
        enum parse_mode "text/ocr/native NULL"
        text failure_reason NULL
        timestamptz retrieval_disabled_at NULL "删除即禁检索"
        uuid active_index_version_id FK NULL "当前服务索引"
        int version
        timestamptz created_at
    }
    COMPANY_BOOKING_EXCEPTION {
        uuid id PK
        uuid interviewer_user_id FK
        string company_fingerprint "HMAC"
        uuid approved_by
        text reason
        timestamptz expires_at
        timestamptz consumed_at NULL "一次性"
        timestamptz created_at
    }
```

> 其余实体（AuthSession / InterviewerProfile / OwnerContactConfig / EmailVerificationToken / PasswordResetToken / Company / AvailabilityOverride / PageAnnouncement / NotificationEvent / Conversation / Message / KnowledgeIndexVersion / AuditLog / RecommendedQuestionCache）字段类型与约束见 §6。

---

## 5. 状态机规范（引用需求文档 §8.10 唯一规范源）

三状态机互相独立，仅通过 `appointment_id` 关联：

| 状态机 | 枚举 | 持久化 | 关键不变量 |
|--------|------|--------|-----------|
| **SlotStatus**（时段） | `available` / `booked` / `owner_locked` / `unavailable` | `AppointmentSlot.status` | 🟨 黄格**不属此枚举**（前端 Session 态）；`unavailable`=系统规则（周末/节假日/用餐），可由 `AvailabilityOverride(action=force_unavailable)` 修正；`force_available` 可把系统判为不可约的某天强制设为可约；`owner_locked`=owner 主动锁定（含 owner 强制取消） |
| **AppointmentStatus**（预约） | `active` / `cancelled` / `completed` | `Appointment.status` | 提交即 `active`；改期 `active→active`（原子事务）；无 `pending`/`draft`；`cancelled`/`completed` 仅置位时间字段 |
| **DeliveryStatus**（通知投递，通道无关） | `queued` / `sending` / `succeeded` / `failed` / `retry_scheduled` / `dead_letter` | `NotificationDelivery.status` | 独立于预约；手动重发=**新建 `NotificationDelivery` 尝试记录**（`attempt_no`+1）；邮件 `bounced` 与飞书 `response_code` 仅存 `channel_metadata` JSONB 分支，不混入通用枚举 |

> **NotificationEvent 生命周期（P0-6）**：`status` = `pending` → `processing` → `processed`（终态）；异常 `failed`（进入 Delivery 重试/死信）；**改期/取消时**：未执行的 `reminder_due` 事件置 `cancelled`（填 `cancelled_at`），改期产生的旧提醒可经 `superseded_by_event_id` 指向新事件。事件类型仅表达**业务事实**：`appointment_created` / `appointment_details_updated` / `appointment_rescheduled` / `appointment_cancelled` / `reminder_due`；具体用哪个模板/通道由消费者与通道适配器决定，**不允许 `appointment_created` 与 `confirm_mail` 重复投递**（已移除 `confirm_mail` 类型）。

> **通道元数据判别联合（P1-5）**：`NotificationDelivery.channel_metadata` 为 JSONB，但代码中必须定义为两个独立类型，禁止作为任意字典穿透业务层：
> - email 分支：`smtp_accepted_at` / `bounced_at` / `bounce_reason`
> - feishu 分支：`provider_request_id` / `feishu_record_id` / `response_code`

---

## 6. 正式表结构（Schema，仅 20 建表实体）

> 约定：`PK`=主键，`FK`=外键，`UK`=唯一，`NULL`=可空；`AES` 逐列密文，`HMAC` 指纹；`明文/受控` 明文存但仅授权角色可读。

### 6.1 User（单表双认证域）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| email | string | UK, 全局唯一 | 单身份单角色；注册验证邮箱；确认函收件人=此邮箱（R26） |
| password_hash | string | NOT NULL | 待《安全设计》ADR 裁定（当前按 Argon2id 设计；PRD §8.7 记为 BCrypt，冲突待安全设计确认） |
| role | enum | NOT NULL | interviewer / owner_admin |
| verified | bool | NOT NULL | 邮箱验证通过 |
| deletion_requested_at | timestamptz | NULL | 注销请求时间 |
| deleted_at | timestamptz | NULL | 软删；查询默认排除 |
| purge_after | timestamptz | NULL | 硬删时点（注销后 30 天） |

> **账号域隔离（P0-1）**：面试官与 owner_admin 同物理表、按 `role` 分认证域；`email` 全局唯一保证一个邮箱=一个身份=一个角色；owner_admin 不能创建预约，interviewer 不能访问 admin 后台。`InterviewerProfile`（仅 interviewer）与 `OwnerContactConfig`（仅 owner_admin）均为 **0..1**。所有持久登录经 `AuthSession`（见 6.2），`User` 不再存 `remember_token_hash`。

### 6.2 AuthSession（P0-1）
| id UUID PK | user_id UUID FK→User | session_token_hash string NOT NULL（中性名称，不预设 JWT/Refresh 模式） | device string NULL | ip inet NULL | expires_at timestamptz NOT NULL | revoked_at timestamptz NULL |

> 刷新/吊销/多设备/单设备注销统一由本表管理；具体是 Cookie Session 还是 Refresh Token 由认证 ADR 决定。

### 6.3 InterviewerProfile / OwnerContactConfig（0..1）
| InterviewerProfile.user_id UUID PK,FK | display_name string NULL |
| OwnerContactConfig.id UUID PK | user_id UUID UK,FK | candidate_phone_ciphertext bytes AES NULL | updated_at timestamptz |

### 6.4 EmailVerificationToken / PasswordResetToken（P0-7）
| (EmailVerificationToken\|PasswordResetToken).id UUID PK | user_id UUID FK | token_hash string NOT NULL | expires_at timestamptz NOT NULL | consumed_at timestamptz NULL |

### 6.5 Company
| id UUID PK | normalized_name_fingerprint string UK,HMAC-SHA256 | raw_name_ciphertext bytes AES-256 |

### 6.6 Appointment
| id UUID PK | user_id UUID FK→User NOT NULL | company_id UUID FK→Company NOT NULL | dedupe_exception_id UUID FK→CompanyBookingException NULL（消费一次性授权时填入） |
| start_at / end_at timestamptz 明文/受控 | status enum NOT NULL active/cancelled/completed |
| company_name_ciphertext bytes AES **预约时快照** | company_name_fingerprint string HMAC **预约时快照** |
| meeting_platform_ciphertext / meeting_number_ciphertext / contact_ciphertext / notes_ciphertext bytes AES 逐列加密 |
| version int NOT NULL 乐观锁 | created_at timestamptz NOT NULL |
| cancelled_at / completed_at timestamptz NULL | deleted_at timestamptz NULL | purge_after timestamptz NULL |

> **快照语义（P1）**：`company_name_*` 是提交时拷贝自 Company 的**不可变快照**，不随 Company 后续修改而变；`Appointment` 自身即"该次预约登记了什么公司"的真相源。已移除冗余 `last_delivery_status`。**占用关系仅经 `AppointmentSlot.appointment_id` 表达，不冗余存 `slot_ids[]`**（P0-3）。

**部分唯一索引（P0-4，"一家公司一时段"+"一人一时段"，公司例外经独立授权）**：
```sql
-- 公司指纹约束：正常预约唯一；被一次性例外授权绕过时（dedupe_exception_id 非空）排除
CREATE UNIQUE INDEX uq_active_company
  ON Appointment(company_name_fingerprint)
  WHERE status='active' AND dedupe_exception_id IS NULL;

-- 一人一时段：始终生效，例外授权绝不绕过
CREATE UNIQUE INDEX uq_active_user
  ON Appointment(user_id)
  WHERE status='active';

-- 保证同一 (面试官, fingerprint) 仅存在一个未消费例外（一次性）
CREATE UNIQUE INDEX uq_exception_open
  ON CompanyBookingException(interviewer_user_id, company_fingerprint)
  WHERE consumed_at IS NULL;
```
> 预约创建时若命中 `DUP_COMPANY`：在事务内以行锁读取 `CompanyBookingException`（`consumed_at IS NULL AND revoked_at IS NULL AND expires_at > now()`，fingerprint 与 interviewer 匹配）；命中则在同一事务写入 `dedupe_exception_id` 并置 `consumed_at`、创建 `Appointment`（受 `uq_appointment_exception` 约束，防并发重复消费）；`uq_active_user` 在任何情况下都强制「一人一个 active 预约」。

### 6.7 AppointmentSlot（P0-2）
| id UUID PK | start_at / end_at timestamptz NOT NULL（带日期与时区） | status enum NOT NULL SlotStatus | appointment_id UUID FK→Appointment NULL（唯一占用真相源） | version int NOT NULL 乐观锁 |

```sql
ALTER TABLE AppointmentSlot
  ADD CONSTRAINT uq_slot_unique UNIQUE (start_at, end_at),
  ADD CONSTRAINT ck_slot_duration CHECK (end_at = start_at + interval '30 minutes');
```

### 6.8 并发抢占（P0-4，Slot 行锁）
```sql
BEGIN;
SELECT id, status, start_at, end_at, version FROM AppointmentSlot
  WHERE start_at IN (:s1,:s2,:s3) AND status='available'
  FOR UPDATE;                 -- 行锁，先到先得
-- 服务端校验（不依赖前端传入三个合法格子）：
--   命中行数 = 3
--   同一 day（start_at 同日）
--   s2.start_at = s1.end_at 且 s3.start_at = s2.end_at（连续 30min 格）
--   appointment.end_at = s1.start_at + interval '90 minutes'
-- 任一不满足 → ROLLBACK，返回 SLOT_TAKEN
-- 公司/账号去重由 6.6 部分唯一索引在 INSERT 时强制
INSERT INTO Appointment(..., start_at, end_at) VALUES (..., :s1_start, :s1_start + interval '90 minutes');
UPDATE AppointmentSlot SET status='booked', appointment_id=:aid, version=version+1
  WHERE id IN (:s1,:s2,:s3);
COMMIT;
```
> `Appointment.version` 仅保护**已存在行**并发写；新预约并发由 **Slot 行锁 + 部分唯一索引** 保证；三格连续性由服务端锁行后校验，不信任前端。`appointment.end_at = 起始格 + 90min` 为唯一计算口径。

### 6.9 AvailabilityOverride（P0-5，合并 CalendarOverride）
| id UUID PK | start_at timestamptz NOT NULL | end_at timestamptz NOT NULL | action enum[force_unavailable, force_available] NOT NULL | reason string NULL | created_by UUID NOT NULL FK→User | created_at timestamptz |
> `CHECK(end_at > start_at)`；`force_unavailable` = owner 主动标红 / 节假日覆盖（系统规则可由它修正）；`force_available` = 将系统判为不可约（周末/节假日）的某天**强制设为可约**。**`AvailabilityOverride` 是 owner 人工意图的真相源**，`AppointmentSlot.status` 仅为供网格查询的**物化状态**；创建/修改/删除 override 必须在同一事务内同步更新受影响 Slot 并发送 SSE，不允许两个相互冲突的人工 override 同时覆盖同一时段；人工覆盖优先级高于自动规则。

### 6.10 PageAnnouncement
| id UUID PK | content text | updated_at timestamptz |

### 6.11 NotificationEvent（Outbox，合并 ReminderSchedule，P0-6）
| id UUID PK | type enum[appointment_created,appointment_details_updated,appointment_rescheduled,appointment_cancelled,reminder_due] | biz_id UUID | scheduled_at timestamptz NULL（仅 reminder_due） | idempotency_key string UK | status enum[pending,processing,processed,cancelled,failed] | cancelled_at timestamptz NULL | superseded_by_event_id UUID NULL | created_at |
> 临近提醒：定时任务扫描 `type=reminder_due AND scheduled_at<=now() AND status=pending`，触发生成 `NotificationDelivery`，不独立建表。**改期/取消时**：将未执行 `reminder_due` 事件置 `cancelled`（填 `cancelled_at`）；改期产生的旧提醒可经 `superseded_by_event_id` 指向新事件，确保提醒随预约生命周期正确撤销/重建。

### 6.12 NotificationDelivery（通用状态 + 通道元数据 JSONB，合并 Email/Feishu 元数据）
| id UUID PK | event_id UUID FK | channel enum[feishu,email] | event_version int | attempt_no int | status enum[queued,sending,succeeded,failed,retry_scheduled,dead_letter] | channel_metadata jsonb（email/feishu **判别联合**，见 §5） | provider_message_id string NULL | next_retry_at timestamptz NULL | last_error text NULL | created_at |
```sql
CREATE UNIQUE INDEX uq_delivery_attempt
  ON NotificationDelivery(event_id, channel, event_version, attempt_no);
```
> 手动重发=新建一条 `NotificationDelivery` 尝试记录（`attempt_no`+1），幂等键含 `event_version`；该唯一索引防止并发消费者产生重复尝试记录。

### 6.13 Conversation / Message（含留存）
| Conversation.id UUID PK | user_id FK→User | created_at / updated_at | deleted_at timestamptz NULL | purge_after timestamptz NULL（180 天） |
| Message.id UUID PK | conv_id FK→Conversation | role enum(user/assistant) | content text | is_offtopic bool | created_at |

### 6.14 KnowledgeDocument / KnowledgeIndexVersion（P1-3）
| KnowledgeDocument.id UUID PK | name | type enum(md/pdf/docx/txt) | size int | content_checksum string（SHA-256 解析文本，相同文件去重） | storage_key string（对象存储路径） | status enum(indexing/indexed/failed) | parse_mode enum(text,ocr,native) NULL | failure_reason text NULL | retrieval_disabled_at timestamptz NULL（删除立即禁检索） | active_index_version_id UUID FK→KnowledgeIndexVersion NULL（当前服务索引） | version int | created_at |
| KnowledgeIndexVersion.id UUID PK | doc_id FK→KnowledgeDocument | version int | status enum(building/ready,rolled_back) | indexed_at |

> 热更新原子切换：`retrieval_disabled_at` 在删除时立即置位（禁止命中）；新索引 `building` 完成后置 `active_index_version_id` 并切 `ready`，旧索引继续服务至切换；失败 `rolled_back` 回退。

### 6.15 AuditLog（合并 AppointmentEvent）
| id UUID PK | actor string | action string（含 appointment.created/updated/rescheduled/cancelled、去重例外解除、确认函手动重发） | target string | masked_detail text（脱敏） | created_at |

### 6.16 RecommendedQuestionCache（P1-2，0..*）
| id UUID PK | page_key string NOT NULL（home_page / project_page） | questions_json jsonb | generated_at timestamptz | invalidated_at timestamptz NULL |
```sql
CREATE UNIQUE INDEX uq_rq_cache ON RecommendedQuestionCache(page_key)
  WHERE invalidated_at IS NULL;
```
> 推荐问题异步生成后落此表（每页一组）。知识库**任一文档**新增/删除/活动索引切换时，将所有 `invalidated_at IS NULL` 的缓存行置 `invalidated_at`，再由后台任务异步重新生成（新行 `invalidated_at` 为空、独占该 page_key）。页面只读缓存，缺失或已失效走固定兜底问题（非实时生成），**不引入"知识库全局版本"表**。

### 6.17 CompanyBookingException（P0-4，一次性例外授权）
| id UUID PK | interviewer_user_id UUID FK→User NOT NULL | company_fingerprint string NOT NULL（HMAC，匹配 Company.fingerprint） | approved_by UUID NOT NULL | reason text NOT NULL | expires_at timestamptz NOT NULL | consumed_at timestamptz NULL（消费后一次性失效） | revoked_at timestamptz NULL（撤销后置位） | revoked_by UUID NULL | created_at timestamptz |
> 仅 admin 可创建；仅绕过**公司指纹**唯一约束（`uq_active_company` 经 `dedupe_exception_id` 排除），**绝不绕过 `uq_active_user`**；消费后 `consumed_at` 置位，不可复用；**未消费可撤销（`revoked_at`/`revoked_by`），撤销后不可再消费**；**已消费例外不能靠撤销删除已有预约**，已有预约只能走 owner 强制取消（UC-20）；全程入 `AuditLog` 可审计。

**并发消费保证（P0-6）**：两个并发预约同时命中同一未消费例外时，必须在同一数据库事务内、以行锁消费例外并创建预约，确保二者互斥：
```sql
-- 事务内：先以行锁读取未撤销、未过期、未消费的例外
SELECT id, consumed_at, revoked_at, expires_at
  FROM CompanyBookingException
  WHERE id = :exception_id
    AND consumed_at IS NULL
    AND revoked_at IS NULL
    AND expires_at > now()
  FOR UPDATE;

-- 校验通过则：① 置 consumed_at；② INSERT Appointment 并写 dedupe_exception_id；
-- 二者在同一事务提交，配合 uq_appointment_exception 防止重复消费。
INSERT INTO Appointment(..., dedupe_exception_id) VALUES (..., :exception_id);
```
```sql
-- 保证每个例外最多被一个预约消费（防并发重复消费）
CREATE UNIQUE INDEX uq_appointment_exception
  ON Appointment(dedupe_exception_id)
  WHERE dedupe_exception_id IS NOT NULL;
```


---

## 7. 数据层权限支撑（非业务权限矩阵）

> 完整 RBAC 权限矩阵（面试官 / owner_admin / 系统任务 的查看-修改-删除）见未来 **SRS**（吸收用例规约后），不在本文重复维护。领域模型仅保证数据层可支撑：

- 字段级加密（AES）字段仅经授权通道解密：面试官的 `meeting_*` / `contact_*` 经确认函渲染与本人后台；owner 的 `OwnerContactConfig.candidate_phone_ciphertext` 仅设置页与确认函渲染可解密。
- 红格对他人仅显"已预约"，无公司名/可识别信息（R16）；完整 PII 仅授权角色经加密/脱敏通道。
- 所有敏感操作（owner 锁定/取消、手动重发、去重例外）入 `AuditLog`（脱敏）。

---

## 8. 关键业务不变量（与需求规则映射）

| 不变量 | 规则 | 落点 |
|--------|------|------|
| 一家公司一时段 | 同 `company_name_fingerprint` 仅一个 `active` 且 `dedupe_exception_id IS NULL` 预约 | 部分唯一索引 `uq_active_company` + 归一化比较；一次性例外经 `CompanyBookingException`（消费后置 `dedupe_exception_id`） |
| 一人一时段 | 同 `user_id` 仅一个 `active` 预约 | 部分唯一索引 `uq_active_user`（**始终生效，例外绝不绕过**） |
| 确认不预占 | 黄格不落库；提交成功才 `available→booked` | §8.10.1 + P1-2 |
| 改期原子 | 占新段+释旧段同事务，新段不可用则保持原 `active` | §8.10.2 |
| 并发抢占 | 仅一人成功，另一收 `SLOT_TAKEN` | Slot 行锁（`FOR UPDATE`）+ 部分唯一索引 |
| 通知独立重试 | 通道失败不相互兜底，独立重试+告警 | §8.10.3 + 通道元数据 JSONB |
| 去重例外可审计 | 例外仅 admin、一次性、需原因、可撤销；仅绕过公司约束 | `CompanyBookingException` + `uq_exception_open` + `AuditLog` |
| 强制可约/不可约 | 人工覆盖优先于自动规则 | `AvailabilityOverride.action` |
| 提醒随生命周期 | 改期/取消时旧提醒 `cancelled`，不重复/不漏发 | `NotificationEvent.status`/`cancelled_at`/`superseded_by_event_id` |
| PII 不泄露 | 红格脱敏、字段密文、日志脱敏 | §8.7 / §8.6 |
| 确认函只发验证邮箱 | 收件人=注册邮箱，不可改 | R26 |
| 留存与清理 | 取消 30d / 完成 90d / 对话 180d / 注销 30d 后硬删 | `cancelled_at`/`completed_at`/`purge_after`/`deleted_at` |

---

## 9. 数据留存与清理映射（P0-8）

| 对象 | 触发 | 留存期 | 字段 | 清理动作 |
|------|------|--------|------|----------|
| Appointment（取消） | `cancelled_at` 置位 | 30 天 | `cancelled_at` / `purge_after` | 到期硬删（留 AuditLog 摘要） |
| Appointment（完成） | `completed_at` 置位 | 90 天 | `completed_at` / `purge_after` | 到期硬删 |
| Conversation | 创建 | 180 天 | `purge_after` | 到期硬删（含 Message） |
| User（注销） | `deletion_requested_at` | 30 天 | `deleted_at` / `purge_after` | 软删后到期彻底删除账号及关联 PII |
| KnowledgeDocument（删除） | `retrieval_disabled_at` 置位 | 立即禁检索；索引 `rolled_back` | `retrieval_disabled_at` / `active_index_version_id` | 旧索引继续服务至新索引就绪，删除即禁检索 |

> 定时清理任务读取上述时间字段执行，全程可审计。

---

## 10. 与后续工件接口（待办）

- **《接口契约》**：基于本模型定义 `POST /appointments`、`POST /appointments/{id}/reschedule`、`DELETE /appointments/{id}`、`GET /slots`、`GET /conversations`、`POST /auth/...` 等 REST + SSE（`slot.updated` / `appointment.created` / `appointment.cancelled`）+ 飞书/邮件外部对接边界。
- **《测试计划》**：覆盖并发抢格（Slot 行锁 + `SLOT_TAKEN`）、隐私（红格脱敏/DB 加密/飞书明文同步）、通知（失败/重试/幂等、邮件 `bounced` vs 飞书 `response_code` 分存 `channel_metadata`）、去重例外（`CompanyBookingException` 一次性放行 + `uq_active_user` 不绕过 + 审计）、提醒撤销（改期/取消置 `cancelled`）、知识库热更新（去重/立即禁检索/索引切换）、留存清理、AI（RAG 正确/越界拒答/人格一致）。
- 编码准入由 `docs/baseline.yml` 的 `development_gate` 决定（须 `prd` / `use_cases` / `domain_model` / `srs` / `ui_wireframe` / `architecture` / `security` / `openapi` / `test_plan` / `ai_governance` 全部 `approved`），仅《接口契约》与《测试计划》通过不足开放功能编码。

---

> 版本：v1.1.2（2026-08-06，第六轮一致性整改）｜配套 PRD v2.3.3、用例规约 v1.7.2｜状态机以需求文档 §8.10 为唯一规范源｜建表实体 20 个 + 合并实现 5 项能力（不独立建表）。
