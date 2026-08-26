# TASK-APPOINTMENT-WINDOW-001 过期预约完成与三自然周日历实现

> 状态：In Progress；依据已批准 `TASK-CR-APPOINTMENT-WINDOW-001`。

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.5 / 用例规约 1.7.3 / 领域模型 1.1.7 / SRS 1.6 / OpenAPI 0.7 / 测试计划 0.4
- 基线 commit：`bc430ca`

## 精确规范引用
- `docs/requirements/SRS.md §3.4 / §3.5 / §3.6 / §3.9 / §6.2`
- `docs/design/domain-model.md §5 / §6.6`
- `docs/api/openapi.yaml` `getSlotSnapshot`
- `docs/test/test-plan.md` TC-UI-006 / TC-APT-012

## 需求来源
- 用户 2026-08-26 当前请求；已批准 CR `TASK-CR-APPOINTMENT-WINDOW-001`。

## 目标
1. 集合式、幂等完成过期 active 预约，维护命令与预约读写路径均可收敛。
2. Slot 快照支持 offset 0/1/2 且 interviewer/owner_admin 可读。
3. 预约、改期与管理端统一裁剪为明天起 15 日窗口。
4. 管理端显示同源 Slot 网格，点击格子带入精确 30 分钟 override 表单。
5. 预约日历充分铺满无聊天栏主区并提升关键字号。

## 非目标
- 不新增迁移、状态枚举、公开 operationId、响应字段或外部依赖。
- 不改变 Slot 并发锁、预约加密、通知、Agent 工具权限。
- 不新增公告编辑功能。

## 允许修改路径
- `apps/api/app/appointments/lifecycle.py`
- `apps/api/app/appointments/service.py`
- `apps/api/app/appointments/materialize_slots.py`
- `apps/api/app/appointments/router.py`
- `apps/api/tests/appointments/**`
- `apps/web/main.tsx`
- `apps/web/my-appointments.tsx`
- `apps/web/appointment.css`
- `tests/web-shell/shell.test.ts`
- `tasks/TASK-APPOINTMENT-WINDOW-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、依赖清单、认证/加密/通知实现、AIQA、其他规范工件。

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化；批准更新既有 `appointments.status/completed_at` 数据。
- API：`getSlotSnapshot.week_offset` 允许 0/1/2；读取角色允许 interviewer/owner_admin；响应 Schema 不变。
- 依赖：无。

## 规范影响评估
- behavior_change：true（已由批准 CR 完成规范同步）
- affected_specs：SRS/domain/OpenAPI/UI/test_plan = updated
- reason：实现批准后的用户可观察行为；spec_sync=clean。

## 功能验收
- TC-APT-012：过期 active → completed、completed_at=end_at、幂等、未过期保持 active、无取消事件。
- TC-UI-006：三个 offset、15 日裁剪、管理端同源网格与精确格子选择、关键字号≥12px。
- 当前本地 8 月 24 日旧预约运行维护命令后变 completed，可再次预约。
- 现有 override CRUD 仍可设置任意对齐时间段并即时物化。

## 安全与隐私验收
- owner_admin 快照仍不返回 appointment_id/公司/联系方式；ownership 使用既有隐私投影。
- interviewer 归属与 CSRF/RBAC 不放宽。

## 性能验收
- 过期完成单条集合 UPDATE，无逐行 N+1。
- 前端最多并发拉取 3 个自然周（525 个 Slot），无额外轮询频率。

## 变更预算
- max_files：12
- expected_prod_lines：260
- expected_test_lines：220

## 必须运行的测试命令
- `pytest tests/appointments/test_booking.py tests/appointments/test_slot_materializer.py -v`（真实 PG）
- `ruff check . && mypy app`
- `npm test -- --run && npm run typecheck && npm run build`
- 真实本地 DB 状态与 HTTP 快照检查。

## 回滚方法
- 回退实现提交；已转 completed 的真实过期预约符合旧枚举且无需逆转；无 schema 回滚。

## 强制停止条件
- 遵循 `AGENTS.md §2`；冻结 TC 失败、超预算或需新增未批准字段/API/依赖立即停止。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：否
- 规范影响结论：updated（CR 已批准）
- spec_sync：clean
- verified_commit：待回填

## 关联
- Change Request：`TASK-CR-APPOINTMENT-WINDOW-001`
- 测试：TC-UI-006 / TC-APT-012
