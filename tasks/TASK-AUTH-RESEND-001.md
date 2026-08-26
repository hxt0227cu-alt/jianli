# TASK-AUTH-RESEND-001 注册验证码安全重发实现

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.6 / SRS 1.5 / OpenAPI 0.6
- 基线 commit：`a846dd2`

## 精确规范引用
- `docs/requirements/SRS.md §3.3 / §5.6`
- OpenAPI operationId `resendEmailVerification`
- `docs/test/test-plan.md` TC-AUTH-001 / TC-AUTH-006
- `TASK-CR-AUTH-RESEND-001`

## 目标
实现注册验证码重发：恒 202 防枚举、共享注册发码限频、原子使旧未消费码失效并创建新码。

## 非目标
- 不新增 DB 字段/迁移/依赖；不修改登录、找回密码或邮件投递模式。

## 允许修改路径
- `apps/api/app/auth/router.py`
- `apps/api/app/auth/service.py`
- `apps/api/app/auth/repository.py`
- `apps/api/tests/auth/test_account_lifecycle.py`
- `tasks/TASK-AUTH-RESEND-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- 认证表迁移、依赖文件、预约/AIQA/通知模块、approved 规范

## 已批准的 DB / API / 依赖变更
- DB：无；复用 `email_verification_tokens`。
- API：实现 OpenAPI 0.6 `POST /auth/resend-verification` / `resendEmailVerification`；202/429。
- 依赖：无。

## 规范影响评估
- behavior_change：true；已由 TASK-CR-AUTH-RESEND-001 批准
- srs/domain/openapi/security/test_plan：none（实现批准态）
- spec_sync：clean

## 功能、安全与性能验收
- 未验证账号重发后，所有旧未消费注册码被原子消费，仅新码可验证。
- 未知邮箱、已验证邮箱、未验证邮箱均返回同样 202 空响应；限频返回 429 + Retry-After。
- 重发与注册使用 `kind=verify` 的同一邮箱/IP 发码计数；不记录或返回验证码。
- 单次请求不新增额外外部往返；数据库更新与新 token 插入同事务。

## 变更预算
- max_files：6
- expected_prod_lines：90
- expected_test_lines：140

## 必须运行的测试命令
- `pytest tests/auth/test_account_lifecycle.py -v`（真实 PG/Redis）
- `pytest tests/auth -q`
- 本任务文件 `ruff check`；`mypy app`

## 回滚方法
- 回退实现提交；无迁移。

## 强制停止条件
- 遵循 `AGENTS.md §2`；未列明 DB/API/依赖变化、冻结测试失败或超预算立即停止。

## 交付证据
- commit / PR：`ce608b4`
- 修改文件清单：auth repository/router/service、真实生命周期测试、本任务（5 文件）
- 测试命令及结果：真实 PG/Redis `test_account_lifecycle.py` 6 passed；DB-free `tests/auth` 16 passed / 7 env-skipped
- lint / typecheck：本任务 Python 文件 ruff passed；`mypy app` 46 source files / 0 error
- DB 迁移验证：无
- 验收证据：旧码返回 422 INVALID_VERIFY_CODE、新码 204；未知/已验证/未验证响应均 202 JSON null；注册后立即重发 429 RATE_LIMITED
- 变更预算实际值：5/6 文件；生产新增 59 行、测试新增 72 行；未超预算
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated（上游 CR 已批准）
- spec_sync：clean
- verified_commit：`ce608b4`
- 关闭门禁：Closed（四条件满足）

## 关联
- Change Request：TASK-CR-AUTH-RESEND-001（Approved / Closed，`06ebfd7`）
- 测试：TC-AUTH-001 / TC-AUTH-006
