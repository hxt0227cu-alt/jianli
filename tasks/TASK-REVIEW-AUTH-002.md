# TASK-REVIEW-AUTH-002 AUTH 最终独立审查

## 任务类型
- test / review

## 目标
- 独立审查 AUTH 最终实现是否符合 SRS 1.3 / OpenAPI 0.2，并复核既有安全门禁没有回归。

## 审查对象
- TASK-AUTH-003 最终实现 commit（待回填）
- TC-AUTH-002/003/004/006/007/008

## 允许修改路径
- `tasks/TASK-REVIEW-AUTH-002.md`（仅审查证据）

## 必查项
- 401 `INVALID_CREDENTIALS` 模糊响应；422 `INVALID_REQUEST` Problem 脱敏。
- BCrypt/dummy hash、会话旋转、Cookie/CSRF/CORS、Redis TTL/fail closed、RBAC、安全日志无回归。
- 无新增依赖/DB/API；真实测试零 skip；TASK-AUTH-003 预算真实性。

## 交付证据
- 审查结论：待回填
- findings：待回填
- verified_commit：待回填
- 状态：Open
