# TASK-AUTH-EMAIL-DELIVERY-001 注册验证码邮件环境隔离

> 状态：Closed（2026-08-26，verified_commit=`537fbbf`）

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.5
- 基线 commit：`3437b8b`（PRD 基线校正任务关闭快照）

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.3、§4.2（注册验证/密码找回邮件与凭证不得进日志）
- `docs/design/security.md` §7、§10、§11（验证码、通知日志、安全日志）
- `docs/api/openapi.yaml` operationId：`registerInterviewer`、`verifyEmail`、`requestPasswordReset`、`confirmPasswordReset`
- `tasks/TASK-M4-APPOINTMENTS.md` 邮件 best-effort 与 TC-AUTH-REG/VERIFY/RESET 既有验收

## 需求来源
- 用户要求项目正式绑定域名上线：面试官以真实邮箱接收 6 位验证码完成注册；本地/测试环境必须能自动取得验证码，但生产环境任何路径均不得输出验证码。
- 用户 2026-08-26 明确授权本任务：仅处理测试/生产邮件模式隔离、生产环境禁止输出验证码及相关测试；不新增 API、数据库迁移或外部依赖。

## 目标
把注册验证和密码找回验证码交付拆为显式、互斥的 `console` 测试模式与 `smtp` 邮件模式，并让生产配置 fail closed，杜绝 SMTP 失败后验证码进入日志。

## 非目标（明确排除）
- 不新增或实现 `resend-verification`；该行为需独立 Change Request。
- 不改变 4 个 approved Auth operation 的路径、字段、状态码或响应语义。
- 不改验证码生成、SHA-256 存储、10 分钟 TTL、一次性消费、限频、登录/CSRF/RBAC。
- 不改数据库、迁移、依赖、前端、AIQA、预约与通知 Worker。
- 不把 QQ/163 真实邮箱或 SMTP 凭据写入自动化测试；真实邮箱仅作显式冒烟验证。

## 允许修改路径
- `tasks/TASK-AUTH-EMAIL-DELIVERY-001.md`
- `apps/api/app/config.py`
- `apps/api/app/auth/runtime.py`
- `apps/api/app/auth/service.py`
- `apps/api/tests/test_config.py`
- `apps/api/tests/auth/test_email_delivery.py`
- `PROJECT_STATE.md`

## 禁止修改路径
- 所有 migration、OpenAPI/SRS/安全设计正文、依赖锁文件。
- `apps/api/app/aiqa/`、`apps/web/`、预约域与通知 Worker。
- 当前工作区中与本任务无关的既有未提交改动。

## 已批准的 DB / API / 依赖变更
- DB：无。
- API：无；仅保持 4 个 approved Auth operation。
- 依赖：无；复用标准库输出/日志、现有 `EmailSender` 与 Pydantic。
- 配置：允许现有未提交的 `JIANLI_EMAIL_MODE=smtp|console` 进入本任务；默认 `smtp`。`console` 仅允许 `environment in {local,test}`，生产选择 console 必须拒绝启动；production 构建 Auth runtime 时 SMTP 配置不完整必须拒绝启动。

## 规范影响评估（spec impact）
- behavior_change：false（生产用户可观察契约不变）
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none（新增实现级安全回归测试，不修改冻结 TC）
- reason：Bug 修复使实现重新符合 approved security §10/§11“验证码不得写日志”和 SRS §4.2“凭证不进日志”；本地/test console 是用户显式批准、环境硬隔离的非生产测试通道。
- 分类：Bug 修复使代码重新符合现有 SRS/安全设计。

## 功能验收
- `local/test + console`：不构造 SMTP sender，验证码仅输出到显式本地终端通道，注册/找回业务继续执行。
- `smtp`：配置完整时调用真实 `EmailSender`；发送失败仍保持既有 best-effort 业务语义，但只写不含邮箱、验证码、正文或异常文本的脱敏事件。
- `production + console`：配置校验失败，应用不得启动。
- `production + smtp` 但 SMTP 配置不完整：Auth runtime 构建失败，不允许静默 sink。
- 非生产 `smtp` 且 SMTP 未配置：保持历史本地 sink（令牌入库、无输出），不泄露验证码。

## 安全与隐私验收
- 生产和 SMTP 失败日志不得出现验证码、收件人明文、邮件正文、授权码或异常文本。
- console 通道只能在 `local/test` 显式启用，使用终端输出而非应用 logger；默认关闭。
- 测试不得包含真实 QQ/163 邮箱、密码、验证码或 SMTP 授权码。

## 性能验收
- 不增加网络调用次数；console 为一次同步终端写；SMTP 路径保持一次发送。

## 变更预算（change_budget）
- max_files：7
- expected_prod_lines：约 90
- expected_test_lines：约 150

## 必须运行的测试命令
- `cd apps/api && python -m pytest tests/test_config.py tests/auth/test_email_delivery.py -q`
- 若真实 PG/Redis 环境可用：`cd apps/api && python -m pytest tests/auth/test_account_lifecycle.py -q`
- `cd apps/api && python -m ruff check app/config.py app/auth/runtime.py app/auth/service.py tests/test_config.py tests/auth/test_email_delivery.py`
- `cd apps/api && python -m mypy app`
- `git diff --check`（仅本任务文件）

## 回滚方法
- `git revert` 本任务实现提交；恢复到“未配置 SMTP 时静默 sink”的历史实现。不得恢复 SMTP 失败输出验证码的未提交实现。

## 强制停止条件
- 需要新增 resend API、DB 字段/迁移、依赖或修改验证码/鉴权策略时立即停止并另立任务。
- 任一冻结 Auth 验收测试失败，停止且不得放宽断言或 skip。
- 超过 7 文件或生产/测试行预算，停止拆分。

## 交付证据
- commit / PR：实现提交 `537fbbf`；任务关闭证据提交见本文件后续 Git 历史。
- 修改文件清单：本任务单、`PROJECT_STATE.md`、`app/config.py`、
  `app/auth/runtime.py`、`app/auth/service.py`、`tests/test_config.py`、
  `tests/auth/test_email_delivery.py`，共 7 文件。
- 测试命令及结果：
  - `PYTHONPATH=. python3 -m pytest tests/test_config.py tests/auth/test_email_delivery.py -q`
    → 11 passed。
  - `PYTHONPATH=. python3 -m pytest tests/test_app.py tests/test_config.py tests/auth/test_email_delivery.py -q`
    → 14 passed。
  - `PYTHONPATH=. python3 -m pytest tests/auth -q`
    → 16 passed、6 skipped（缺少专用真实 PG/Redis 测试变量，既有集成用例按门禁跳过）。
- lint / typecheck：
  - 本任务 5 个 Python 文件 `ruff check` → pass。
  - `mypy app/config.py app/auth/runtime.py app/auth/service.py` → 0 error。
  - 全量 `mypy app` → 被任务外既有工作区改动阻塞：`aiqa/service.py` 2 error、
    `aiqa/runtime.py` 1 error；未越界修改。
- DB 迁移验证：无。
- 验收证据：
  - `production + console` 配置拒绝、production SMTP 不完整拒绝、SMTP 失败日志脱敏、
    local/test console 显式输出均有自动化用例。
  - 使用运行时 SMTP 配置向授权的 QQ 收件箱发送不含可用验证码的冒烟邮件；
    SMTP 服务端接受，Chrome 中确认约 1 分钟内由 163 通道送达。未记录邮箱密码、
    Cookie、验证码或邮件正文中的敏感值。
  - 本任务文件 `git diff --check` 与 staged diff check → pass。
- 变更预算实际值：7 文件；生产代码 75 changed lines；测试新增 129 行，未超预算。
- 未解决风险：本机没有专用 `JIANLI_AUTH_TEST_DATABASE_URL` / Redis 测试变量，
  因此未重复执行真实账户生命周期集成用例；全量 mypy 的 3 个 AIQA 错误属于任务外既有改动。
- 是否偏离 TASK：否。
- 规范影响结论：none。
- spec_sync：clean（无规范正文、API、DB 或依赖变化）。
- verified_commit：`537fbbf`。
- 关闭门禁：通过；任务范围内测试、lint、类型检查、真实 SMTP 收件与变更预算均满足。

## 关联
- 前置治理：`TASK-GOV-BASELINE-PRD-001`（Closed）
- 历史实现：`TASK-M4-APPOINTMENTS`
- 后续候选：`TASK-CR-AUTH-RESEND-001` → `TASK-AUTH-RESEND-001`
