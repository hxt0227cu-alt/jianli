# TASK-AUTH-003 认证错误契约实现适配

## 任务类型
- implementation

## 当前阶段
- 状态：Closed

## 基线版本与基线 commit
- baseline：SRS 1.3 / OpenAPI-SSE 0.2 / test_plan 0.2（均 approved）；其余基线不变
- 基线 commit：`2c46060`

## 精确规范引用
- SRS §3.3、§8
- OpenAPI operationId `login`、responses `InvalidCredentials` / `InvalidRequest`
- TC-AUTH-002、TC-AUTH-004、TC-AUTH-008

## 需求来源
- 用户批准的 TASK-AUTH-CONTRACT-001；关闭 TASK-REVIEW-AUTH-001 唯一剩余契约 P1。

## 目标
- 错误凭证统一返回 401 `INVALID_CREDENTIALS`；认证请求校验失败统一返回 422 `INVALID_REQUEST` Problem 且不回显输入。

## 非目标
- 不改变登录成功、密码、会话、CSRF/CORS、限频、RBAC、DB、依赖；不实现其他接口。

## 允许修改路径
- `apps/api/app/auth/service.py`
- `apps/api/app/factory.py`
- `apps/api/tests/auth/test_auth.py`
- `tasks/TASK-AUTH-001.md`
- `tasks/TASK-AUTH-002.md`
- `tasks/TASK-AUTH-003.md`
- `tasks/TASK-REVIEW-AUTH-001.md`
- `tasks/TASK-REVIEW-AUTH-002.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- approved 规范、migration、依赖文件、其他业务、`sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB/依赖：无。
- API：按 approved OpenAPI v0.2 实现 `INVALID_CREDENTIALS` 401 与 `INVALID_REQUEST` 422 Problem；不新增其它字段、码或 endpoint。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：实现已批准契约，不再借用旧码。

## 验收
- 不存在账号与错误密码除 trace_id 外响应完全一致，均为 401 Problem `INVALID_CREDENTIALS`。
- 73-byte/多字节超限及 schema 校验错误均为 422 Problem `INVALID_REQUEST`；响应无原始输入。
- AUTH 全量真实 PostgreSQL/Redis 测试零 skip；全套门禁通过；独立审查无 P0/P1。

## 变更预算
- max_files：9
- expected_prod_lines：40
- expected_test_lines：100

## 必须运行的测试命令
- `python -m pytest tests/auth tests/test_app.py -q -ra`
- `python -m pytest -q -ra`
- Ruff check/format、mypy、pip check

## 回滚方法
- 回退本任务实现提交；规范仍保留为后续实现要求。

## 强制停止条件
- 需要新错误码/schema/依赖/DB、改变成功路径、修改冻结断言方向或超过预算时停止。

## 交付证据
- commit / PR：`b8c7fc5`（认证错误契约实现快照）
- 修改文件清单：`apps/api/app/auth/service.py`、`apps/api/app/factory.py`、`apps/api/tests/auth/test_auth.py`；连同任务建立文件按基线 `2c46060..b8c7fc5` 共 6/9 路径
- 测试命令及结果：一次性真实 PostgreSQL 16 + Redis 7 环境中 AUTH 切片 15 passed / 0 skipped；全套 27 passed / 0 skipped
- lint / typecheck：Ruff check/format、mypy、pip check 全部通过
- DB 迁移验证：无迁移
- 验收证据：错误密码与不存在账号均返回 401 `INVALID_CREDENTIALS`，除 `trace_id` 外 Problem 字段一致；AUTH 请求校验失败返回 422 `INVALID_REQUEST`，未返回 Pydantic `input`/`ctx` 或原始输入；独立审查 P0=0、P1=0
- 变更预算实际值：6/9 文件；生产新增 14/40 行、删除 7 行；测试新增 21/100 行、删除 1 行，未超预算
- 未解决风险：无；审查指出的 P2 仅为本交付证据未回填，现已补齐
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`b8c7fc5`
- 状态：Closed
- 关闭结论：测试通过、规范影响为 none、spec_sync=clean、verified_commit 为真实实现快照，四项关闭门禁全部满足。
