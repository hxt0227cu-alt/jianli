# TASK-API-001 OpenAPI/SSE 契约

## 任务类型
- design

## 基线版本与基线 commit
- PRD 2.3.3 / domain-model 1.1.5 / UI 1.0 / architecture 0.2（approved）
- SRS 1.2 / security 0.1（approved）
- 基线 commit：`d33b24a`

## 精确规范引用
- SRS §3.1-§3.9 / §4 / §5.6 / §6.2 / §7 / §8
- domain-model §6.1-§6.17
- architecture §4-§7 / §11
- security §2-§12

## 需求来源
- R1-R26 / UC-01-UC-23

## 目标
- 产出并收口 REST OpenAPI 3.1 与 SSE 事件契约，覆盖公开站点、问答、认证、预约、管理后台与可靠恢复。

## 非目标
- 不批准契约；不实现接口；不新增 DB 结构或外部依赖；不修改上游规范。

## 允许修改路径
- docs/api/openapi.yaml
- docs/api/sse.md
- docs/baseline.yml
- tasks/TASK-API-001.md
- PROJECT_STATE.md

## 禁止修改路径
- 已有需求/设计正文、代码、迁移、测试计划

## 已批准的 DB / API / 依赖变更
- DB/依赖：无。API：本任务已完成候选契约与 impact review；获批后才允许实现。

## 规范影响评估
- behavior_change：false
- affected_specs：test_plan=update；其余 none
- reason：把既有行为映射为接口契约，不新增用户能力。

## 验收
- operationId 唯一；请求/响应/错误/权限/幂等键明确。
- SSE 含 snapshot watermark、stream_seq/resource_version、重连与 resync。
- 不泄露红格/PII；错误码与 SRS v1.2 一致。

## 变更预算
- max_files：5
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- YAML 解析、operationId 唯一、引用存在、SSE 与架构一致性检查。

## 回滚方法
- `git revert` 本任务提交。

## 交付证据
- commit / PR：`1f7eb3d`（初始草案）→ `4fb0d01`（首次标准 lint 修正）→ `fd9747c`（SRS/security impact-sync 与安全契约修正）→ `2c8cede`（approval_commit）
- 修改文件清单：docs/api/openapi.yaml / docs/api/sse.md / docs/baseline.yml / tasks/TASK-API-001.md / PROJECT_STATE.md
- 测试命令及结果：33 个 operationId 唯一；Cookie 保护操作缺失 401/403=0；`createConversation` CSRF=true；`streamAnswer` 条件鉴权=true；UTF-8 字节规则=3 处；`git diff --check` pass
- lint / typecheck：Redocly recommended lint → exit 0，0 error / 0 warning
- DB 迁移验证：无
- 验收证据：docs/api/openapi.yaml + docs/api/sse.md
- 变更预算实际值：max_files=5，实际 5 文件，未超预算
- 未解决风险：实现阶段仍需独立 implementation TASK；具体鉴权、CSRF、外部通知实现按安全/基础设施人审边界执行
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`3e2b58b`
- 状态：Closed

## 关联
- 上游：TASK-SRS-003 / TASK-SEC-001
- 下游：测试计划与实现任务
