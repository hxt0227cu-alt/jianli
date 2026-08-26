# TASK-SLOT-MATERIALIZE-001 生产预约 Slot 物化

## 任务类型
- implementation
- infrastructure
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.4 / 用例规约 1.7.2 / 领域模型 1.1.6 / SRS 1.5
- 基线 commit：`5ba111c`

## 精确规范引用
- `docs/requirements/SRS.md §3.4`
- `docs/design/domain-model.md §6.7 / §6.9`
- 用户于 2026-08-26 对 TASK-SLOT-MATERIALIZE-001 的显式批准

## 目标
提供幂等生产 Slot 物化 CLI，以官方年度日历生成滚动 8 周时段，并接入部署前置与每日 cron 运维流程。

## 非目标
- 不新增迁移、公开 API、外部运行时依赖或在线日历服务。
- 不改预约并发、加密、RBAC 或 owner override 语义。

## 允许修改路径
- `apps/api/app/appointments/materialize_slots.py`
- `apps/api/app/appointments/calendars/2026.json`
- `apps/api/tests/appointments/test_slot_materializer.py`
- `docker-compose.prod.yml`
- `scripts/deploy.sh`
- `docs/deploy/阿里云部署指南.md`
- `tasks/TASK-SLOT-MATERIALIZE-001.md`
- `PROJECT_STATE.md`

## 禁止修改路径
- migrations、公开 API/OpenAPI、依赖清单、预约写事务

## 已批准的 DB / API / 依赖变更
- DB：无，复用 `appointment_slots` / `availability_overrides`。
- API：无。
- 依赖：无。
- 基础设施：生产 compose 增一次性 Slot 物化服务；API/Worker 在其成功后启动；指南增加每日维护命令。

## 规范影响评估
- behavior_change：false（实现 SRS 既有可预约日历物化要求）
- srs/domain/openapi/security/test_plan：none
- spec_sync：clean

## 功能、安全与性能验收
- 每天 09:30–22:00 生成 25 个 30 分钟 Slot；今天及以前、周末、法定假日、午晚餐不可约，调休工作日可约。
- owner override 最终优先；`force_unavailable` 冲突时更严格者优先。
- 重跑幂等；不得覆盖 booked / owner_locked，不为未变化 free slot 增 version。
- 缺少目标年份的官方日历时 fail closed，不把未知节假日当普通工作日。
- 8 周物化在单事务内完成，最多 1400 行，无 N+1 查询。

## 变更预算
- max_files：8
- expected_prod_lines：220
- expected_test_lines：180

## 必须运行的测试命令
- `pytest tests/appointments/test_slot_materializer.py -v`（含真实 PG）
- 本任务 Python 文件 ruff；`mypy app`
- `docker compose -f docker-compose.prod.yml config`
- shell 静态检查 `bash -n scripts/deploy.sh`

## 回滚方法
- 回退实现/compose 提交；已物化 free/unavailable 行可保留，由旧系统读取；不删除预约数据。

## 强制停止条件
- 遵循 `AGENTS.md §2`。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无迁移
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
- 关闭门禁：未关闭

## 关联
- 官方日历来源：国务院办公厅《国务院办公厅关于2026年部分节假日安排的通知》（国办发明电〔2025〕7号）
