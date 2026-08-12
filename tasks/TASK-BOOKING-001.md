# TASK-BOOKING-001 预约预览与原子创建

## 任务类型
- implementation

## 会话开始上下文

基线：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5
任务：TASK-BOOKING-001
目标：实现预约预览与原子创建，并以真实 PostgreSQL 冻结三格抢占和同事务 Outbox/审计行为。
非目标：改期/取消、SSE、通知投递、SMTP/飞书、生产迁移、部署、Agent 自动预约。
允许修改：预约模块、应用配置与装配、Python 依赖清单、预约测试、当前任务与独立审查证据。
预计变更：最多 18 个文件；生产代码约 750 行；测试代码约 650 行。
验收测试：TC-APT-001～003、TC-SEC-001～004、TC-AUTH-006/008。
输出语言：简体中文。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5；SRS 1.3 / architecture 0.2 / security 0.1 / OpenAPI 0.2 / test_plan 0.2（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`5062c699f1b692ae0571955ec92976b555071c65`
- 前置迁移：DB-002 最终快照 `2fd1199`；DB-003 最终快照 `4f3b74c`（均已独立审查；不代表生产已迁移）
- 用户批准：2026-08-11 用户明确批准「BOOKING-001 加密实施方案，按 `dd59869` 实施」，授权本任务列明的 `cryptography==46.0.7`、AES-256-GCM key ring、公司指纹 HMAC 与三分钟确认 token HMAC；不含生产密钥、生产迁移、外部通知或基础设施。

## 精确规范引用（AI 只读取这些章节）
- SRS §3.5、§5.1～§5.3、§5.6、§7、§8
- domain-model §6.5～§6.8、§6.11、§6.15、§6.17
- architecture §4.0～§4.1
- security §3、§4、§6、§8、§11～§13
- ADR-IMPL-001 §1、§5
- OpenAPI `previewAppointment` / `createAppointment` / `AppointmentDraft` / `AppointmentPreview` / `Appointment`
- test-plan TC-APT-001～003、TC-AUTH-006/008、TC-SEC-001～004

## 需求来源
- R8 / R10 / R12 / R26；UC-08 / UC-19；预约创建安全与并发边界。

## 目标
- 实现 `POST /appointment-confirmations`：登录 interviewer 提交三格与表单后取得绑定用户、完整 payload 和三分钟过期时间的签名确认 token；预览不写数据库、不占 Slot。
- 实现 `POST /appointments`：校验 Cookie 会话、CSRF、同源、限频、`Idempotency-Key`、确认 token 与原 payload 一致后，按 approved 锁顺序完成公司、例外、三格、预约、两条 NotificationEvent 与脱敏 AuditLog 的单事务写入。
- 用真实 PostgreSQL 覆盖两个并发事务抢同一 Slot 仅一方成功。

## 非目标（明确排除）
- 不实现预约改期、用户取消、owner 强制取消或 AvailabilityOverride 管理。
- 不实现 Slot 查询/SSE、NotificationDelivery、Worker、Sweeper、SMTP、IMAP、飞书或实际通知发送。
- 不新增数据库表、字段、索引、枚举、迁移或公开 API/SSE 字段。
- 不执行生产迁移、生产密钥注入、云资源、域名、付款或不可逆外部操作。
- 不实现 Agent 自动预约；大模型不得调用本任务写接口。

## 允许修改路径
- `apps/api/app/appointments/**`
- `apps/api/app/config.py`
- `apps/api/app/factory.py`
- `apps/api/pyproject.toml`
- `apps/api/requirements.lock`
- `apps/api/tests/appointments/**`
- `tasks/TASK-BOOKING-001.md`
- `tasks/TASK-REVIEW-BOOKING-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `apps/api/migrations/**`
- `docs/requirements/**`、`docs/design/**`、`docs/api/**`、`docs/test/**`、`docs/baseline.yml`
- `apps/web/**`、`sleep202603-an/**`
- 认证成功/失败外部契约、Cookie 属性、会话存储或 RBAC 策略
- 通知投递、外部服务、基础设施与生产配置

## 已批准的 DB / API / 依赖变更
- DB：**无 schema 变更**。只使用已批准并已迁移验证的 `0001`～`0003` 表、列、约束和索引；本任务不得新增 migration。
- API/SSE：**无契约变更**。严格实现 approved OpenAPI 0.2 的 `previewAppointment` 与 `createAppointment`；不得增删请求/响应字段或 SSE 事件。
- 鉴权：复用 AUTH 最终快照 `b8c7fc5` 的 Cookie session、CSRF、Origin、RBAC 与 Redis fail-closed 机制；只允许 `interviewer` 创建预约，`owner_admin` 返回 `PERM_DENIED`。
- 依赖（**已由用户批准**）：新增直接依赖 `cryptography==46.0.7`，并把其解析出的传递依赖以精确版本写入 `requirements.lock`；来源为 accepted ADR-IMPL-001，实施授权见本任务「用户批准」。
- 加密与密钥（**已由用户批准**）：
  - `JIANLI_FIELD_ENCRYPTION_CURRENT_KEY_ID`：当前写入 key id；
  - `JIANLI_FIELD_ENCRYPTION_KEYS`：JSON key ring，`key_id -> URL-safe Base64(32-byte AES key)`，仅允许当前与上一版本读取，当前版本写入；
  - `JIANLI_COMPANY_FINGERPRINT_HMAC_KEY`：独立 URL-safe Base64 32-byte key；
  - `JIANLI_APPOINTMENT_CONFIRMATION_HMAC_KEY`：独立 URL-safe Base64 32-byte key，签名三分钟确认 token；
  - 四项不得与 CSRF、rate-limit、Cookie 或外部服务凭证复用；密钥只由环境变量/Secret Manager 注入，不入 Git、日志、响应或测试证据。
- 加密格式（**已由用户批准**）：AES-256-GCM 每次 96-bit 随机 nonce；二进制版本化 envelope 包含 version/key_id/nonce/ciphertext/tag；AAD 绑定 `table + column + record_id`；解密失败拒绝并写不含 PII 的安全告警；key ring 双读单写。
- 确认 token（**已由用户批准**）：HMAC-SHA256 签名、URL-safe 编码，绑定 `user_id + canonical appointment payload digest + expires_at + 256-bit nonce`；服务端只信签名内容并重新校验提交 payload，三分钟后返回 `CONFIRM_EXPIRED`；token 不持久化、不写日志。
- 公司归一化：严格按 PRD 已批准口径（去空格、统一小写、去常见标点后缀）后使用独立 HMAC-SHA256 key 生成 fingerprint；不得记录归一化原文。

> **批准门禁已解除**：用户已于 2026-08-11 明确批准本节的精确依赖与预约加密/密钥实施方案；任何未列明的 DB/API/依赖/加密变化仍须 Stop & Report。

## 规范影响评估（spec impact）
- behavior_change：false（实现 approved 行为，不改变规范）
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：本任务只把已批准的预约预览、原子创建、加密、鉴权和并发规则落为代码；若实现发现契约或 schema 不足，立即 Stop & Report。

## 功能验收
- TC-APT-001：预览返回只读注册邮箱、公司名、称呼与三分钟确认 token；预览前后数据库行数及 Slot 状态不变；token 过期、payload/user 篡改均失败且不落库。
- TC-APT-002：成功提交在一个事务内写 1 Appointment、更新恰好 3 Slot、写 `appointment_created` 与 `reminder_due` 两条 NotificationEvent、写 1 条脱敏 AuditLog；事务内无外部调用。
- TC-APT-003：真实 PostgreSQL 中两个独立事务抢同一组 Slot，仅一个 201，另一个 `SLOT_TAKEN`；失败方无 Appointment/Outbox/AuditLog 残留。
- 三格必须同日、连续、每格 30 分钟、合计 90 分钟；按 `start_at,id` 升序一次性 `FOR UPDATE`，锁成功后重新校验。
- `uq_active_user` / `uq_active_company` / `uq_appointment_exception` 分别映射 approved 错误语义；不吞掉未知完整性错误。

## 安全与隐私验收
- TC-SEC-001：同明文重复加密得到不同 nonce/密文；跨字段或跨记录替换因 AAD 认证失败。
- TC-SEC-002：当前 key 单写、当前+上一 key 双读；撤销旧 key 后旧 envelope 明确失败并告警。
- TC-SEC-003：公司 fingerprint 稳定；AES、company HMAC、confirmation HMAC、CSRF、rate-limit key 全部不同，启动时拒绝重复 key 材料。
- TC-SEC-004：Problem 响应、应用日志、SQL 日志与 AuditLog 不含公司原文、会议号、电话、备注、token、Cookie 或密钥；AuditLog 只记录 actor、action、target 与脱敏类别。
- TC-AUTH-006：预约提交同账号每小时最多 10 次；Redis 故障 fail closed；预览不消耗预约提交配额。
- TC-AUTH-008：两个 POST 均要求同源、有效会话与 CSRF；owner_admin/匿名/跨源均不能预约。
- `recipient_email` 固定取当前已验证 `User.email`，不得信任请求体中的邮箱；请求体不存在可编辑邮箱字段。

## 性能验收
- 预约提交（写库、加密、事务、Outbox）本地真实 PostgreSQL 基准 P95 ≤ 1.5s，不含外部通知。
- 锁事务内禁止 SMTP/飞书/LLM/HTTP；并发测试不得使用 mock 数据库替代 TC-APT-003。

## 变更预算（change_budget）
- max_files：18
- expected_prod_lines：750
- expected_test_lines：650

## 必须运行的测试命令
- 冻结 TC-APT-001～003 后先证明未实现时失败，再实现至通过；不得降低断言或改为 mock。
- 真实 PostgreSQL：预约测试全部通过；TC-APT-003 至少连续 10 轮并发重复。
- `pytest` 全套；AUTH 回归不得出现新增 skip。
- `ruff check`、`ruff format --check`、`mypy`、`pip check`。
- 依赖与 secret scan；确认 Git diff 不含密钥或预约 PII。

## 回滚方法
- `git revert` 本任务实现提交；移除预约 router/config 与 `cryptography` 锁定项。无 migration，不执行数据库 down。
- 测试环境密钥、PostgreSQL、Redis、venv 全部一次性创建，测试后停止并删除。

## 强制停止条件
- 出现本任务已批准范围之外的加密、密钥和依赖变化。
- 需要新增/修改 DB schema、migration、公开 API/SSE、鉴权/加密策略或外部依赖。
- 确认 token、`Idempotency-Key` 或一次性例外语义无法在 approved 工件与现有 schema 内实现。
- 冻结 TC 失败、真实并发测试不能运行或超过 change_budget。
- 发现当前 migration/代码与领域模型不一致；不得以文档推断实现已存在。

## 交付证据
- commit / PR：评审包 `dd59869`；批准记录 `9dc6379`；初始实现 `2291e4b`；独立测试修正 `b8b241f`；测试增强 `90884af`；审查修正后的最终固定实现 `4d5381a`；未创建 PR
- 修改文件清单（相对基线 Git 路径口径，共 17）：`PROJECT_STATE.md`、`apps/api/app/appointments/{__init__,crypto,models,router,runtime,service}.py`、`apps/api/app/config.py`、`apps/api/app/factory.py`、`apps/api/pyproject.toml`、`apps/api/requirements.lock`、`apps/api/tests/appointments/{test_booking,test_security}.py`、`tasks/TASK-BOOKING-001.md`、`tasks/TASK-REVIEW-BOOKING-001.md`、`tasks/TASK-TEST-BOOKING-001.md`、`tasks/TASK-TEST-BOOKING-002.md`
- 测试命令及结果：第二轮证据修正使用一次性 WSL Python 3.12 / PostgreSQL 16.14 / Redis 7.0.15，执行 `pytest tests/appointments -q` → 14 passed / 0 skipped；执行 `pytest -q` → 57 passed / 0 failed / 0 skipped（14 条既有 Alembic 配置弃用 warning）
- lint / typecheck：`ruff check .` → pass；`ruff format --check .` → 38 files formatted；`mypy app` → 22 source files / 0 issues；`pip check` → no broken requirements
- DB 迁移验证：BOOKING/AUTH 两个空库 `0001 → 0002 → 0003` upgrade 通过；全套 26 个 migration 用例通过；另在独立空库显式执行 `upgrade head → downgrade base → upgrade head` 通过；未执行生产迁移
- 临时环境清理：PostgreSQL/Redis 已停止，端口 `55442`/`6403` 无监听；`/var/tmp/jianli-booking-evidence-9caa-r2`（venv、下载包、四个临时数据库、data、日志、PID）已删除
- 验收证据：TC-APT-001～003、TC-SEC-001～004、TC-AUTH-006/008 通过；TC-APT-003 使用两个不同 backend PID 与测试侧屏障连续 10 轮均为一个 201、一个 `SLOT_TAKEN`，每轮严格为 1 Company / 1 Appointment / 3 个归属 winner 的 booked Slot / 2 NotificationEvent / 1 AuditLog，loser 完整回滚；两个 POST 的匿名/owner_admin/CSRF/跨源拒绝与 create Redis fail closed 均通过；非 URL-safe、垃圾字符、缺失/额外 padding 的 key 表示均在启动时拒绝
- 变更预算实际值：17 个 Git 路径；生产代码 `+748/-1`；预约测试代码 `+643/-0`；均低于 18 / 750 / 650 硬预算
- 未解决风险：`Idempotency-Key` 的请求级重放响应未在 approved OpenAPI 中定义，本任务仅强制 16～128 长度且不自行扩展重放语义；Alembic 现有 `path_separator` 弃用 warning 非本任务范围
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`<回填关闭快照>`
- 状态：Closed（2026-08-12）
- 第二轮证据修正：`b41b28c` 的预约套件 13 passed 为计数笔误；`07c6eff` 真实复跑确认为 14 passed、全套仍为 57 passed。
- 独立审查：第三轮审查提交 `ce5b95f`，结论 PASS（P0=0 / P1=0 / P2=0）。
- 关闭结论：① 冻结验收与全套测试通过；② 规范影响 none；③ `spec_sync=clean`；④ 独立审查 PASS。以本次状态收口提交作为完整关闭快照，后续纯证据提交仅回填其 SHA，避免自引用。

## 关联
- 前置：TASK-AUTH-001～003、TASK-DB-002、TASK-DB-003（均 Closed）
- 独立审查：TASK-REVIEW-BOOKING-001
- 冻结验收：TC-APT-001～003、TC-AUTH-006/008、TC-SEC-001～004
