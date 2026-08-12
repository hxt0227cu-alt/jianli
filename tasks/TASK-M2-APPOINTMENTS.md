# TASK-M2 SSE 实时刷新（slots 事件流）

> 合并同域主线：SSE 实时刷新为单一实现任务（端点 + 前端订阅）。
> **治理节奏（接手 Codex 必读，与 TASK-M1 一致）**：① 合并同域主线；② 风险分级——本任务复用已验证 `slot_snapshot` 读路径与 `SseRegistry` 连接上限，**不单列独立 REVIEW 任务**，仅内联自审（连接上限/ownership 脱敏/心跳/断线释放）；③ 交付证据一次写全（关闭时不补纯回填 commit）；④ 验证批处理（一轮 pytest+ruff+mypy+pnpm typecheck/build/test）。

## 任务类型
- implementation（含同域前端订阅）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2（均 approved）
- 基线 commit：`cb0fa6f`（M1 状态更新后 HEAD，接手 Codex 代码，工作区干净）

## 精确规范引用（AI 只读取这些章节）
- sse.md v0.1 §1（通用帧）、§2（Slot 实时流 `GET /slots/events`、连接算法、ownership 仅 none/self/other）、§4（恢复与代理：无缓冲、心跳 15s、45s 断线、指数退避）
- architecture 0.2 §5.1（提交派生，无消息中间件）、§5.2（resource_version/stream_seq 单调）、§5.3（先订阅再拉快照）、§5.4（强制重拉触发）、§5.5（多实例一致）、§5.7（连接约束 ≤2、降级）
- SRS 1.3 §4.3（SSE 推送行为、≤2s 到达、断线重拉快照）、§5.6（限频独立命名空间）
- TC-SSE-001~005（提交后≤2s 到达、缓冲/快照重放、断线/漏序/跳跃强制重拉、ownership 不泄露 PII、同账号第 3 连接拒绝）

## 需求来源
- R8（动态面试表实时刷新）、R13/R18（事件近实时同步）、UC-07（SSE 不可用轮询降级）；PRD §4.5「实时刷新与一致性」

## 目标
一次性交付 Slot SSE：`GET /slots/events` 端点（interviewer 会话、无 CSRF）+ 前端 `InterviewView` 的 `EventSource` 订阅，使课表网格在他人预约/改期/取消后 ≤2s 刷新，且不泄露他人 PII。

## 非目标（明确排除）
- 不引入 Redis Pub/Sub 或任何消息中间件（architecture §5.1 明确 MVP 不用）
- 不做 AI 回答流 `POST /api/v1/answers:stream`（独立任务，RAG 域）
- 不新增迁移/表/列/索引（仅进程内 `SseRegistry` 连接计数）
- 不改加密/密钥/鉴权策略

## 允许修改路径
- `apps/api/app/appointments/sse.py`（新增）
- `apps/api/app/appointments/service.py`（新增 `SseRegistry` + `self.sse_registry` 字段）
- `apps/api/app/appointments/router.py`（注册 `GET /slots/events`）
- `apps/web/main.tsx`（`InterviewView` 内 `EventSource` 订阅 + `useRef` 导入）
- `PROJECT_STATE.md`（仅当前任务段）

## 禁止修改路径
- `apps/api/app/appointments/crypto.py`、`runtime.py`（密钥/加密不变）
- 迁移文件（无 schema 变更）
- auth 域、预约写路径、通知 Worker

## 已批准的 DB / API / 依赖变更
- DB 迁移：**无**（复用 `appointment_slots` 现有列）
- API：新增 operation `streamSlotEvents`，实现已批准 sse.md v0.1 契约（非新增契约字段，属契约实现）
- 依赖：**无新增**

## 规范影响评估（spec impact）
- behavior_change：true（新增 SSE 用户可观察行为）
- affected_specs：srs/domain_model/openapi/security/test_plan 均为 none（实现已批准 SSE 契约）
- reason：实现 approved sse.md v0.1 + architecture §5，不改变规范；无需 Change Request。
- 分类：实现 approved 契约（非重构/非 bugfix/非变更规范）。

## 功能验收
- `GET /slots/events` 连上即发 `stream.ready`（stream_seq=0）；客户端随后拉 `/slots/snapshot` 并按 `resource_version` 收敛缓冲
- 变更帧 `slot.changed` 仅含 `id/start_at/end_at/status/resource_version/ownership`；`ownership` ∈ none/self/other（self = `appointment.user_id ==  viewer`）；**不含 appointment_id / 公司 / 会议号 / 联系人 / 备注**（TC-SSE-004）
- 轮询周期 T=1s，变更 ≤2s 到达客户端（TC-SSE-001）
- 心跳 `event: heartbeat` 每 15s（TC-SSE-003 心跳缺失触发重拉）
- 同账号第 3 条连接拒绝 429 RATE_LIMITED（TC-SSE-005）
- 断线/漏序/resource_version 跳跃/heartbeat 超时 → 客户端重拉快照（sse.md §4；前端 `onerror`/`resync.required` 调 `loadSlots`）
- 前端按 `resource_version` 收敛单格更新（`incoming.resource_version > slot.resource_version`）

## 安全与隐私验收
- 端点要求 interviewer Cookie 会话（复用 `viewer`）；GET 不需 CSRF
- `ownership` 严格脱敏，他人红格不泄露 PII
- SSE 不引入 Redis 读取，故不受 security §38 Redis 故障 fail-closed 影响（slot_snapshot 只读 PG）

## 性能验收
- 每连接 1s 轮询一次（窗口 ≈350 行 / 实例）；≤2 连接/账号；轮询占 DB 负载远低于 architecture §5.6 升级阈值

## 变更预算（change_budget）
- max_files：6
- expected_prod_lines：~90（后端 sse.py）+~30（service/router 增量）+~20（前端）
- expected_test_lines：~80

## 必须运行的测试命令
- `pytest apps/api/tests/appointments/test_sse.py`（需真实 PG；连接上限/心跳/ownership 脱敏）
- `ruff check apps/api app` + `mypy apps/api/app`
- `pnpm -C apps/web typecheck && pnpm -C apps/web build && pnpm -C apps/web test`

## 回滚方法
- 纯代码变更，无迁移；回滚 = `git revert` 本任务 commit

## 强制停止条件
- 出现未列明变更（新依赖/新迁移/改加密策略/改公开 API 契约字段）→ 立即停止报告
- 超出 change_budget（max_files>6）→ 拆任务
- 冻结 TC 断言失败 → 停止，不改断言/不 skip

## 交付证据（关闭前一次写全）
- commit / PR：`<回填>`
- 修改文件清单：<回填>
- 测试命令及结果：<回填；逐条 TC-SSE-001~005>
- lint / typecheck：<回填>
- DB 迁移验证：无
- 验收证据：<回填接口响应样例 / 前端订阅行为>
- 变更预算实际值：<回填>
- 未解决风险：<回填；sandbox 无法跑真实 PG/venv/node 验证批处理>
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：<回填真实 sha>
- 关闭门禁：① 测试通过 ② 规范影响 none ③ spec_sync clean ④ verified_commit 已记录

## 关联
- Change Request：无
- 测试任务：TC-SSE-001~005
- 后续主线：M3 通知 Worker（Outbox 消费，凭运行时 SMTP 163 凭据）/ M4 注册找回 / M5 管理后台
