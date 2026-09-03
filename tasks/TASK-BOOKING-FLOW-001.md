# TASK-BOOKING-FLOW-001 可操作预约主流程

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 1.0 / architecture 0.2 / security 0.1 / OpenAPI 0.2 / test_plan 0.2（均 approved）
- implementation baseline：`0e5f6602664f1fae3799f6ed67b4bcbef3fbebec`（BOOKING-001 完整关闭快照）

## 精确规范引用
- SRS §3.3、§3.4、§3.5、§5.1、§5.2、§5.3、§7、§8
- domain-model v1.1.5 §6.7 AppointmentSlot
- OpenAPI `login` / `getCurrentUser` / `getSlotSnapshot` / `previewAppointment` / `createAppointment`
- test-plan TC-AUTH-002/003/008、TC-UI-004、TC-APT-001/002/003、TC-SEC-004

## 目标
- 交付桌面端可操作主流程：登录 → 查看真实 14 天 Slot 快照 → 选择连续三格 → 填写预约信息 → 三分钟预览确认 → 原子创建预约。
- 提供可重复使用的本地 PostgreSQL/Redis 开发环境与显式 demo seed，避免每轮重新下载临时服务。

## 非目标
- 不实现注册/找回密码、SSE、改期/取消、管理后台、通知 Worker、SMTP/IMAP/飞书、RAG/LLM、生产部署或 Agent 自动预约。
- 不生成虚假线上数据；demo seed 仅用于本地开发库。

## 允许修改路径
- `apps/api/app/appointments/**`
- `apps/api/app/factory.py`
- `apps/api/tests/appointments/**`
- `apps/api/scripts/**`
- `apps/web/**`
- `tests/web-shell/**`
- `vite.config.ts`
- `docker-compose.dev.yml`
- `tasks/TASK-BOOKING-FLOW-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- `docs/**`、`apps/api/migrations/**`、`docs/baseline.yml`
- `apps/api/app/auth/**`、依赖清单与锁文件
- `C:/Users/<user>/Desktop/sleep202603-an/**`

## 已批准的 DB / API / 依赖变更
- DB schema / migration：无；只读写既有 `users`、`auth_sessions`、`appointment_slots`、`appointments` 及 BOOKING-001 已批准表。
- API：不改变契约；实现既有 `GET /slots/snapshot`，复用既有四个 operationId。
- 依赖：无新增；复用现有 FastAPI/SQLAlchemy/React/Vite。
- 本地基础设施：新增可删除的 Docker Compose PostgreSQL/Redis 与显式 demo seed；不得连接生产环境。

## 规范影响评估
- behavior_change：false（从未实现推进到符合已批准规范）
- affected_specs：srs=none；domain_model=none；openapi=none；security=none；test_plan=none
- reason：实现已批准、尚未落地的既有行为，不改变用户可观察契约。

## 功能验收
- 登录成功后显示 `getCurrentUser` 身份与本周/下周真实 Slot；未登录显示登录入口。
- 仅 `available` 且满足预约窗口的连续三格可选；黄格仅前端态。
- 预览不写库；确认创建成功后刷新快照，三格显示 booked/self。
- API 错误以用户可理解的状态呈现，不吞掉 Problem code。

## 安全与隐私验收
- Cookie、CSRF、同源与 interviewer RBAC 复用 AUTH/BOOKING 已验证实现。
- 他人 booked Slot 只返回 `ownership=other`，不返回 appointment_id 或 PII。
- 前端不记录密码、token、会议号、电话或密钥到日志/持久存储。

## 性能验收
- Slot 快照本地真实 PostgreSQL P95 ≤500ms；前端选段反馈 <100ms。

## 变更预算（change_budget）
- max_files：14
- expected_prod_lines：900
- expected_test_lines：450

## 必须运行的测试命令
- 后端 Slot/预约真实 PostgreSQL+Redis 测试；`pytest -q`。
- `ruff check .`、`ruff format --check .`、`mypy app`、`pip check`。
- `pnpm test`、`pnpm typecheck`、`pnpm build`、Playwright 桌面端主流程。

## 回滚方法
- `git revert` 本任务实现提交；`docker compose -f docker-compose.dev.yml down -v` 删除本地开发数据。

## 强制停止条件
- 需要新 schema/migration、公开 API 字段、依赖、鉴权/加密策略或外部通知。
- 冻结测试失败且必须降低断言、超出预算或发现 approved 工件冲突。

## 交付证据
- commit / PR：主实现 `28530b4`；独立审查发现的唯一 P1（创建成功后刷新失败被误报为预约失败）已于最终实现快照 `ccd698b` 修复
- 修改文件清单：`apps/api/app/appointments/{models,router,service}.py`、`apps/api/app/factory.py`、`apps/api/tests/appointments/test_booking.py`、`apps/api/scripts/seed_demo.py`、`apps/web/{main.tsx,appointment.css}`、`tests/web-shell/shell.test.ts`、`vite.config.ts`、`docker-compose.dev.yml`、本 TASK、`PROJECT_STATE.md`
- 测试命令及结果：隔离真实 PostgreSQL 16 + Redis 7 回归 `pytest tests/appointments tests/auth tests/migrations -q` → 53 passed / 0 skipped；基础测试 → 5 passed；`pnpm test` → 1 passed；桌面端浏览器真实流程 → pass
- lint / typecheck：`ruff check .` / `ruff format --check .` / `mypy app` / `pip check` / `pnpm typecheck` / `pnpm build` 全部 pass
- DB 迁移验证：无新 migration；隔离测试库由既有 Alembic `0001 → 0002 → 0003` upgrade 成功；本地 `jianli_dev` seed 成功
- 验收证据：已实测登录 → 真实 14 天时段 → 连续三格 → 信息表单 → 三分钟预览 → 原子创建；返回日历后三格显示 `booked/self` 且标记“已预约（本人）”；他人预约仅返回 `ownership=other`，无 `appointment_id`/PII；浏览器无 console error/warning
- 变更预算实际值：13 个允许路径（上限 14）；产品代码约 205 新增行，测试约 80 新增行，均未超预期
- 未解决风险：无 P0/P1；日历刷新失败时保留“预约已创建”事实并提供重试，不会诱导重复提交
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`ccd698b8cfffac7a5036e9d358000e98c2fcb1d4`
- 状态：Closed

## 关联
- 前置：TASK-BOOKING-001（Closed）
- 验收：TC-AUTH-002/003/008、TC-UI-004、TC-APT-001/002/003、TC-SEC-004
