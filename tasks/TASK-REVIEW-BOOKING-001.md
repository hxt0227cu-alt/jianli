# TASK-REVIEW-BOOKING-001 预约创建独立审查

## 任务类型
- review

## 状态
- Reviewed；FAIL（存在 P1/P2 findings，退回实现窗口前向修正；审查窗口未修改生产代码或冻结测试）。

## 审查对象
- TASK-BOOKING-001 的最终固定实现 commit（待回填；审查不得以工作区浮动状态替代）。

## 审查范围
- 越界：新增 DB/API/依赖/鉴权/加密策略是否逐项位于 TASK-BOOKING-001 已批准章节。
- 实现真相：逐字段对照 migration `0001`～`0003`，不得用领域文档推断数据库实际存在。
- 事务：Company → Exception → Slot 升序锁；锁后复检；Appointment/3 Slot/2 Event/AuditLog 原子提交；事务内无外部调用。
- 并发：TC-APT-003 使用真实 PostgreSQL 两个独立连接，至少 10 轮，仅一方成功且失败方无副作用。
- 安全：Cookie/CSRF/Origin/RBAC、Redis fail closed、AES-GCM envelope/AAD/nonce、key ring、独立 HMAC、确认 token 绑定与过期、日志脱敏。
- 契约：只实现 approved OpenAPI 0.2；错误码/Problem media type/status 不漂移。
- 依赖：只新增用户批准的精确 `cryptography` 及必要传递依赖；无重复抽象、未使用代码或未来功能空壳。
- 测试：冻结 TC-APT-001～003、TC-AUTH-006/008、TC-SEC-001～004 未被改宽、skip 或 mock 化。

## 允许修改路径
- `tasks/TASK-REVIEW-BOOKING-001.md`（只回填审查证据）

## 禁止修改路径
- 所有生产代码、测试断言、migration、规范与 baseline；发现问题只报告给实现角色向前修正。

## 审查输出
- P0/P1/P2 findings（文件/行号/复现证据）；无发现时明确写 0。
- 固定被审查 commit、测试环境、命令与结果。
- 复核修正 commit 后给出 PASS/FAIL；不得代替用户批准加密或生产操作。

## 交付证据
- reviewed_commit：`9374a91cd9d332c9dc81c87f8faa16fda5b814d5`
- implementation_evidence_commit：`45b9fa7990c97edfa8c77d46cb574720aa19d397`（其父提交为 reviewed_commit）
- independent_test_compatibility_fix：`b8b241f120b6fc4ca0333fd5952fb021b46141a8`
- reviewer：独立审查窗口 `019fefce-a6d9-7871-a616-944a0c3d1715`
- findings：P0=0，P1=2，P2=2

### Findings

#### P1-1：TC-APT-003 未证明两个独立 PostgreSQL 事务真实重叠，且 loser 无副作用断言不完整
- 位置：`apps/api/tests/appointments/test_booking.py:300`、`:308`、`:318`、`:332`、`:335`
- 证据：测试创建两个 `AsyncClient` 后直接 `asyncio.gather`，但没有事务屏障、`pg_backend_pid()` 或其他证据证明两个请求在 winner 提交前已分别持有独立数据库连接并进入竞争区；串行调度也能得到 `[201, 409]` 并通过。最终仅断言 1 Appointment / 2 NotificationEvent / 1 AuditLog，没有断言 loser 的 Company 插入已回滚，也没有断言恰有 3 个 Slot 为 `booked` 且全部绑定 winner Appointment。`_table_counts()` 虽返回 `companies` 与 `appointment_slots`，本测试未使用这两个值。
- 影响：冻结测试可能在没有真实锁竞争或 loser 遗留 Company/Slot 副作用时误报通过，尚不足以关闭 TC-APT-003。
- 修正方向：由实现窗口按治理流程前向修正冻结测试；显式同步两个独立事务进入竞争区，并核对 backend/连接独立性、1 Company、3 个 winner-owned booked Slot、1 Appointment、2 Event、1 AuditLog。

#### P1-2：预约端点缺少 Redis 故障 fail-closed 与两个 POST 的完整 CSRF/RBAC 冻结覆盖
- 位置：`apps/api/tests/appointments/test_booking.py:150`、`:178`、`:183`、`:187`、`:195`、`:239`
- 证据：现有预约测试验证预览端点的匿名、owner_admin、跨源拒绝及正常 Redis 下第 11 次创建限频；没有对 `BookingRateLimiter` 注入 Redis 故障，也没有分别验证 `/appointment-confirmations` 与 `/appointments` 的缺失/错误 CSRF、跨源、匿名和 owner_admin 拒绝。`apps/api/tests/auth/test_auth.py:225` 的 Redis 故障用例仅覆盖登录限频，不能证明预约写入的独立 `booking:create` 路径。
- 影响：TC-AUTH-006/008 的预约写路径存在冻结验收盲区；静态代码显示当前实现复用了 `_require_csrf`/`require_role` 且 Redis 异常会 fail closed，但测试无法防止端点装配或预约限频路径回归。
- 修正方向：由实现窗口按治理流程补齐预约端点级冻结用例，不改宽既有断言。

#### P2-1：密钥解码未严格拒绝非 URL-safe Base64 表示
- 位置：`apps/api/app/appointments/crypto.py:30`
- 证据：`_decode_key()` 直接调用宽松的 `base64.urlsafe_b64decode()`，未启用字符集校验，也未像确认 token 的 `_b64decode()` 一样重新编码比对 canonical 表示；因此标准 Base64 的 `+`/`/` 或可被解码器忽略的非字母字符可能被接受。已批准配置要求 AES/company HMAC/confirmation HMAC 均为 URL-safe Base64 32-byte key。
- 影响：启动配置校验比批准的密钥格式契约更宽，增加配置歧义；不改变解码后的 32-byte 强度与材料隔离判断。
- 修正方向：严格校验 URL-safe Base64 字符集及 canonical 重编码后再接受。

#### P2-2：变更预算证据的实际文件数少报 2 个
- 位置：`tasks/TASK-BOOKING-001.md`「交付证据」变更预算实际值
- 证据：`git diff --name-status 5062c699f1b692ae0571955ec92976b555071c65..9374a91cd9d332c9dc81c87f8faa16fda5b814d5` 为 16 个文件，而任务证据记录 14 个；遗漏的是审查/独立测试治理文件。实际 16 仍低于 `max_files=18`，生产 745 行、测试 482 行仍分别低于 750/650。
- 影响：不触发预算硬停，但交付证据与固定 Git diff 不一致。
- 修正方向：实现窗口澄清治理文件是否计入预算并回填一致的实际口径。

### 已核对通过的静态项
- migration `0001`~`0003` 的实际 schema 与生产 SQL 字段、enum、FK、unique/index 一致；本实现无 migration/API/SSE/外部通知变更。
- 锁顺序实际为 Company → 可选 CompanyBookingException → 三个 Slot 按 `start_at,id` 升序一次性 `FOR UPDATE`；锁后复检；Appointment/3 Slot/2 NotificationEvent/1 AuditLog 位于单一 PostgreSQL 事务；事务内无外部调用。
- `uq_active_user`/`uq_active_company`/`uq_appointment_exception` 定向映射，未知 `IntegrityError` 原样重新抛出。
- AES-256-GCM 使用 96-bit 随机 nonce、版本化 envelope、AAD=`table+column+record_id`；key ring 当前 key 单写、至多当前/上一 key 双读；AES/company HMAC/confirmation HMAC/CSRF/rate-limit 材料做去重隔离。
- 确认 token 使用 HMAC-SHA256、canonical Base64URL，绑定 user_id、canonical payload digest、expires_at、256-bit nonce；篡改、用户/payload 不匹配与过期均拒绝。
- Cookie session、Origin/Referer、CSRF、interviewer RBAC 复用 AUTH 固定实现；owner_admin/匿名拒绝；预约创建每账号每小时 10 次、Redis 异常代码路径 fail closed；预览不消耗预约配额。
- approved OpenAPI 仅要求 `Idempotency-Key` 必填且长度 16~128，未定义请求级重放语义；当前仅长度校验忠实于契约，不据此提出重放扩展。
- Problem media type/status/error code、敏感响应与 AuditLog 脱敏、事务内无 SMTP/飞书/LLM/HTTP 调用均经静态核对未发现漂移。
- 依赖 diff 仅新增直接依赖 `cryptography==46.0.7`，锁文件新增必要传递依赖 `cffi==2.0.0`、`pycparser==3.0`；未发现密钥或预约 PII 进入生产 Git diff。
- `b8b241f` 仅把 fixture/每轮清理从 `TRUNCATE users CASCADE` 改为显式清理 `audit_logs, notification_events, users, companies CASCADE`，未修改任何断言、阈值、skip 或 mock。

### 测试与门禁
- 审查窗口静态命令：`git diff --check 5062c699..9374a91` → pass；固定 diff/依赖/migration/生产代码/冻结测试逐行审查完成。
- 动态证据复核：implementation_evidence_commit 记录一次性 WSL Python 3.12 + PostgreSQL 16 + Redis 7：`pytest tests/appointments -q` → 8 passed / 0 skipped；`pytest -q` → 51 passed / 0 failed / 0 skipped；`ruff check .`、`ruff format --check .`、`mypy app`、`pip check` 均 pass；migration `0001→0002→0003` 与全套 up/down 路径通过。
- 审查窗口独立复跑：未完成。Windows 无 Python/Docker；一次性 WSL 隔离环境未能可靠启动，已按主窗口指令终止，不再安装或运行。误建 `/packages` 经列出本次下载包并核验路径后删除；`/var/tmp/jianli-review-booking-001` 亦已删除；未启动 PostgreSQL/Redis，端口 `55439`/`6399` 无已知监听。
- 残余风险：动态测试、lint/typecheck、migration up/down 仅复核实现窗口固定证据，未由审查窗口独立重跑；结合 P1-1，既有 TC-APT-003 通过结果不能替代真实重叠/完整 loser 回滚证明。
- result：FAIL（P0=0 / P1=2 / P2=2）
