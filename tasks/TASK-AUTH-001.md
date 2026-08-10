# TASK-AUTH-001 认证、会话、CSRF、登录限频与 RBAC 核心

## 任务类型
- implementation

## 当前阶段
- 状态：In Progress
- 用户授权：2026-08-11 用户明确要求直接开始 AUTH-001，并在通过独立审查后自动进入 BOOKING 主线。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.1 / test_plan 0.1（均 approved）
- ADR-IMPL-001：accepted
- 基线 commit：`a25fd07`

## 精确规范引用
- `docs/requirements/SRS.md` §3.3、§5.6、§6.3、§7、§8
- `docs/design/security.md` §2、§3、§7、§8、§12
- `docs/design/domain-model.md` §6.1–§6.2
- `docs/design/architecture.md` §2 Auth 服务、§9.1
- OpenAPI operationId：`login`、`logout`、`getCurrentUser`
- `docs/adr/ADR-IMPL-001.md` §1–§2、§5
- 冻结测试：TC-AUTH-002/003/004/006（登录切片）/007/008

## 需求来源
- R9、R19、R20；预约主线的登录前置条件。

## 目标
- 实现密码登录、PostgreSQL 不透明会话、Secure/HttpOnly/SameSite Cookie、CSRF/同源防护、Redis 登录限频、当前用户查询和 RBAC 核心，为 BOOKING-001 提供可信 principal。

## 非目标
- 不实现 `registerInterviewer`、`verifyEmail`、`requestPasswordReset`、`confirmPasswordReset`；这些依赖后续通知 Outbox/邮件投递并单独建任务。
- 不实现预约、通知、AI、admin 业务接口，不新增 AES/HMAC 业务字段加密。
- 不创建或修改数据库表、字段、索引、enum 或 migration。
- 不安装/启动生产 PostgreSQL、Redis，不写入生产密钥或连接外部服务。

## 允许修改路径
- `apps/api/app/config.py`
- `apps/api/app/factory.py`
- `apps/api/app/auth/**`
- `apps/api/pyproject.toml`
- `apps/api/requirements.lock`
- `apps/api/tests/test_app.py`
- `apps/api/tests/auth/**`
- `tasks/TASK-AUTH-001.md`
- `tasks/TASK-REVIEW-AUTH-001.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- `apps/web/**`、`apps/api/migrations/**`、`infra/**`
- 已批准 PRD/SRS/domain/architecture/security/OpenAPI/test-plan 正文
- `sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB：无；只读写 DB-001 已批准并创建的 `users`、`auth_sessions`。
- API：实现已批准 operationId `login`、`logout`、`getCurrentUser`，路径与请求/响应保持 OpenAPI v0.1；不新增公开 endpoint/schema/error code。
- 浏览器防护：`__Host-session` 为 HttpOnly 会话 Cookie；会话派生的 `__Host-csrf` 双提交 Cookie + `X-CSRF-Token` + Origin/Referer 同源校验，不新增数据库列。
- 依赖：新增 ADR-IMPL-001 已接受的 `bcrypt`、`redis` Python 包并精确锁定；不得新增其它直接依赖。
- 配置：只新增数据库 URL、Redis URL、允许 Origin、CSRF HMAC key、限频 HMAC key 的运行时环境变量名；不提交值。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：仅实现已批准行为与接口，不改变用户可观察契约。

## 功能验收
- 正确密码且账号已验证时建立会话；错误密码与不存在账号走 dummy hash 恒定路径；验证码不能登录。
- 普通会话 12h，remember_me 会话 14d；登录旋转随机 token，数据库仅存 SHA-256 hash。
- `GET /auth/me` 返回当前用户；退出后旧 Cookie 返回 `AUTH_EXPIRED`。
- owner_admin 与 interviewer principal 可被服务端 RBAC 区分；角色拒绝返回 `PERM_DENIED`。

## 安全与隐私验收
- BCrypt cost=12；密码按 UTF-8 10–72 bytes，73 bytes 明确拒绝且不截断。
- Cookie 为 Secure/HttpOnly/SameSite=Lax/Path=/；CSRF 缺失、错误或非同源写请求拒绝。
- Redis 不可用时登录 fail closed；限频 key 只含 HMAC 标识或截断 IP，不含邮箱明文。
- 日志与错误响应不含密码、Cookie、session/CSRF token、哈希、密钥或邮箱明文。

## 性能验收
- BCrypt cost 不低于 12；正式 P95 校准留上线性能任务，不在单元测试降低 cost。
- 数据库会话查询使用 DB-001 既有主键/FK路径；不引入进程内会话或限频真相源。

## 变更预算
- max_files：18
- expected_prod_lines：750
- expected_test_lines：900

## 必须运行的测试命令
- `python -m pytest tests/auth tests/test_app.py -q -ra`
- `python -m pytest -q -ra`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy app`
- `python -m pip check`
- 使用一次性 PostgreSQL 真实验证 session 创建/读取/吊销；Redis 成功/超限/故障路径使用真实 Redis 或可审计协议故障注入，不把进程内计数冒充正式实现。

## 回滚方法
- 回退 AUTH-001 实现提交和新增依赖；无 migration down。删除一次性测试环境，不触碰生产数据。

## 强制停止条件
- 需要新增未列明依赖、DB schema、公开 API/SSE、错误码或改变批准的鉴权/密钥策略。
- 注册/找回邮件被要求并入本任务，或出现 OpenAPI/security/domain 冲突。
- 冻结验收失败、真实 PostgreSQL 会话路径无法验证或超出 change_budget。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无迁移；真实会话读写待回填
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 状态：Open

## 关联
- 独立审查：TASK-REVIEW-AUTH-001
- 后续：DB-002（预约域迁移）→ BOOKING-001

