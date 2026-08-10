# TASK-REVIEW-AUTH-001 AUTH-001 独立实现审查

## 任务类型
- test / review

## 目标
- 独立检查 AUTH-001 的范围、契约、密码、会话、CSRF、限频、RBAC、日志脱敏和测试真实性。

## 审查对象
- TASK-AUTH-001 最终实现 commit（待回填）。
- 冻结 TC-AUTH-002/003/004/006（登录切片）/007/008。

## 允许修改路径
- `tasks/TASK-REVIEW-AUTH-001.md`（仅审查证据；审查角色不得改实现）。

## 必查项
- 是否越界实现注册/找回、预约、通知或新增 schema/API。
- BCrypt UTF-8 byte 边界、cost、dummy hash；session token 熵与仅存 hash。
- Cookie 属性、CSRF 双提交与同源校验是否可绕过。
- Redis 故障是否 fail closed、限频 key 是否泄露邮箱、是否错误使用进程内计数。
- RBAC 是否只信服务端 principal；Problem/error code 与 OpenAPI 是否一致。
- 冻结测试是否真实覆盖且未被改宽、skip 或 mock 掉关键安全路径。

## 交付证据
- 审查结论：待回填
- findings：待回填
- verified_commit：待回填
- 状态：Open

