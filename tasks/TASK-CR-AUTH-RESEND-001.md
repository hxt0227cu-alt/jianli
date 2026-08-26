# TASK-CR-AUTH-RESEND-001 注册验证码重发规范批准

> 状态：Approved / Closed（2026-08-26）。用户明确批准恒 202 防枚举、复用发码限频、重发使旧码失效；本任务只同步规范，不写实现。

## 基线与引用

- baseline commit：`7da321f`
- SRS 1.4 §3.3 / §5.6 / §9；OpenAPI 0.5 `registerInterviewer` / `verifyEmail`；测试计划 0.2 `TC-AUTH-001/006`
- 用户批准文本：2026-08-26 对 `TASK-CR-AUTH-RESEND-001` 第 2 项授权

## 目标

- SRS 1.5：未验证账号可请求重发注册验证码；无论邮箱未知、已验证或未验证均返回相同 202。
- OpenAPI 0.6：新增 `POST /auth/resend-verification`，operationId `resendEmailVerification`，复用 `EmailRequest`。
- 有效重发复用注册发码限频；新码生成前使该账号所有未消费旧注册验证码失效。
- 测试计划 0.3：在既有 TC-AUTH-001/006 中冻结重发与防枚举断言，不增加 TC 总数。

## 非目标

- 不修改代码、数据库、依赖或前端。
- 不改变登录、密码找回、验证码 TTL/错误次数或 SMTP 交付模式。

## 允许修改路径

- `docs/requirements/SRS.md`
- `docs/api/openapi.yaml`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `tasks/TASK-CR-AUTH-RESEND-001.md`
- `PROJECT_STATE.md`

## 已批准的 DB / API / 依赖变更

- DB：无。
- API：新增上述 resend operation；成功/防枚举均 202，限频 429。
- 依赖：无。

## 规范影响评估

- SRS：1.4 → 1.5 approved
- OpenAPI：0.5 → 0.6 approved
- test-plan：0.2 → 0.3 approved
- domain-model / security / architecture：none
- spec_sync：clean

## change_budget

- max_files：6
- expected_spec_lines：≤100

## 验收

- OpenAPI operationId 全局唯一，request schema 复用 `EmailRequest`。
- 202 响应不泄露账号状态；429 保持独立限频语义。
- 实现必须另由下游 implementation TASK 承载。

## 交付证据

- commit / PR：`06ebfd7`
- 修改文件：SRS / OpenAPI / test-plan / baseline / PROJECT_STATE / 本任务
- 验证结果：OpenAPI 静态检查通过，38 个 operationId 唯一；resend 路径、operationId 与 EmailRequest 引用存在；`git diff --check` PASS
- 规范影响：SRS 1.5 / OpenAPI 0.6 / test-plan 0.3 approved
- spec_sync：clean
- verified_commit：`06ebfd7`
