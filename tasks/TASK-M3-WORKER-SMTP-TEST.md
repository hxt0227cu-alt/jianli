# TASK-M3-WORKER-SMTP-TEST 补 M3 通知 Worker 的真 SMTP E2E 测试

## 任务类型
- test  # 测试：单元 / 集成 / 验收

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5（取自 `docs/baseline.yml`）
- 基线 commit：`3bdf067`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/design/domain-model.md` §6.11（`NotificationEvent` Outbox 状态机：`pending/processing/processed/cancelled/failed`，`scheduled_at` 仅 `reminder_due` 非空）
- `docs/design/domain-model.md` §6.12（`NotificationDelivery` 收件人来源：`interviewer_confirmation` = `Appointment.user_id → User.email`，即面试官/预约归属人注册邮箱）
- `tasks/TASK-M3-APPOINTMENTS.md`（其「未解决风险：Worker SMTP 发送路径 runtime-unverified，待补 test_worker.py」）

## 需求来源
- 现状勘误：M3 的**桩测试其实已在 commit `1c44372` 落地**（`apps/api/tests/test_worker.py`：`test_worker_smoke_logs_one_safe_structured_event` + `test_worker_smtp_path_claims_renders_marks`，用 fake sender 验证 claim→解密→渲染→send→processed，含 reminder_due 门禁）。PROJECT_STATE 与 M3 任务单的「未解决风险」描述**过时**。
- **唯一真实缺口**：真 SMTP E2E——现有测试用 fake sender，从未真连 `smtp.163.com:465` 发送。本任务只补这一条。

## 目标
在已存在的 `apps/api/tests/test_worker.py` 追加一条真 SMTP E2E 用例：经真实 `smtp.163.com:465` SSL 把 `appointment_created` 确认函实发到预约 owner 注册邮箱，以事件达 `processed` 为发送成功判据（`smtplib` 无异常）；`JIANLI_SMTP_PASSWORD` 缺失时 skip。

## 非目标（明确排除）
- 不改任何生产代码（`apps/api/app/**` 只读不改）。
- **不重复造桩测试**（已存在于 `tests/test_worker.py`，本任务不复制、不微调）。
- 不新建/修改数据库表、字段、索引、迁移（不建延后的 `notification_deliveries`）。
- 不新增外部依赖（真 E2E 复用既有 `smtplib`）。
- 不接飞书通道、不实现候选人侧（owner_admin）email/feishu 双通道（仍为延后项）。
- 不改变 SMTP 发送逻辑 / 收件人语义。

## 允许修改路径
- `apps/api/tests/test_worker.py`（追加真 E2E 用例 + 两个 helper + 2 个 import）
- `tasks/TASK-M3-WORKER-SMTP-TEST.md`（本任务单）

## 禁止修改路径
- `apps/api/app/**`（生产代码）
- `apps/api/migrations/**`
- `docs/**`（含 `docs/api/openapi.yaml`、`docs/design/domain-model.md`）
- `apps/web/**`

## 已批准的 DB / API / 依赖变更
- 无（纯测试；不新增依赖、不改 schema、不改契约）

## 规范影响评估（spec impact，每个代码 TASK 必填）
- behavior_change：false（新增测试，不改变用户可观察行为）
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅为 M3 已实现发送路径补真 E2E 测试，不改变实现行为。
- 分类：**代码重构（行为未变）→ 不需要改 SRS；更新测试/交付证据即可**

## 功能验收
- 真 SMTP E2E（`JIANLI_SMTP_PASSWORD` 存在时启用，缺失则 skip）：
  - 预约 owner 注册邮箱 = `[邮箱已脱敏]`（用户指定，便于真收信核对）。
  - 经 API 创建预约 → Outbox 写入 `appointment_created`。
  - worker 真连 `smtp.163.com:465` SSL → `smtplib` login + send 无异常 → 事件 `status=processed`。
  - 发送失败（认证/网络）会留 `failed`，断言不通过，从而真实暴露发送路径问题。

## 安全与隐私验收
- SMTP 授权码**绝不写入测试源码 / 记忆 / 配置**，仅经运行时环境变量 `JIANLI_SMTP_PASSWORD` 读取（`_smtp_settings` 用 `os.environ[...]`）。
- 收件人 `[邮箱已脱敏]` 是用户本人运营邮箱（非加密字段），用于真 E2E 收信核对，不落任何明文敏感字段（住址/工资等）。

## 性能验收
- 无新增生产路径；真 E2E 单用例，SMTP 网络往返约 1–3s，超时 40s 兜底。

## 变更预算（change_budget）
- max_files：2
- expected_prod_lines：0
- expected_test_lines：≤ 130

## 必须运行的测试命令
- `pytest tests/test_worker.py -v`（WSL 真实 PostgreSQL/Redis，需 `JIANLI_BOOKING_TEST_DATABASE_URL` / `JIANLI_BOOKING_TEST_REDIS_URL` + 密钥 env；真 E2E 额外需 `JIANLI_SMTP_PASSWORD`）
- `ruff check tests/test_worker.py`
- `mypy apps/api`（或 repo 级）
- `python -m py_compile tests/test_worker.py`

## 回滚方法
- `git checkout -- apps/api/tests/test_worker.py`（还原该文件，去掉追加的真 E2E，无生产影响）。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 若真 E2E 暴露生产代码与领域模型 §6.12 收件人语义不一致（如实际发给了非预约 owner），立即停止并报告，不自行改生产代码。
- 若需要新增外部依赖才能真发送，立即停止并报告（本任务复用既有 `smtplib`，不新增）。
- 超出 `change_budget`（max_files=2 / 测试行数 > 130）→ 拆任务。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`e77f3e9`（实现：test_worker.py + 任务单）+ `91b1ef3`（verified_commit 回填）+ 本关闭提交（收口结论 + PROJECT_STATE 同步）
- 修改文件清单：`apps/api/tests/test_worker.py`（追加真 E2E 用例 `test_worker_real_smtp_e2e` + `_seed_user_with_email`/`_smtp_settings` 两个 helper + `threading`/`time` 两个 import，+119 行）；`tasks/TASK-M3-WORKER-SMTP-TEST.md`（本任务单）。与「允许修改路径」一致。
- 测试命令及结果：
  - 桩测试（用户 WSL 2026-08-18）：`pytest tests/test_worker.py -v` → **2 passed + 1 skipped**（真 E2E 无授权码时 skip，预期正确）。
  - 真 E2E 首次（用户 WSL）：`pytest tests/test_worker.py::test_worker_real_smtp_e2e -v` → **FAILED**：`AttributeError: 'str' object has no attribute 'get_secret_value'`（email.py:141）。
  - **根因**：`_smtp_settings()` 用 `model_copy(update=...)` 塞 `smtp_password` 为普通 `str`，pydantic `model_copy` 不做类型校验（str 不会自动转 `SecretStr`），而 `EmailSender` 期望 `SecretStr.get_secret_value()`。
  - **修复**：`"smtp_password": SecretStr(os.environ["JIANLI_SMTP_PASSWORD"])` 显式包装 + `from pydantic import SecretStr`。沙箱本地验证 `EmailSender(updated)` 构造通过，ruff ✅ / py_compile ✅。
  - **真 E2E 终跑（用户 WSL 2026-08-18）**：`pytest tests/test_worker.py::test_worker_real_smtp_e2e -v` → **PASSED（1 passed in 5.73s）**——真连 `smtp.163.com:465` SSL，事件达 `processed`，确认函实发到 `[邮箱已脱敏]`（用户本人邮箱）。
- lint / typecheck：`ruff check tests/test_worker.py` → All checks passed ✅；`python -m py_compile tests/test_worker.py` → OK ✅；`mypy` → Success, no issues found in 45 source files ✅（tests 不在 mypy 范围，属项目既有配置）
- DB 迁移验证：无
- 验收证据：真 E2E 事件达 `processed` ✅（用户 WSL 2026-08-18，`1 passed in 5.73s`）；用户邮箱 `[邮箱已脱敏]` **收信核对通过 ✅**（用户 2026-08-18 确认收到确认函，主题含「面试预约确认」+「Example, Inc.」，正文含会议号 123-456-789）。
- 变更预算实际值：max_files=2（实际 2）/ 生产行数 0（实际 0）/ 测试行数 +119（预算 ≤130，未超）
- 未解决风险：
  - **安全提醒（高优先，非关闭阻塞）**：用户 2026-08-18 已**两次**在 WSL 终端把 163 SMTP 授权码明文贴进对话（`export JIANLI_SMTP_PASSWORD=...`）。授权码已两次出现在对话记录，**建议作废并重新生成**（163 邮箱设置→POP3/SMTP/IMAP→关闭再开启或重置授权码），新授权码只在本机 WSL `export`，**绝不贴入对话/文件/记忆**。此提醒已随任务单留痕，作废与否由用户操作，不阻塞本任务关闭。
- 是否偏离 TASK：否（发现桩测试已于 `1c44372` 存在后，如实收敛为「只补真 E2E」，未复制桩测试；已撤销冗余的 `tests/appointments/test_worker.py`；`SecretStr` 包装修复属于本任务真 E2E 用例自身缺陷，不越界）
- 规范影响结论：none
- spec_sync：clean（本任务不改任何规范工件）
- verified_commit：`e77f3e9`（实现+任务单提交，2026-08-18）
- **关闭门禁（四条件）**：① 测试通过 ✅（真 E2E 用户 WSL 2026-08-18 `1 passed in 5.73s`）；② 规范影响 none ✅；③ spec_sync clean ✅；④ verified_commit=`e77f3e9` ✅。**已关闭（Closed，2026-08-18 用户邮箱核对通过 + 显式授权关闭）**。M3 遗留风险「Worker SMTP 发送路径 runtime-unverified」闭合。

## 关联
- Change Request：无
- 测试任务：补 `tasks/TASK-M3-APPOINTMENTS.md` 的「未解决风险」（真 E2E 部分；桩测试部分已于 `1c44372` 闭合）
