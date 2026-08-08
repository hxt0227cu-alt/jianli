# TASK-ARCH-002 架构内容修正：SSE 可靠传播 / 预约事务锁顺序 / Outbox Worker / 退信入口边界

> 架构内容修正任务，承载 architecture.md **v0.1 → v0.2**。本任务**只修会影响一致性、可靠性与安全边界的问题**，不做措辞整理、不处理历史表述、不新建治理任务（TASK-GOV-*）。
> **不批准架构**：`baseline.architecture.status` 保持 `review`；不得进入《安全设计》/《接口契约》/《测试计划》/编码。
> **不扩模型**：若修正方案需要新增领域实体 / 表 / 字段 / 外部依赖 → 立即 Stop & Report，不得自行扩模型。

## 任务类型
- design         # 架构设计内容修正（review 草案升版，不代签 approved）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.4（approved）/ SRS 1.1（approved，行为唯一源）/ UI 线框 1.0（approved）/ AI 治理 1.0.1（均取自 `docs/baseline.yml`）
- 基线 commit：c18c326（TASK-ARCH-001 v0.1 证据回填提交；v0.1 草案快照锚点为 2f73982）

## 精确规范引用（AI 只读取这些章节）
- SRS v1.1：§3.5（预约创建）/ §3.6（改期·取消）/ §3.7（owner 强制取消·去重例外）/ §3.8（通知可靠性·失败矩阵·退信）/ §3.9（失败中心）/ §4.3（SSE 行为·通知可靠性行为·退信）/ §5.1（性能阈值）/ §5.4（可用性·降级）/ §5.6（限频·SSE 并发）/ §6.2（状态模型）/ §7（权限矩阵）/ §8（错误码表，唯一权威）
- 领域模型 v1.1.4：§5（状态机）/ §6.5（Company）/ §6.6（Appointment·部分唯一索引）/ §6.7（AppointmentSlot）/ §6.8（并发抢占行锁）/ §6.9（AvailabilityOverride）/ §6.11（NotificationEvent Outbox）/ §6.12（NotificationDelivery·uq_delivery_attempt）/ §6.15（AuditLog）/ §6.17（CompanyBookingException·uq_appointment_exception）
- UI 线框 v1.0：A6/A7（通知与同步失败中心：投递状态与退信筛选）

## 需求来源
- R8 / R10 / R11 / R12 / R14 / R14b / R18 / R21 / R26；UC-07 / UC-08 / UC-09 / UC-10 / UC-11 / UC-12 / UC-14 / UC-19 / UC-20 / UC-21 / UC-22

## 目标
将 `docs/design/architecture.md` 由 v0.1 修正为 v0.2（仍为 review 草案），完成六项：

1. **修正 SSE 方案**：不得声称 Redis Pub/Sub 自身可靠 / 有序 / 可恢复；消除「DB commit 后 Redis publish」的双写丢事件窗口；定义持久化事件来源或 PostgreSQL CDC / 现有 Outbox relay 方案；每个事件带单调版本 / 序列；明确「先订阅再拉带水位的快照」或等价算法以消除快照与增量之间的竞态；断线、漏序或版本跳跃时强制重拉快照。
2. **重写预约事务**：创建 / 改期 / 用户取消 / owner 强制取消四条流程的加锁对象、加锁顺序、锁后校验、写入序列与同事务 Outbox；明确全流程**统一锁顺序**以避免死锁与改期/取消竞态；`CompanyBookingException` 须在同一事务 `FOR UPDATE` 校验并消费、写 `dedupe_exception_id`、受 `uq_appointment_exception` 保护。
3. **补全 Outbox Worker**：多 Worker 原子领取机制；处理超时后的恢复；明确至少一次投递模型；稳定幂等键 / 服务商幂等能力，处理「外部发送成功、数据库状态提交失败」的重复投递风险；`NotificationEvent` 与 `NotificationDelivery` 状态转换须与 SRS §6.2 / 领域模型 §5 一致。
4. **核心 ADR 给出明确推荐与理由**：部署形态、向量方案（PostgreSQL+pgvector 或独立向量库，只选一个 MVP 主方案）、SSE 可靠传播方案、Outbox 消费方案。
5. **退信（Bounce）回调入口标记为公网不可信入口**：架构层先规定幂等回写、未知消息拒绝、回调不得直接改变预约状态；验签 / 防重放 / 来源校验 / 密钥轮换要求转交《安全设计》。
6. 同步 `tasks/TASK-ARCH-001.md`（登记缺陷与被取代关系，不重写历史证据）、`docs/baseline.yml`（architecture 版本 0.1→0.2，**status 保持 review**）、`PROJECT_STATE.md`。

## 非目标（明确排除）
- **不批准架构**（不得把 `baseline.architecture.status` 改为 approved）。
- **不选择密码哈希算法**（留《安全设计》ADR；若与 PRD §8.7 BCrypt 不一致须先走 Change Request）。
- **不预先假定退信接入方式、会话存储介质、限频实现**——三者留《安全设计》裁定，架构正文只写不依赖具体实现的边界约束。
- 不修改 SRS / PRD / 用例规约 / 领域模型 / UI 线框业务内容；不新增、不修改错误码（SRS §8 为唯一权威）。
- 不定义 REST URL / 请求响应 Schema / SSE 事件载荷字段（留《接口契约》）。
- 不新建 TASK-GOV-*；不处理历史措辞；不重写既有 commit 与既有交付证据。
- 不写任何代码、迁移脚本；不进入安全设计 / OpenAPI / 测试计划 / 编码。

## 允许修改路径
- docs/design/architecture.md        # 主交付物：v0.1 → v0.2
- tasks/TASK-ARCH-002.md             # 本任务单自身（含证据回填）
- tasks/TASK-ARCH-001.md             # 追加缺陷登记与被取代关系（只追加，不改写历史证据）
- docs/baseline.yml                  # architecture.version 0.1→0.2；status 保持 review
- PROJECT_STATE.md                   # 同步架构阶段任务态

## 禁止修改路径
- docs/requirements/PRD.md / use-cases.md / SRS.md
- docs/design/domain-model.md / ui-wireframe.md
- 其他 tasks/TASK-*.md（除 ARCH-001 / ARCH-002）
- 任何代码文件、数据库迁移脚本、OpenAPI / SSE 契约文件
- 安全设计 / 测试计划 工件

## 已批准的 DB / API / 依赖变更
- **无**。本任务全部方案**只使用领域模型 v1.1.4 已批准的实体、字段与索引**：
  - `AppointmentSlot.version` / `Appointment.version`（§6.6/§6.7 既有乐观锁列）作为 SSE 的单调资源版本；
  - `NotificationDelivery.status` + `created_at` + `uq_delivery_attempt`（§6.12）作为 Outbox 的隐式租约与跨 Worker 互斥；
  - `CompanyBookingException` + `uq_appointment_exception`（§6.17）作为例外一次性消费保护。
- **未新增**任何领域实体 / 表 / 字段 / 索引 / 外部依赖 → **未触发 Stop & Report**。
- 已识别但**明确不采纳**的扩模型方案（若将来采纳必须先走 Change Request 改领域模型，不得在实现阶段引入）：新增持久化事件日志表（全局 `bigserial` 序列）、`AppointmentSlot.updated_at` 增量列、`NotificationEvent` 租约列、PostgreSQL 逻辑复制槽（CDC）。

## 规范影响评估（spec impact）
- behavior_change：**false**（架构层设计修正，不改变 SRS 定义的用户可观察行为）
- affected_specs：
  - srs：none —— SSE 行为（事件带版本/序列、断线重拉全量快照、丢失事件经全量刷新恢复、多实例一致有序、≤2s）与通知可靠性行为（Outbox / ≤3 次退避 / 不互为兜底 / 手动重发 / 退信不改 `DeliveryStatus`）均为 SRS v1.1 §4.3/§6.2 **已批准**内容，本次仅在架构层选择满足这些行为的机制。
  - domain_model：none —— 未新增实体/字段/索引，全部落在 v1.1.4 已批准范围内。
  - openapi：none（尚未产出；本文不定义 URL / 载荷字段）
  - security：none —— 退信验签 / 防重放 / 来源校验 / 密钥轮换、会话存储、限频实现均**转交**《安全设计》，本文不预设实现。
  - test_plan：none（尚未产出；已在正文登记须由测试计划覆盖的残留重复风险）
- reason：架构机制选择属设计层决策，未改变任何已批准规范定义的对外行为，也未越界扩展领域模型。

## 功能验收
- **SSE**：正文不出现「Redis Pub/Sub 保证可靠/有序/可恢复」类表述；事件来源为已提交的数据库状态，不存在 commit 与 publish 的双写窗口；每个事件带单调资源版本 + 连接级连续序号；给出「先订阅 → 缓冲 → 拉快照 → 按版本重放」的竞态消除算法；断线 / 漏序 / 版本跳跃 / 心跳缺失 / 服务端 resync 五类触发强制重拉快照；满足 SRS §4.3 与 §5.1（≤2s）。
- **事务**：给出唯一全局锁顺序（Company → Appointment → CompanyBookingException → AppointmentSlot 按 start_at 升序）；四条流程均"先加锁后校验"，`FOR UPDATE` 不带 status 过滤；创建校验数量/同日/连续性/available；例外在同一事务 `FOR UPDATE` 校验并消费并写 `dedupe_exception_id`；改期先锁 Appointment 校验 active/归属/version，再合并新旧 Slot 统一升序加锁，占新、释旧（按 §4.6 重新物化）、更新 Appointment、撤销旧提醒、写新 Outbox 同事务；用户取消释放格按 §4.6 重新物化（不再无条件 available）；owner 强制取消写 `owner_locked`；两流程均写通知事件（owner 另写 AuditLog）；`AvailabilityOverride` 创建/修改/删除事务须锁受影响 Slot 并重新物化（§4.7）。
- **Outbox**：事件级原子领取（`FOR UPDATE SKIP LOCKED` + `uq_delivery_attempt` 二重互斥，仅防重复建行）；**新增投递级原子领取**（§6.3.2：`NotificationDelivery` `queued→sending` 短事务 `FOR UPDATE SKIP LOCKED` + RETURNING，提交后才调外部，`uq_delivery_attempt` 不防同一行重复发送）；隐式租约（非终态 + `created_at`，5min）超时回收，且**区分 `queued`（未发送，`queued_lease_expired`）/ `sending`（结果未知，`sending_lease_expired_unknown`）两类超时与不同 `last_error`**，外部调用超时须远小于 5min；明确至少一次语义；稳定幂等键**不含 attempt_no**、手动重发经 `event_version` 有意区分；`NotificationEvent`/`NotificationDelivery` 状态转换逐条对齐 SRS §6.2 与领域模型 §5，不新增状态。
- **ADR**：部署形态 / 向量方案 / SSE 传播 / Outbox 消费四项各给出**唯一推荐 + 理由 + 重裁触发条件**；向量方案只选一个 MVP 主方案，不并存。
- **退信入口**：标记为公网不可信入口；架构层规定幂等回写、未知消息拒绝、回调不得直接改变预约状态与 `DeliveryStatus`；验签/防重放/来源校验/密钥轮换列为《安全设计》必答项。
- **不批准**：`docs/baseline.yml` 中 `architecture.status` 仍为 `review`。

## 安全与隐私验收
- 退信回调按公网不可信输入处理：匹配不到既有投递记录一律拒绝，不创建任何记录、不改预约状态、不改 `DeliveryStatus`；仅写 `channel_metadata.bounced_at`/`bounce_reason`，重复回调幂等。
- 正文不假定会话存储介质与限频实现，仅保留"应用进程不得在本地内存持有会话/限频状态"的无状态约束。
- 密码哈希算法未裁定；敏感字段 AES-256 / 密钥 Secret Manager / 日志脱敏表述与 SRS §5.2/§6.3 一致，不新增策略。

## 性能验收
- SSE 传播 ≤2s（SRS §5.1）：轮询周期 T=1s + 推送，留足余量；给出窗口规模（14 天 × 25 行 ≈ 350 行）与升级触发阈值。
- 预约提交 P95 ≤1.5s（SRS §5.1）：事务内禁止任何外部调用（SMTP/飞书/LLM），仅本地行锁与写入。
- 邮件 P95 ≤10s 提交至 SMTP（SRS §5.1）：租约 5 分钟 > 该阈值，避免误回收。

## 变更预算（change_budget）
- max_files：**5**
  1. docs/design/architecture.md
  2. tasks/TASK-ARCH-002.md
  3. tasks/TASK-ARCH-001.md
  4. docs/baseline.yml
  5. PROJECT_STATE.md
- expected_prod_lines：0（设计任务，无生产代码）
- expected_test_lines：0

## 必须运行的测试命令
- 无自动化测试（设计任务）。交付前执行一致性校验：
  1. `grep` 校验 architecture.md 不再出现「Redis Pub/Sub …保证…一致、有序」类表述；
  2. 逐条比对 §6 状态转换表与 SRS §6.2 / 领域模型 §5 枚举，确认无新增状态；
  3. 逐条比对 §4 事务用到的表/列/索引与领域模型 §6.5–§6.17，确认无新增结构；
  4. 确认 `docs/baseline.yml` 中 `architecture.status` 仍为 `review`。

## 回滚方法
- `git revert` 本任务提交；本任务不产生迁移、不产生代码。

## 强制停止条件（与 `AGENTS.md §2` 一致）
判定口径：**看变更是否已在本任务单「允许修改路径」与「已批准的 DB / API / 依赖变更」列明，而不是看变更类型本身。**
- **可继续**：变更已列明且为设计性质，依据工件（SRS v1.1 / 领域模型 v1.1.4 / UI 线框 v1.0）在 `docs/baseline.yml` 为 `approved`。
- **必须立即停止并报告**：出现任何未列明的变化，包括——SSE / Outbox / 事务方案需要**新增领域实体、表、字段、索引或外部依赖**；新增或修改公开 API / SSE 契约字段；自行新增或修改错误码；自行选择密码哈希算法；预设退信接入方式 / 会话存储 / 限频实现；修改 SRS 等已批准规范的业务内容；把 `architecture.status` 改为 `approved`。
- **其余硬停条件**：超出 `change_budget.max_files`（5）→ 拆任务。

## 交付证据（review 草案升版，**不关闭**）
- commit / PR：ef671228c02b3c099e8b17c2026eb6de9d3fa5dd（G1 快照，v0.2 初版 review）
- 补充修正（2026-08-09 三项实现正确性）：1e0d9ed（docs/design/architecture.md 单文件；§6.3.2 投递级原子领取 + §6.3 澄清 uq_delivery_attempt 边界 + §4.6/§4.7 Slot 释放重新物化 + §6.4 两类超时区分 + 删除 §13；仍 review 不批准）
- 修改文件清单（G1 初版）：docs/design/architecture.md / tasks/TASK-ARCH-002.md / tasks/TASK-ARCH-001.md / docs/baseline.yml / PROJECT_STATE.md（5 个路径，与「允许修改路径」逐一对照一致）；本轮补充修正（1e0d9ed）仅 docs/design/architecture.md 1 个路径。
- 测试命令及结果：
  1. `grep "Redis" architecture.md` → 仅出现「MVP SSE 路径不使用消息中间件」与「v0.1 错误记录」两处表述，无「Redis 保证一致/有序/可恢复」类断言（pass）；
  2. 逐条比对 §6 状态转换表与 SRS §6.2 / 领域模型 §5/§6.11：NotificationEvent=`pending/processing/processed/cancelled/failed`、NotificationDelivery=`queued/sending/succeeded/failed/retry_scheduled/dead_letter`、退信仅入 `channel_metadata`，无新增状态（pass）；
  3. 逐条比对 §4 事务用到的表/列/索引（Company / Appointment / CompanyBookingException / AppointmentSlot + 既有索引 uq_active_company / uq_appointment_exception / uq_delivery_attempt）与领域模型 §6.5–§6.17，无新增结构（pass）；
  4. `grep "architecture:" baseline.yml` → `version: "0.2", status: review`，未变为 approved（pass）。
- 5. `grep -n "worker_lease_expired" architecture.md` → 无匹配（已被 `queued_lease_expired` / `sending_lease_expired_unknown` 取代，pass）；`grep -n "queued_lease_expired\|sending_lease_expired_unknown" architecture.md` → 均出现（§6.4，pass）。
- lint / typecheck：不适用（设计任务）
- DB 迁移验证：无
- 验收证据：architecture.md v0.2（§1–§12）覆盖六项强制要求：§5 SSE 改 commit-derived 轮询消除双写窗口、§4 统一锁顺序 L0→L3、§6 Outbox `FOR UPDATE SKIP LOCKED`+隐式租约+至少一次、§7 退信入口边界、§10 四项 ADR 唯一推荐；§12 含 16 项 v0.1→v0.2 变更记录；§6.10 模型边界声明（零扩模型）。
- 变更预算实际值：max_files=5，实际 5 文件（architecture.md / TASK-ARCH-002.md / TASK-ARCH-001.md / baseline.yml / PROJECT_STATE.md），未超预算。
- 未解决风险：
  1. **残留重复投递风险（转《测试计划》）**：Outbox 至少一次语义下，若外部发送成功但 `NotificationDelivery` 状态提交失败（进程崩溃/网络分区），服务商侧已发邮件而 DB 未落库 → Sweeper 回收后重发 → 用户可能收到重复邮件。已用稳定幂等键（不含 attempt_no）+ §6.3.2 投递级原子领取（提交后才调外部）+ §6.4 `sending` 超时的「结果未知」口径与告警尽力降低，但不保证跨崩溃端到端去重；须由《测试计划》覆盖重发幂等验证（尤其 `sending_lease_expired_unknown` 场景）与业务可接受性评估。
  2. **开放项待用户裁定**：ADR-005/006/007/008 留《安全设计》；`AUTH_EXPIRED` 语义冲突（SRS §3.3 关联限频 vs §8 定义登录过期）仍留作 OpenAPI 前阻塞项。**§11.2 取消释放目标状态已在本轮裁定并并入 §4.6（按 AvailabilityOverride 与日历规则重新物化），§13 待办已删除，正文与验收一致。**
- 是否偏离 TASK：否（仅做六项强制修正；未处理历史措辞、未建 TASK-GOV-*、未扩模型、未批准架构、未进入下游阶段）。
- 规范影响结论：none（与上方「规范影响评估」一致）
- spec_sync：clean（上游 SRS v1.1 / 领域模型 v1.1.4 / UI 线框 v1.0 均 approved 且 based_on 未变）
- verified_commit：1e0d9ed（2026-08-09 三项实现正确性修正，最新 review 草案快照；仍 review 不批准，非自指）
- **关闭门禁（四条件全满足方可关闭）**：① 测试通过；② 规范影响已处理（none）；③ spec_sync = clean；④ verified_commit 已记录真实 sha。
  **本任务与 TASK-ARCH-001 均保持 review，待用户独立评审批准 architecture v0.2 后方可关闭。AI 不得代签 approved。**

## 关联
- 上游任务：TASK-ARCH-001（产出 v0.1 草案，保持 review；v0.1 已被本任务的 v0.2 取代，v0.1 快照锚点 2f73982 保留为历史）
- Change Request：无（AUTH_EXPIRED 语义冲突、以及将来若采纳 CDC/事件日志表方案，均须另走 Change Request，不得在本任务内裁定）
- 测试任务：无（设计）
