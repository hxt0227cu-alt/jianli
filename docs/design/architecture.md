# 架构设计与 ADR（review 草案 v0.1）

> **文档状态**：v0.1 · `status = review`（尚未 approved，不计入 `docs/baseline.yml` 的 precedence 裁决约束；经用户独立评审通过后方可置 `approved`）。
> **依据基线（based_on，引用 `docs/baseline.yml`）**：PRD v2.3.3 / 用例规约 v1.7.2 / 领域模型 **v1.1.4** / SRS **v1.1** / UI 线框 **v1.0** / AI 治理 1.0.1。
> **范围边界（硬约束）**：本文档定义系统边界、模块划分、部署与调用关系、关键事务边界、SSE/通知可靠性机制、知识库索引切换、部署运维与 ADR 清单；**不定义** REST URL、请求/响应 Schema、SSE 事件载荷字段、物理表结构（以领域模型 §6 为准）、密码哈希算法（留《安全设计》ADR）、具体错误码新增。SRS §8 错误码表为唯一权威，本文不新增、不修改。

---

## 1. 系统边界与上下文

### 1.1 系统范围
| 边界 | 包含 | 不包含（延后/外部） |
|------|------|---------------------|
| 前端 | 页面1 简历问答页 / 页面2 项目展示页 / 页面3 动态面试表页 / admin 后台 / 登录注册 | 移动端竖屏（<1024px 阻断）、微信助理（deferred） |
| 后端 | 认证、时段/预约、通知 Outbox 消费者、知识库管理、飞书同步、临近提醒调度、退信回调 | 混元 Fallback（deferred）、LangGraph/MCP（deferred） |
| 数据 | PostgreSQL（关系 + 向量）+ Redis（会话/广播/限频） | 数据仓库、OLAP |
| 外部集成 | SMTP（邮件）、飞书开放 API（多维表格+提醒）、托管 LLM（DeepSeek）、向量库 | 微信 WorkBuddy（deferred） |

### 1.2 外部依赖（PRD §8.2，待确认，不阻塞设计）
- 邮箱与 SMTP 账号/授权码、域名/备案；
- 飞书多维表格授权；
- 人格素材与知识库文件；
- 腾讯云资源（云数据库 PostgreSQL、Redis、向量库、对象存储）。

### 1.3 运行环境约束（SRS §2.3）
- 云端部署（腾讯云），本机不搭服务；大模型经托管 LLM API。
- 浏览器：Chrome/Edge/Firefox 最新稳定版；最低视口 1280×720；平板横屏可用；<1024px 阻断提示。
- 时区 UTC+8；时段以 `start_at`/`end_at` 时间戳存储。

---

## 2. 模块划分

| 模块 | 职责 | 对应领域实体 | 进程形态 |
|------|------|--------------|----------|
| Web 前端（静态+SSE 客户端） | 三大页面 + admin 后台 + 登录注册；SSE 接收状态推送 | — | 静态资源（CDN/对象存储） |
| API 网关 / BFF | 统一鉴权、限频、路由 | — | 无状态应用实例（可多副本） |
| Auth 服务 | 注册/登录/记住我/找回；账号隔离 | User / AuthSession / EmailVerificationToken / PasswordResetToken | 同 API 进程 |
| Slots/Appointments 服务 | 时段查询、预约创建/改期/取消（原子事务） | AppointmentSlot / Appointment / Company / CompanyBookingException / AvailabilityOverride | 同 API 进程 |
| Notifications Outbox 消费者 | 拉取 NotificationEvent → 投递 NotificationDelivery（重试/死信/退信回写/人工重发） | NotificationEvent / NotificationDelivery | 独立 Worker（可同进程线程或独立部署） |
| Reminder Scheduler | 扫描 `reminder_due` 事件触发临近提醒 | NotificationEvent(type=reminder_due) | 独立定时任务 |
| Feishu Sync | 预约变更同步飞书多维表格；同步失败告警 | — | 同 Notifications 或独立 |
| Knowledge 服务（admin） | 知识库上传/删除/热更新；索引版本切换 | KnowledgeDocument / KnowledgeIndexVersion | 同 API 进程 |
| RAG 检索+生成 | 切片检索 + L1 人格层生成（调用托管 LLM） | Conversation / Message / RecommendedQuestionCache | 同 API 进程 |
| SSE Hub | 维护 SSE 连接；订阅 Redis Pub/Sub 广播领域事件 | — | 同 API 进程（每实例本地连接表 + 中心化广播） |
| Bounce Webhook | 接收 SMTP 服务商退信回调 → 回写 channel_metadata | NotificationDelivery.channel_metadata | 同 Notifications 或独立端点 |

> 模块边界与领域模型 §2 实体清单一一对应；MVP 推荐**单体模块化**（同进程多模块），非强制微服务（complex_agent_infra 为 deferred）。Outbox 消费者与 Reminder Scheduler 可独立进程部署以满足可靠性隔离。

---

## 3. 部署与调用关系

### 3.1 逻辑部署图（文字描述）
```
[浏览器]──HTTPS──▶[API 网关/BFF](无状态×N)
                        │
        ┌───────────────┼───────────────────────┬───────────────────┐
        ▼               ▼                        ▼                   ▼
  [Auth/Slots/        [Notifications        [Reminder           [Knowledge/RAG]
   Appointments/        Outbox 消费者]        Scheduler]           (admin + 检索生成)]
   Knowledge/RAG]       │                      │
        │               │ 轮询/CDC 拉 Outbox    │ 扫描 reminder_due
        ▼               ▼                      ▼
   [PostgreSQL          [Redis: 会话/限频/      [向量库: 知识库索引]
    (关系+向量)]         SSE 广播 Pub/Sub]
        ▲               ▲
        │               │
   [SMTP]◀──投递──[Notifications]      [飞书 API]◀──同步/提醒──[Feishu Sync]
   [SMTP]──退信回调──▶[Bounce Webhook]──▶ channel_metadata 回写
   [托管 LLM API]◀──生成──[RAG]
```

### 3.2 调用关系要点
- **写路径（预约创建）**：浏览器 → API 网关 → Appointments 服务 → 单 DB 事务（Slot 行锁 + 部分唯一索引 + 写 Appointment + 写 NotificationEvent Outbox）→ 提交；事务外由 Notifications 消费者异步投递。
- **读路径（面试表）**：浏览器 → API 网关 → Slots 服务查快照；SSE Hub 经 Redis Pub/Sub 接收写事件并推浏览器。
- **通知路径**：Appointments/Feishu Sync → NotificationEvent（Outbox）→ Notifications 消费者 → 按通道建 NotificationDelivery → SMTP/飞书。
- **RAG 路径**：问答 → RAG 检索（向量库）→ 托管 LLM 生成（L1 人格层）→ 流式返回；会话持久化（登录用户）。
- **外部失败解耦**：预约成功事务**不依赖** SMTP/飞书成功（SRS §4.3）；确认函失败 `CONFIRM_MAIL_FAIL` 不回滚预约。

---

## 4. 关键事务边界

> 所有事务在单一 PostgreSQL 事务内完成；Outbox 写入与业务写**同事务**保证原子性（SRS §3.8/§4.3，领域模型 §6.11）。

### 4.1 预约创建（SRS §3.5，领域模型 §6.6/§6.7/§6.11）
```
BEGIN;
  SELECT id,status,... FROM AppointmentSlot
    WHERE start_at IN (:s1,:s2,:s3) AND status='available' FOR UPDATE;   -- 行锁，先到先得
  -- 校验三格均 available（不信任前端）；否则 ROLLBACK → SLOT_TAKEN
  -- 公司/账号去重由部分唯一索引在 INSERT 时强制（DUP_COMPANY/DUP_ACCOUNT）
  INSERT INTO Appointment(...) VALUES (...);                            -- uq_active_company / uq_active_user 强制
  UPDATE AppointmentSlot SET status='booked', appointment_id=:aid, version=version+1
    WHERE id IN (:s1,:s2,:s3);
  INSERT INTO NotificationEvent(type='appointment_created', idempotency_key=..., status='pending');
COMMIT;
-- 事务后：Notifications 消费者异步生成 NotificationDelivery（双通道提醒 + 飞书同步 + 确认函）
```
- 二次确认（UC-19）**不预占**：黄格不落库；确认提交才走上述原子锁；3 分钟超时 `CONFIRM_EXPIRED` 仅作废前端态、无持久化。
- 并发抢占：另一人绿转红 → 返回 `SLOT_TAKEN`（领域模型 §6.7）。

### 4.2 原子改期（SRS §3.6，领域模型 §6.7）
```
BEGIN;
  -- 锁新段（不先释旧段）
  SELECT ... FROM AppointmentSlot WHERE start_at IN (:n1,:n2,:n3) AND status='available' FOR UPDATE;
  -- 新段不可用 → ROLLBACK，原 Appointment 保持 active（禁止先释放原格再重选）
  UPDATE Appointment SET start_at=:n_start, end_at=:n_start+interval '90 min' WHERE id=:aid;
  UPDATE AppointmentSlot SET status='available', appointment_id=NULL, version=version+1
    WHERE appointment_id=:aid AND start_at IN (:o1,:o2,:o3);   -- 释旧 3 格
  UPDATE AppointmentSlot SET status='booked', appointment_id=:aid, version=version+1
    WHERE id IN (:n1,:n2,:n3);                                  -- 占新 3 格
  -- 旧 reminder_due 事件置 cancelled；INSERT NotificationEvent(type='appointment_rescheduled')
COMMIT;
-- 改期重发确认函（标注时间已更新）
```
- 不变量：新段不可用则原预约不变；≥50 并发重复≥10 次仅一人成功（SRS §3.6 验收）。

### 4.3 owner 强制取消（SRS §3.7，领域模型 §6.7/§6.15）
```
BEGIN;
  UPDATE AppointmentSlot SET status='owner_locked', appointment_id=NULL, version=version+1
    WHERE appointment_id=:aid;                                 -- 释放 3 格为 owner_locked（红，优先级高于自动规则）
  UPDATE Appointment SET status='cancelled', cancelled_at=now() WHERE id=:aid;
  INSERT INTO NotificationEvent(type='appointment_cancelled'); -- 取消告知函（必须）
  INSERT INTO AuditLog(action='appointment.cancelled', masked_detail=...);
COMMIT;
-- 告知函投递失败 CONFIRM_MAIL_FAIL：不回滚释放，可手动重发（失败中心）
```
- 后台**不提供直接修改/删除预约入口**；仅"锁定已约时段触发取消"这一受审计操作（SRS §7/§3.7）。

---

## 5. SSE 多实例一致性与断线全量恢复

### 5.1 一致性与有序传播（SRS §4.3）
- **中心化事件总线**：所有实例在提交写事务后，发布领域事件到 **Redis Pub/Sub**（频道如 `slot.updated` / `appointment.created` / `appointment.cancelled` / `appointment.rescheduled`）。每个 API 实例订阅频道，向本实例持有的 SSE 连接广播 → 保证**多实例下事件一致、有序到达**（SRS §4.3「多实例部署时事件传播必须保证一致性与有序恢复」）。
- 推送内容 ≤2s 到达客户端（SRS §4.3，§5.1）。

### 5.2 断线全量恢复（降级）
- 客户端 SSE 断线 → **重连先拉快照**：`GET /slots`（当前窗口网格状态快照）+ `GET /appointments/me`；再建立 SSE 增量流。保证断线期间变更不丢（全量快照 + 增量）。
- 降级路径（SRS §5.4）：SSE 不可用 → 轮询降级（UC-07 4a）；前端定时回拉快照。

### 5.3 连接约束
- 同账号 SSE 并发 ≤2（SRS §5.6）；断线重连指数退避；服务端维护每连接订阅的频道。

---

## 6. 通知可靠性：Outbox / 重试 / 死信 / 退信回写 / 人工重发

### 6.1 Outbox 模式（SRS §3.8/§4.3，领域模型 §6.11/§6.12）
- 业务事件写入 `NotificationEvent`（带唯一 `idempotency_key`）；异步消费者按通道创建 `NotificationDelivery`（通用 `DeliveryStatus` + 通道元数据 JSONB）。
- 每事件幂等；每通道每次尝试一条 `NotificationDelivery`；唯一索引 `uq_delivery_attempt(event_id, channel, event_version, attempt_no)` 防并发重复尝试。

### 6.2 重试与死信
- 投递失败 → `retry_scheduled` + `next_retry_at`（指数退避，**≤3 次**）；仍失败 → `dead_letter` + 独立告警（SRS §4.3，§3.8 失败矩阵）。
- **通道独立重试，不相互兜底**（SRS §3.8/§4.3，MVP 硬规则）：飞书失败→重试飞书+邮件告警；邮箱失败→重试邮件+飞书告警；均失败→后台高优先级告警持续重试。

### 6.3 退信(Bounce) 回写（SRS §3.8/§4.3，领域模型 §5/§6.12）
- 邮件通道 SMTP 接受后被退回 → **Bounce Webhook/定时拉取**匹配 `provider_message_id`/`event_version` → 更新对应 `NotificationDelivery.channel_metadata.bounced_at` / `bounce_reason`。
- 退信**仅邮件通道元数据**，不改变通用 `DeliveryStatus` 枚举（§6.2）；触发飞书候选人告警 + 后台高优先级告警；**不回滚业务预约**（与 `CONFIRM_MAIL_FAIL` 一致）。

### 6.4 人工重发（SRS §3.8/§3.9，领域模型 §6.12）
- 失败中心手动重发 = **新建 `NotificationDelivery` 尝试记录**（`attempt_no`+1，幂等键含新 `event_version`，version+1）；受 `uq_delivery_attempt` 约束防重复。
- 限频：同账号每 10 分钟≤5、每小时≤20（SRS §5.6，UC-21）。

### 6.5 提醒随生命周期（领域模型 §6.11）
- 改期/取消时旧 `reminder_due` 事件置 `cancelled`（填 `cancelled_at`）；可经 `superseded_by_event_id` 指向新事件，确保不重复/不漏发。

---

## 7. 知识库热更新与索引原子切换

### 7.1 版本化索引（SRS §3.2 R24，领域模型 §6.14）
- 上传/删除 → 创建 `KnowledgeIndexVersion`（状态 `building`）；切片+嵌入构建向量。
- 完成后置 `ready` 并**原子切换** `active_index_version_id`；旧索引继续服务至切换完成（无服务中断）。
- 删除 → `retrieval_disabled_at` **立即置位**（禁止命中）；旧索引继续服务至切换（SRS §3.2 热更新边界）。

### 7.2 分档 SLA（SRS §5.1）
- 纯文本 P95≤60s / 扫描不可复制 PDF P95≤120s / OCR PDF 异步 P95≤5min / 删除 P95≤5s。
- 索引失败 → 回滚旧索引继续服务（`INDEX_FAIL`，SRS §3.2）。

### 7.3 RAG 检索质量（SRS §3.2）
- 检索不到明确告知"资料未涵盖"不编造；冲突以最新/权威源为准；注入拦截率=100%；删除后相关缓存答案失效；合理推断须标注"推测"。

---

## 8. 腾讯云部署 / 备份恢复 / 日志监控 / 故障降级

### 8.1 部署拓扑（SRS §2.3/§5.7）
- **单 Region 腾讯云**（面试期 1–2 月短期）：云数据库 PostgreSQL（主备）+ Redis 内存版 + 向量库（pgvector 扩展或腾讯云向量数据库）+ 对象存储（静态前端/知识库文件）+ 应用容器/CVM。
- 应用**无状态**：会话存 Redis/DB（记住我令牌哈希）；支持水平扩容多副本（SSE Hub 经 Redis Pub/Sub 协同）。

### 8.2 备份与恢复（SRS §5.5）
- 数据库每日自动**加密**备份；**RPO ≤ 24h，RTO ≤ 4h**；至少每月一次恢复演练。
- 向量索引随文档版本可重建；知识库文件存对象存储多副本。

### 8.3 日志与监控（SRS §5.2/§5.4）
- 集中日志（脱敏：会议号/电话写入前脱敏，SRS §6.3）；健康检查端点；指标：SSE 延迟、通知成功率/死信率、限频触发、RAG 首字延迟。
- 凭证（SMTP/飞书/LLM）存 **Secret Manager**，不进代码/前端/日志（SRS §5.2，PRD §8.7）。

### 8.4 故障降级（SRS §5.4）
- SSE 断线 → 重拉快照/轮询降级（§5.2）。
- 飞书/邮件失败 → 失败通道独立重试告警，**不切换其他通道**（不互为兜底）。
- 模型不可用 → `MODEL_UNAVAILABLE`，不切换第二模型、不编造（SRS §3.2/§4.2）。
- 上线后 SLO：月度可用性 ≥ 99.5%（SRS §5.4）。

---

## 9. 需要独立裁定的 ADR 清单（proposed，待 ratification）

> 以下为**建议 ADR**，须在架构 approved 前或安全/接口阶段由独立裁定（用户或评审）。本文档**不自行裁定**。

| ADR | 议题 | 候选方案 | 约束/备注 |
|-----|------|----------|-----------|
| ADR-ARCH-001 | 部署形态 | 轻量 CVM+Docker Compose vs 容器服务 TKE vs Cloud Studio | 短期 1–2 月；成本 SRS §5.7（¥130–220） |
| ADR-ARCH-002 | 向量库选型 | pgvector 扩展 vs 腾讯云向量数据库 | 与 PostgreSQL 同栈优先 pgvector 降运维 |
| ADR-ARCH-003 | SSE 广播机制 | Redis Pub/Sub（中心化）vs 其他 | 满足多实例一致+有序（§4.3） |
| ADR-ARCH-004 | Outbox 消费模式 | 定时轮询 pending vs PostgreSQL CDC（Logical Replication） | CDC 近实时但增运维；轮询简单 |
| ADR-ARCH-005 | **密码哈希算法** | **不在本阶段裁定** | 留《安全设计》ADR；若与 PRD §8.7 BCrypt 不一致须先走 Change Request（SRS §6.3） |
| ADR-ARCH-006 | 退信接入方式 | 服务商 bounce webhook vs 定时拉取 | 影响 Bounce Webhook 实现（§6.3） |
| ADR-ARCH-007 | 会话存储与记住我 | Redis（哈希令牌）vs DB | 无状态扩容；令牌哈希+失效（SRS §5.2） |
| ADR-ARCH-008 | 限频实现 | Redis 令牌桶 vs 网关中间件 | 阈值 SRS §5.6 |

---

## 10. 开放问题与遗留裁定（不得在本阶段解决）

### 10.1 AUTH_EXPIRED 语义冲突（**OpenAPI 设计前必须裁定**）
- **冲突事实**：SRS §8 错误码表定义 `AUTH_EXPIRED` = **登录过期**（处理=重新登录）；但 SRS §3.3 异常流将限频提示写为 `AUTH_EXPIRED`/`EMAIL_UNVERIFIED`，即把 `AUTH_EXPIRED` 关联到了限频场景。
- **本阶段处理**：架构**不裁定、不新增错误码、不修改 SRS**。该冲突登记为「**OpenAPI 设计前必须裁定**」开放项 —— 须在《接口契约》阶段由 Change Request 明确（要么 §3.3 限频改用语、要么 §8 增补限频错误码），裁定完成前不得据此实现登录/限频错误映射。
- **架构影响**：登录鉴权失败统一走 `AUTH_EXPIRED`（仅会话过期）；凭证错误与限频按普通错误提示呈现（与 UI 线框 v1.0 U4 一致），待 OpenAPI 裁定后定码。

### 10.2 其他待定（不阻塞架构 review）
- 退信 webhook 具体接入（ADR-ARCH-006）。
- 飞书多维表格具体字段映射（留《接口契约》）。

---

## 11. 与基线/下游关系

- 本文档 based_on SRS v1.1 / 领域模型 v1.1.4 / UI 线框 v1.0（均 approved）。
- 密码哈希算法**显式不在本阶段选择**，留《安全设计》ADR（SRS §6.3 冲突升级条款）。
- 下游：《安全设计》→《接口契约（OpenAPI/SSE）》→《测试计划》→ 开发准入评审。
- 本文档 approved 前，下游接口契约不得据此锁定物理端点；SRS §8 错误码表为唯一权威。

---

> **文档结束** · 架构 v0.1（review 草案） · based_on SRS v1.1 / 领域模型 v1.1.4 / UI 线框 v1.0 · 待用户独立评审批准。
