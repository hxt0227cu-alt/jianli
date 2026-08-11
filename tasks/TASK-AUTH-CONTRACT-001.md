# TASK-AUTH-CONTRACT-001 认证错误契约收口

## 任务类型
- documentation / approved Change Request

## 当前阶段
- 状态：In Progress
- 人工批准：用户于 2026-08-11 明确批准新增 `INVALID_CREDENTIALS`（401）与 `INVALID_REQUEST`（422 Problem）并同步 SRS/OpenAPI/测试计划。

## 基线版本与基线 commit
- baseline：SRS 1.2 / OpenAPI-SSE 0.1 / test_plan 0.1（均 approved）
- 基线 commit：`9e00f2c`

## 精确规范引用
- SRS §3.3、§8
- OpenAPI operationId `login`、components `Problem`
- 测试计划 TC-AUTH-002、TC-AUTH-004、TC-AUTH-008

## 需求来源
- TASK-REVIEW-AUTH-001 对 `f5fd75c` 的独立审查：凭证错误借用 `AUTH_EXPIRED`；登录输入 422 不符合统一 Problem envelope。

## 目标
- 以用户批准的精确语义更新并批准 SRS v1.3、OpenAPI v0.2、测试计划 v0.2，解除 AUTH 实现阻塞。

## 非目标
- 不改变登录成功路径、密码策略、限频阈值、会话、权限、DB、依赖或任何非认证业务；不修改实现代码。

## 允许修改路径
- `docs/requirements/SRS.md`
- `docs/api/openapi.yaml`
- `docs/test/test-plan.md`
- `docs/baseline.yml`
- `PROJECT_STATE.md`
- `tasks/TASK-AUTH-CONTRACT-001.md`

## 禁止修改路径
- `apps/**`、migration、PRD、use-cases、domain-model、architecture、security、UI、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB/依赖：无。
- API：`login` 凭证错误统一返回 401 `INVALID_CREDENTIALS`；请求校验失败返回 422 `INVALID_REQUEST` + `application/problem+json`，不得回显输入值。

## 规范影响评估
- behavior_change：true（稳定错误码与错误媒体类型属于外部可观察契约）
- affected_specs：srs=update；openapi=update；test_plan=update；security=none；domain_model=none；architecture=none；ui=none
- reason：经用户批准的 Change Request 修复契约缺口，不改变成功路径或产品能力。

## 验收
- 不存在账号与错误密码对外完全同码同文案，均为 401 `INVALID_CREDENTIALS`。
- 登录请求校验失败为 422 `INVALID_REQUEST`，媒体类型为 `application/problem+json`，错误体不含原始输入。
- `AUTH_EXPIRED` 继续仅表示无效/过期会话；冻结 TC 不降低断言。
- OpenAPI lint 0 error；三份工件与 baseline 版本/状态一致。

## 变更预算
- max_files：6
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- OpenAPI 解析与 lint
- 错误码、版本、baseline 一致性检查

## 回滚方法
- `git revert` 本任务规范提交；不触碰 v1.2/v0.1 历史快照。

## 强制停止条件
- 需要新增第三个错误码、修改成功路径/鉴权/密码/限频、改动代码或超过 6 文件时停止。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：updated
- spec_sync：dirty
- verified_commit：待回填
- 状态：Open
