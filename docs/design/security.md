# 安全设计与 ADR（review 草案 v0.1）

> 状态：`review`。依据 PRD 2.3.3 / SRS 1.2 / domain-model 1.1.5 / architecture 0.2（均 approved）。本轮仅完成 SRS v1.2 文字级 impact review；待批准锚点提交后约束实现。

## 1. 安全目标与信任边界

保护对象：账号与会话、预约 PII、候选人联系方式、SMTP/飞书/LLM 凭证、知识库原文与向量、通知回执、审计日志。公网输入包括浏览器请求、SSE 连接、知识库上传内容、LLM 输入输出及退信邮件。任何外部输入均不可信。

核心原则：默认拒绝、最小权限、服务端重新校验、密钥不入 Git/前端/日志、敏感字段按用途解密、外部通知与 LLM 不进入预约数据库事务、大模型不得调用预约写工具。

## 2. ADR-SEC-001 密码哈希

**推荐：BCrypt，cost=12 作为初始值，上线环境以单次校验 P95 100-300ms 校准，最低不得低于 12。**

- 与 PRD §8.7 的 BCrypt 一致，不触发 Change Request；只存 `User.password_hash`。
- 密码按 UTF-8 字节处理；接受长度 10-72 bytes，超过 72 bytes 明确拒绝，禁止静默截断；不设置易被预测的复杂度组合规则，拒绝常见泄露密码的能力留后续增强，不调用外部密码服务。
- 登录使用恒定路径校验；不存在账号时使用固定 dummy hash，降低账号枚举与时序差异。
- 密码重置成功后吊销该用户全部 `AuthSession`，验证码/重置 token 单次消费。
- 重裁触发：PRD 经 Change Request 改用其他算法，或上线压测证明 cost=12 超出接口预算。

## 3. ADR-SEC-002 会话与浏览器防护

**推荐：服务端不透明会话，PostgreSQL `AuthSession` 为唯一真相源；浏览器仅持有 256-bit 随机 session token，数据库只存 SHA-256(token)；不使用自包含 JWT。**

- 普通会话 12 小时；勾选“记住我”时 14 天。登录成功、密码重置、主动退出和后台吊销均更新/撤销 AuthSession。
- Cookie：`HttpOnly; Secure; SameSite=Lax; Path=/`，生产环境不允许 JavaScript 读取；登录后旋转 token，防 session fixation。
- 写接口同时校验 Cookie 会话、`Origin`/`Referer` 同源和 CSRF token；GET/HEAD 不产生业务写入。
- CORS 生产环境只允许正式站点 origin，不允许 `*` 与凭证并用。代理层强制 HTTPS、HSTS、合理 CSP、`X-Content-Type-Options: nosniff`、`Referrer-Policy: strict-origin-when-cross-origin`。
- 面试官与 owner_admin 按 `User.role` 服务端鉴权；前端隐藏按钮不构成授权。owner_admin 不能预约，interviewer 不能访问 admin API。
- AuthSession 查询可做短 TTL 缓存，但撤销真相仍在 PostgreSQL；MVP 默认不缓存，避免额外一致性面。

## 4. ADR-SEC-003 限频

**推荐：Redis 原子计数/滑动窗口，键仅含 HMAC 后的账号标识或截断 IP，不存邮箱明文；应用进程内存不得作为真相源。**

- 严格执行 SRS §5.6 已批准阈值：注册、验证码、登录、预约、手动重发、问答、SSE 分别独立命名空间。
- Redis 使用私网、ACL、TLS（托管服务支持时）和独立随机密码；禁止公网暴露。计数 TTL 等于窗口长度并附少量抖动。
- Redis 不存会话、PII、预约或通知业务真相。故障策略：登录/验证码/注册/密码找回/手动重发/预约写入 **fail closed**；公开只读页面继续；公开问答降级为更严格的单实例临时保护并告警，但不得声称满足正式限频门禁；SSE 新连接拒绝、既有连接可维持。
- 重裁触发：不允许部署 Redis 时，必须先扩领域模型定义持久限频结构并重新评审，不得临时改用进程内计数。

## 5. ADR-SEC-004 退信接入

**推荐：MVP 使用专用邮箱的 IMAP over TLS 定时拉取 DSN/退信邮件，不开放公网 Webhook。**

- 理由：当前邮件通道是 SMTP，尚无已确认支持签名 Webhook 的服务商；IMAP 拉取减少公网入口与验签依赖，适合单站点低量场景。
- 仅访问专用退信邮箱文件夹；凭证进入 Secret Manager；最小权限、TLS 证书校验、连接/读取超时、固定轮询周期 60s。
- 解析前限制邮件大小、MIME 层数和附件；只接受标准 DSN 或可验证的退信格式。提取原始 `Message-ID/provider_message_id`，仅匹配既有 `channel=email` 投递；未知、重复或歧义消息不创建记录，只审计和告警。
- 幂等更新只写 `channel_metadata.bounced_at/bounce_reason`，不得改变 DeliveryStatus、预约或事件状态。
- 若最终邮件服务商提供签名 Webhook，可在重新评审后切换；届时必须定义原始 body 验签、防重放时间窗、事件 ID 去重、来源限制和双密钥轮换。

## 6. 字段加密、指纹与密钥

- AES 字段统一使用 **AES-256-GCM**。每次加密生成 96-bit 随机 nonce；密文列保存版本化 envelope：`version | key_id | nonce | ciphertext | tag`，无需新增数据库列。
- AAD 至少绑定 `table + column + record_id`，防止密文跨字段/记录替换。解密认证失败必须拒绝并告警，不返回部分明文。
- 公司归一化名称指纹使用独立 HMAC-SHA256 key；不得复用 AES key、Cookie secret 或外部服务凭证。
- 主密钥只在 Secret Manager/运行时环境注入，仓库只保留变量名。生产、测试、本地环境完全隔离；轮换周期不超过 90 天。
- 轮换采用 `key_id` 双读单写：新写只用当前 key，读取兼容当前与上一版本，后台受控重加密；完成后撤销旧 key。密钥材料不得写日志、错误响应、备份说明或任务证据。
- 备份加密，恢复演练使用隔离凭证；导出、日志和审计只记录脱敏标识。

## 7. Token、验证码与账号枚举

- 邮箱验证/密码重置 token 使用至少 256-bit CSPRNG，数据库只存 SHA-256 hash；10 分钟过期、单次消费、最多 5 次错误，成功后原子置 `consumed_at`。
- 注册、登录、找回统一使用模糊响应，避免泄露邮箱是否存在；内部审计可区分原因，外部响应不得包含用户 ID、hash 或栈信息。
- 所有认证失败记录结构化安全事件；日志只保留 HMAC 后账号标识、请求 ID、结果类别和截断 IP。

## 8. 授权与数据最小化

- 对象级授权必须校验资源归属：interviewer 只能访问自己的预约、会话和可公开 Slot；owner_admin 才能访问管理能力。
- 红格对非拥有者只返回“已预约/不可约”和必要版本，不返回公司、会议号、联系人、备注或 appointment_id。
- 敏感字段只在确认函渲染、本人预约详情、飞书同步和 owner 只读应急视图的受控路径解密；解密结果不缓存、不写日志。
- owner 强制取消、去重例外、手动重发、知识库删除、密钥/配置变更必须写脱敏 AuditLog。

## 9. LLM、RAG 与文件上传

- 系统提示词和检索资料均视为数据；知识库中的“指令”不得改变系统规则、调用工具或泄露其他资料。问答 agent **仅注册白名单工具**：`search_knowledge`（只读检索）与预约工具 `request_interview_booking` / `list_my_appointments` / `cancel_appointment` / `reschedule_appointment`（后者经 `TASK-CR-AIQA-BOOKING-001` 与 `TASK-AIQA-AGENT-CRUD-001` 批准登记）；所有写工具复用 `BookingService` 并强制 RBAC：面试官仅本人预约、owner_admin 可经 `admin_*` 旁路管理他人，无白名单外工具、无越权路径。模型不生成除白名单工具外的任何调用。
- 发送给 DeepSeek 的上下文执行最小化：只发回答所需片段，不发送密码、token、密钥、完整预约 PII 或后台数据。
- 输出经范围/引用检查；资料未覆盖时明确说明，模型不可用时返回既有 `MODEL_UNAVAILABLE`。
- 上传采用扩展名、MIME 与文件签名联合校验；单文件≤10MB、单次≤20；文件名净化、对象存储随机 key、禁止路径穿越和可执行内容。解析/OCR 运行在资源受限进程，设置页数、解压大小、CPU 和超时上限。
- 删除知识文档立即置 `retrieval_disabled_at`，检索路径先校验禁用状态；缓存答案同步失效。

## 10. 退信、通知与外部集成

- SMTP、IMAP、飞书和 DeepSeek 凭证均独立、最小权限、可轮换；网络调用设置连接/读取超时，不在数据库事务内执行。
- 通知日志不得记录收件人明文、正文、验证码、授权码或完整第三方响应；只记录投递 ID、目的、通道、状态、脱敏错误类别和 provider_message_id 的摘要。
- 至少一次投递允许“外部成功、DB 未提交”导致的重复邮件；稳定幂等键与 Message-ID 尽量去重，不能把“绝不重复”写成保证。

## 11. 安全日志、监控与事件响应

- 监控：认证失败突增、限频拒绝、权限拒绝、解密失败、退信未知匹配、迟到 Worker、死信、Prompt Injection、上传解析失败。
- 安全日志与业务日志分离访问；禁止记录 Cookie、Authorization、token、密码、验证码、AES/HMAC key、SMTP/飞书/LLM secret 和敏感正文。
- 告警分级：密钥泄露/越权/批量解密失败为 P0，立即吊销凭证并隔离；认证攻击/退信异常为 P1；普通外部超时为 P2。

## 12. 下游强制验收

OpenAPI 必须明确 Cookie/CSRF、401/403/429、对象级授权、统一错误体、SSE 认证与断线恢复；不得继续复用 `AUTH_EXPIRED` 表达限频。测试计划必须覆盖 BCrypt 72-byte 边界、会话旋转/吊销、CSRF/CORS、RBAC/IDOR、AES-GCM 篡改、Redis 故障策略、验证码原子消费、IMAP 退信解析与幂等、Prompt Injection、上传炸弹、日志脱敏和密钥扫描。

## 13. 待人工批准与上线输入

正式实施前需用户批准本安全设计，尤其是：BCrypt cost、Redis 限频依赖、IMAP 退信方式、会话/Cookie 策略、AES-256-GCM envelope 与密钥轮换。上线仍需 SMTP/IMAP 账号、域名/备案、飞书授权、DeepSeek key 和腾讯云资源；任何付款或不可逆操作另行确认。
