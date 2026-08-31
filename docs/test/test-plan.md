# 测试计划 v1.4（approved）

> based_on：SRS 1.9 / domain-model 1.1.8 / UI 1.0.3 / architecture 0.6 / security 0.5 / OpenAPI-SSE 1.0（均 approved）。TC 总数为 78；v1.4 仅完成 Litchi `project_key` 契约追认的 impact review，不改变任何冻结断言、真实依赖级别或阈值。

## 1. 证据等级与门禁

- L1 静态：lint、typecheck、契约解析、迁移 SQL 审查。
- L2 单元：纯函数、策略、状态机、加密 envelope、解析器。
- L3 集成：真实 PostgreSQL/pgvector/Redis，本地 SMTP/IMAP/飞书/LLM 使用协议级替身。
- L4 端到端：浏览器 + API + DB + Worker 完整流程。
- L5 staging：真实云配置、HTTPS、Secret、备份恢复、外部集成。
- L6 production：上线 smoke、监控和回滚证据。

任何 L1-L4 结果不得表述为 staging/production 证据。冻结 TC 的断言、阈值和真实依赖级别不得在实现任务中降低、skip 或改成纯 mock。

## 2. 冻结验收用例

### 2.1 页面与项目展示

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-UI-001 | R1/R6 | 1280×720 下三页面导航、页面 1/2 左内容右问答，无重叠；<1024px 显示阻断提示 |
| TC-UI-002 | R15/R25 | 简历下载成功/失败提示；页面 1/2 正文可选择复制 |
| TC-UI-003 | R1/R6 | 页面二展示 Jianli、Sleep、Litchi 三项目且可切换；每个项目均展示核心价值主卡、工程/可靠性过程板块和版本化证据板块；动效不阻断阅读，证据标签区分本地/模拟/未验证 |
| TC-UI-004 | R16 | 他人红格只显示“已预约/不可约”，DOM、网络响应和可访问名称均无 PII |
| TC-UI-005 | UI U3/U7 | 7×25 网格；选择连续三格后冲突校验通过直接进入二次确认 |
| TC-UI-006 | UI U3/A4 | 预约/改期加载 offset 0/1/2 并裁剪为明天起 15 日；无历史日期；预约页铺满主内容区且关键日历文字≥12px；owner_admin 可读同一隐私安全快照，点击格子带入精确 Slot 时间段并设置不可约，面试官窗口同步生效 |

### 2.2 RAG、Persona 与会话

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-AI-001 | R2 | 八类题库每类≥20题，范围内命中率≥90% |
| TC-AI-002 | R2/R3/R7 | 页面 1/2 的公开问答可用；越界拒答率≥95%，第一人称且不编造 |
| TC-AI-003 | R2 | Prompt Injection 攻击集拦截率=100%，零工具写调用 |
| TC-AI-004 | R2 | 无检索证据明确“资料未涵盖”，事实编造零容忍 |
| TC-AI-005 | R7 | Persona 盲评≥20题、≥3评审、通过率≥80% |
| TC-AI-006 | R4 | 推荐问题读缓存；缓存缺失使用固定兜底，不实时调用模型 |
| TC-AI-007 | R23 | 登录用户会话跨登录可见；匿名问答不持久化 |
| TC-AI-008 | R24 | 文档更新原子切索引；删除≤5s禁检索；索引失败旧版本继续服务 |
| TC-AI-009 | SRS §3.2 | DeepSeek 不可用返回 MODEL_UNAVAILABLE，不切第二模型、不生成无依据回答 |
| TC-AI-010 | SRS §3.1/§3.2 / UI U2 | jianli Agent Lab 四类场景调用真实问答；`answer.trace.step` 单调、字段严格白名单、无用户原文/Prompt/知识原文/工具完整结果/预约 PII；历史消息无 Trace 正常展示 |
| TC-AI-011 | SRS §3.1/§3.2 / UI U2 | jianli 评测证据板读取版本化报告，展示各套件通过数/样本数、验证时间/commit、CI 门禁与脱敏失败分类；报告≤50KB 且不含问题原文、完整回答、Prompt、知识原文、PII/密钥；GitHub Actions push/PR 硬门禁失败返回非零 |
| TC-AI-012 | architecture §8.3 / ADR-RERANK-001 | RRF 候选可经 Cross-Encoder 重排取 top6；未配置零外调，超时/429/5xx/畸形响应/索引越界均回退原顺序；只向 provider 发送域过滤后的问题与候选；低基数观测与版本化对照报告不含输入正文或密钥 |
| TC-AI-013 | architecture §8.3/§9.4 / ADR-RESILIENCE-001 | Semantic Cache 仅命中匿名 grounded 同域回答，按 TTL/容量限制且知识变更失效；Redis/embedding 故障旁路；LLM/Reranker 熔断器覆盖 closed→open→half-open→closed、恢复窗口与单探针；观测无正文、embedding、Redis key 或高基数 ID |
| TC-AI-014 | architecture §9.4 / ADR-RESILIENCE-001 | 两个进程视角共享 Redis failure/open 状态，恢复窗口通过原子操作只允许一个跨实例 half-open 探针；成功/失败转换与 TTL 正确；Redis 故障退回本地 breaker，LLM 异步调用不被同步 Redis I/O 阻塞 |

### 2.3 认证、会话与限频

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-AUTH-001 | R9/R20 | 注册只创建 interviewer；验证码 10 分钟、单次消费；重发恒 202 防枚举，有效重发使所有旧未消费注册码失效且仅新码可用 |
| TC-AUTH-002 | R9 | 密码登录成功；验证码不能用于登录；账号不存在与错误密码均返回同码同文案的 401 `INVALID_CREDENTIALS` |
| TC-AUTH-003 | R19 | 普通会话 12h、remember_me 14d；Cookie Secure/HttpOnly/SameSite=Lax |
| TC-AUTH-004 | security §2 | BCrypt 10/72-byte 边界；73 bytes 返回 422 `INVALID_REQUEST` Problem 且不回显输入、不静默截断；dummy hash 降低账号枚举 |
| TC-AUTH-005 | R20 | 密码重置后所有 AuthSession 被吊销，旧 Cookie 返回 AUTH_EXPIRED |
| TC-AUTH-006 | SRS §5.6 | 注册与注册验证码重发共享发码限频；登录/预约/通知重发/问答/SSE 各阈值独立，超限统一 RATE_LIMITED + Retry-After |
| TC-AUTH-007 | security §3 | Redis 故障时敏感写 fail closed；公开静态页继续；不以进程内计数冒充正式限频 |
| TC-AUTH-008 | security §2 | 写请求缺失/错误 CSRF 或非同源 Origin 被拒；CORS 不允许通配凭证 |

### 2.4 预约与并发一致性

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-APT-001 | R8/R10/R26 | 三连续格预览→3分钟确认→原子创建；未确认不落库、不占 Slot |
| TC-APT-002 | R10 | 预约事务同时写 Appointment/3 Slot/NotificationEvent/AuditLog；事务内无外部调用 |
| TC-APT-003 | R12 | 两事务抢同一 Slot，仅一个成功，另一个 SLOT_TAKEN；冻结真实 PostgreSQL 集成测试 |
| TC-APT-004 | R11 | 改期锁 Appointment 后合并新旧 Slot 升序加锁，占新/释旧/版本更新/Outbox 原子提交 |
| TC-APT-005 | R11 | 用户取消按 Override+日历重新物化，不无条件 available |
| TC-APT-006 | R14b | owner 强制取消后 Slot=owner_locked，并写审计/取消通知 |
| TC-APT-007 | R12 | 同公司/同账号唯一约束分别返回 DUP_COMPANY/DUP_ACCOUNT |
| TC-APT-008 | UC-22 | CompanyBookingException 并发消费仅一次成功，uq_appointment_exception 兜底 |
| TC-APT-009 | arch §4.7 | 同一 Override 并发 UPDATE/DELETE 串行化并重读真实 old_range |
| TC-APT-010 | arch §4.7 | Override 与改期/取消同范围由 Slot 锁串行化；booked 保持 booked |
| TC-APT-011 | SRS 1.3 | 不存在 Override 返回 OVERRIDE_NOT_FOUND；范围零命中返回 OVERRIDE_RANGE_EMPTY，均回滚 |
| TC-APT-012 | SRS 1.6 | `end_at <= now()` 的 active 预约被幂等自动置 completed 且 completed_at=end_at；不再触发 DUP_ACCOUNT/DUP_COMPANY；未过期预约保持 active；不发送取消通知 |

### 2.5 SSE

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-SSE-001 | R8 | commit-derived 轮询 T=1s，提交后≤2s 到达 |
| TC-SSE-002 | SSE §2 | 先订阅/缓冲/快照水位/重放，不丢快照窗口内变化 |
| TC-SSE-003 | SSE §2 | 断线、漏序、版本跳跃、心跳缺失、server_resync 均强制重拉快照 |
| TC-SSE-004 | R16 | Slot 事件只含 none/self/other，不泄露他人 appointment_id/PII |
| TC-SSE-005 | SRS §5.6 | 同账号第3条连接拒绝 RATE_LIMITED；断开后计数释放 |

### 2.6 Outbox、通知与退信

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-NOTIFY-001 | R13/R26 | appointment_created 同时建候选人 email+feishu 与面试官 confirmation email 三目的投递 |
| TC-NOTIFY-002 | arch §6 | 多 Worker SKIP LOCKED 不重复领取同一行；uq_delivery_attempt 只验证防重复建行 |
| TC-NOTIFY-003 | R21 | 通道独立重试≤3次，失败不影响业务预约，不相互兜底 |
| TC-NOTIFY-004 | arch §6.4 | queued/sending 超时分别记录 queued_lease_expired/sending_lease_expired_unknown |
| TC-NOTIFY-005 | arch §6.4.1 | Sweeper 回收后迟到 Txn W CAS 命中0行，不覆盖 retry/dead_letter，只告警 |
| TC-NOTIFY-006 | arch §6.5 | 外部成功/DB失败的至少一次重复风险可观测；幂等键不含 attempt_no |
| TC-NOTIFY-007 | UC-21 | 手动重发新建 attempt_no+1 且 event_version+1；旧行不改写 |
| TC-NOTIFY-008 | R26 | IMAP DSN 匹配既有 email provider_message_id，幂等写 bounce 元数据，不改 DeliveryStatus/预约 |
| TC-NOTIFY-009 | security §5 | 超大/MIME炸弹/未知/歧义退信拒绝且告警，不创建新记录 |
| TC-NOTIFY-010 | R26 | A6/A7 可按通道、失败状态、退信筛选，退信触发双告警 |
| TC-NOTIFY-011 | R14 | 预约新增/修改/取消近实时同步至飞书完整视图；同步失败写失败记录、邮件告警并按既定策略重试，不回滚预约 |
| TC-NOTIFY-012 | R14/SRS 1.7 | 自动完成事务写唯一 appointment_completed Outbox；Worker 仅建 feishu Delivery 并 upsert 状态=completed，不发送候选人/面试官 email 或飞书私信；0010 up/down/up 通过 |

### 2.7 Admin、知识库与权限

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-ADMIN-001 | SRS §7 | interviewer 访问任一 admin API 返回 PERM_DENIED；owner_admin 不能预约 |
| TC-ADMIN-002 | R14a | Admin 完整预约视图只读，除 force-cancel 外无直接修改/删除入口 |
| TC-ADMIN-003 | R5/R24 | 上传≤20文件、单文件≤10MB；类型/MIME/签名不一致拒绝 |
| TC-ADMIN-004 | security §9 | zip bomb、路径穿越、超页数/CPU/超时解析被隔离拒绝 |
| TC-ADMIN-005 | R5 | 公告、Override、例外、手动重发、知识删除均写脱敏 AuditLog |
| TC-ADMIN-006 | domain §6.1 | 恰有一个 active owner；零 owner 时候选人通知解析失败并运维告警 |

### 2.8 加密、隐私与日志

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-SEC-001 | SRS §5.2 | AES-256-GCM 每次随机 nonce；同明文密文不同；AAD 跨字段替换解密失败 |
| TC-SEC-002 | security §6 | key_id 双读单写轮换；旧 key 撤销前后行为符合方案 |
| TC-SEC-003 | domain §6.5 | 公司归一化 HMAC 去重；HMAC key 与 AES/Cookie key 不复用 |
| TC-SEC-004 | SRS §5.3 | 日志/响应/Trace 无密码、token、Cookie、验证码、密钥、PII、知识正文 |
| TC-SEC-005 | SRS §7 | IDOR：更换 appointment/conversation/document UUID 不能跨用户访问 |
| TC-SEC-006 | security §9 | 原始预约 PII/密钥不得进入 LLM 上下文；检索资料指令不能提升权限 |
| TC-SEC-007 | supply chain | secret scan、依赖高危漏洞扫描、SBOM 生成通过；HIGH/CRITICAL 阻断发布 |

### 2.9 性能、备份与发布

| TC | 覆盖 | 验收 |
|---|---|---|
| TC-PERF-001 | SRS §5.1 | 普通 API P95≤500ms；预约提交 P95≤1.5s；模型正常并发≤20首字 P95≤3s |
| TC-PERF-002 | SRS §5.1 | SMTP 接受 P95≤10s；SSE≤2s；前端选段<100ms |
| TC-PERF-003 | R24 | 文本≤60s、扫描PDF≤120s、OCR PDF≤5min、删除≤5s |
| TC-OPS-001 | SRS §5.5 | 加密备份每日执行；独立环境恢复演练 RPO≤24h/RTO≤4h |
| TC-OPS-002 | migration | 全部 migration up/down 在空库与基线库通过；约束/索引与 domain-model 一致 |
| TC-OPS-003 | deploy | 健康检查、自动重启、SSE/LLM/邮件/飞书/Redis 降级 smoke 通过 |
| TC-OPS-004 | release | 同一不可变制品晋级；健康失败、错误率>2%、P95>2×目标或隐私信号触发回滚 |
| TC-OPS-010 | ADR-OBS-001 / security §11 | `/internal/metrics` 仅启用时存在且 Nginx 公网 404；HTTP/AIQA/token/tool 指标可抓取，标签固定低基数且无 TC-SEC-004 禁止字段；OTLP 未配置 no-op、导出失败不影响回答；Prometheus/Grafana/Collector 配置可解析 |

## 3. 需求覆盖门禁

- R1-R7：TC-UI-001~003、TC-AI-001~009、TC-ADMIN-003~005（R3 明确由 TC-AI-002 覆盖）。
- R8-R12/R16/R17：TC-UI-004~005、TC-APT-001~011、TC-SSE-001~005。
- R13-R14b/R18/R21/R26：TC-NOTIFY-001~011、TC-ADMIN-002（R14 与 R14a 分别覆盖飞书完整视图和后台只读应急视图）。
- R9/R19/R20：TC-AUTH-001~008。
- R22-R25：TC-AI-006~008、TC-ADMIN-003~004、TC-UI-002~003。

任何需求无映射、冻结 TC 失败或被 skip，开发准入/发布门禁均失败。

### 3.1 OpenAPI operationId 覆盖

| operationId | 冻结 TC |
|---|---|
| getPageContent | TC-UI-001 / TC-UI-003 |
| listRecommendedQuestions | TC-AI-006 |
| streamAnswer | TC-AI-002 / TC-AI-003 / TC-AI-009 |
| listConversations / createConversation / listConversationMessages | TC-AI-007 / TC-SEC-005 |
| registerInterviewer / verifyEmail / resendEmailVerification | TC-AUTH-001 / TC-AUTH-006 |
| login / logout / getCurrentUser | TC-AUTH-002 / TC-AUTH-003 / TC-AUTH-008 |
| requestPasswordReset / confirmPasswordReset | TC-AUTH-005 |
| getSlotSnapshot / streamSlotEvents | TC-SSE-001~005 / TC-UI-004 |
| previewAppointment / createAppointment | TC-APT-001~003 |
| listMyAppointments / updateAppointment / cancelAppointment | TC-APT-004~005 / TC-SEC-005 |
| adminListAppointments / forceCancelAppointment | TC-ADMIN-001~002 / TC-APT-006 |
| listAvailabilityOverrides / createAvailabilityOverride / updateAvailabilityOverride / deleteAvailabilityOverride | TC-APT-009~011 / TC-ADMIN-005 |
| listNotificationFailures / resendNotificationDelivery | TC-NOTIFY-007 / TC-NOTIFY-010 / TC-ADMIN-001 |
| listKnowledgeDocuments / uploadKnowledgeDocuments / deleteKnowledgeDocument | TC-ADMIN-003~005 / TC-SEC-005 |
| updateAnnouncement | TC-ADMIN-005 |
| createCompanyBookingException | TC-APT-008 / TC-ADMIN-005 |

映射表中的每个 `operationId` 必须由 OpenAPI contract test 覆盖成功、鉴权、主要业务错误和响应 schema；涉及资源归属的接口额外执行 TC-SEC-005。

## 4. 实现测试分层

- 前端：组件/可访问性 + Playwright 桌面端 E2E + 截图回归。
- API：单元 + OpenAPI contract + PostgreSQL/Redis 集成 + 并发事务测试。
- Worker：fake SMTP/IMAP/Feishu 协议服务 + 崩溃/迟到/CAS 故障注入。
- AI：确定性检索/护栏回归与可选真实 DeepSeek 评测分开报告；真实模型结果不得覆盖确定性门禁。
- 部署：Compose smoke，随后 staging HTTPS/Secret/备份/监控验证。

## 5. 开发准入判定

正式编码前必须满足：baseline 十项全部 approved；SRS/security/OpenAPI/test_plan 的 approval_commit 可解析；OpenAPI 标准 lint 通过；冻结 TC 文件已落地且实现任务禁止修改；DB/API/依赖在任务中逐项列明；独立审查任务已建立。本测试计划 impact review 已通过，待 test_plan 独立批准锚点与开发准入复核。
