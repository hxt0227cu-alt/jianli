# TASK-AUTH-002 AUTH-001 独立审查修正

## 任务类型
- implementation / security remediation

## 当前阶段
- 状态：Closed
- 来源：TASK-REVIEW-AUTH-001 对 `f5fd75c` 的独立审查。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.2 / architecture 0.2 / security 0.1 / OpenAPI-SSE 0.1 / test_plan 0.1（均 approved）
- 基线 commit：`f5fd75c`

## 精确规范引用
- `docs/requirements/SRS.md §5.6`、`§8`
- `docs/design/security.md §3`、`§7`、`§11`、`§12`
- OpenAPI operationId：`login`、`logout`、`getCurrentUser`
- 冻结测试：TC-AUTH-002/003/004/006/007/008

## 目标
- 修正账号锁定 TTL、CORS、会话旋转与认证安全日志；把错误契约缺口隔离为 Change Request，不在实现中借用错误码。

## 非目标
- 不新增错误码，不修改 approved SRS/OpenAPI；不实现注册、找回、预约、通知或其他业务。

## 允许修改路径
- `apps/api/app/auth/**`
- `apps/api/app/factory.py`
- `apps/api/tests/auth/**`
- `tasks/TASK-AUTH-002.md`
- `tasks/TASK-REVIEW-AUTH-001.md`
- `PROJECT_STATE.md`（仅任务态与证据）

## 禁止修改路径
- approved 规格、migration、`apps/web/**`、`sleep202603-an/**`。

## 已批准的 DB / API / 依赖变更
- DB/依赖：无。
- API：仅补齐 approved CORS/Origin、现有会话旋转和既定 Problem 响应；不得新增 error code/schema/endpoint。
- 安全：日志仅含 HMAC 账号标识、请求 ID、结果类别、截断 IP；不得记录邮箱、密码、Cookie、token、hash 或密钥。

## 规范影响评估
- behavior_change：false
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：使实现重新符合既有 approved 安全与行为规范；错误码缺口另走 Change Request。

## 验收
- 第 5 次账号失败把锁定 TTL 重置为完整 15 分钟，锁定期间正确密码也被拒绝。
- CORS 仅允许配置 origin 且允许凭证，不产生通配凭证组合。
- 已登录状态再次登录时旋转并吊销旧会话。
- 所有认证拒绝产生脱敏结构化安全事件。
- 真实 PostgreSQL/Redis AUTH 测试与全套门禁均零失败、零跳过。

## 变更预算
- max_files：7
- expected_prod_lines：220
- expected_test_lines：300

## 必须运行的测试命令
- `python -m pytest tests/auth tests/test_app.py -q -ra`
- `python -m pytest -q -ra`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python -m mypy app`
- `python -m pip check`

## 回滚方法
- 回退本任务修正提交，保留 `f5fd75c` 历史快照。

## 强制停止条件
- 需要新增/修改 error code、公开 schema、依赖、DB 或超过预算时停止并走 Change Request/拆任务。

## 交付证据
- commit / PR：`72cdb9a`（主要审查修正）→ `4fcb316`（422 脱敏/CORS 通配拒绝）→ `e796ebe`（脱敏处理器限于 auth 路由）
- 修改文件清单：`app/auth/rate_limit.py`、`app/auth/repository.py`、`app/auth/router.py`、`app/auth/service.py`、`app/factory.py`、`tests/auth/test_auth.py`、本任务单，共 7 路径
- 测试命令及结果：真实 PostgreSQL/Redis 环境 `python -m pytest -q -ra` → 27 passed / 0 failed / 0 skipped；AUTH 切片 → 15 passed
- lint / typecheck：Ruff check/format pass；mypy pass；pip check pass
- DB 迁移验证：无迁移
- 验收证据：第 5 次失败真实 Redis `Retry-After>=895`；锁定期正确密码被拒；CORS 精确 origin/credentials 与 wildcard fail-fast；旧会话与新会话同事务旋转；422 不回显密码；安全事件仅含 HMAC 标识/请求 ID/结果/截断 IP。
- 变更预算实际值：7/7 文件；生产增量 152/220 行；测试增量 91/300 行，未超预算
- 未解决风险：无；原错误契约缺口已由 TASK-AUTH-CONTRACT-001 获用户批准，并由 TASK-AUTH-003 在 `b8c7fc5` 完成适配
- 是否偏离 TASK：否；已在强制停止点停止契约修改
- 规范影响结论：updated（Change Request 已由 TASK-AUTH-CONTRACT-001 完成并批准）
- spec_sync：clean
- verified_commit：`b8c7fc5`（包含本任务安全修正与后续已批准错误契约适配的最终验证快照）
- 状态：Closed
- 关闭结论：安全修正测试通过；契约阻塞已按 Change Request 流程解除；spec_sync=clean；最终验证快照真实存在。
