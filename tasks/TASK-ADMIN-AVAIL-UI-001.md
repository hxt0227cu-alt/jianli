# TASK-ADMIN-AVAIL-UI-001 admin 可用时段设置 UI（实现已批准规格）

> **状态：draft（草案，待用户评审后批准）**
> 核心：admin 后台补「时段设置」入口——列表/新建/修改/删除 availability-overrides（设「强制不可用/强制可用」时段）。**后端 API 已实现并已批准（OpenAPI v0.3），本次仅前端补齐**，属已批准规格（MVP 硬规则⑧ + UI 线框 A4 + UC-13）闭环，非新需求。

## 任务类型
- implementation  # 前端功能补齐（后端零改动）

## 基线版本与基线 commit
- baseline：SRS 1.2 / 领域模型 1.1.5 / architecture 0.2 / OpenAPI 0.3 / UI 线框 1.0（取自 `docs/baseline.yml`）
- 基线 commit：`dc25488`（本任务创建时 master HEAD）

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` A4（「不可约时段 / 公告管理」admin 页）
- `docs/requirements/use-cases.md` UC-13（候选人标记不可约时段——时段部分）
- `docs/requirements/SRS.md` §3.4（owner 公告/不可约展示）、§3.9（admin）
- `docs/api/openapi.yaml` `listAvailabilityOverrides` / `createAvailabilityOverride` / `updateAvailabilityOverride` / `deleteAvailabilityOverride`（**契约已批准，直接消费**）
- `docs/baseline.yml` mvp_hard_rules ⑧（管理不可约时段=硬性 MVP）

## 需求来源
- 用户 2026-08-18 决策：「admin 设置什么时候有空/没空」功能要补 UI（后端已做，界面无入口）
- 属 MVP 硬规则⑧ / UI 线框 A4 / UC-13 已批准规格的**实现闭环**，非新增需求

## 目标
在 `apps/web/main.tsx` admin 页新增「时段设置」tab：
1. **列表**：GET `/admin/availability-overrides` 展示现有 override（时间范围 + action + reason + 创建时间）
2. **新建**：POST——选日期/起止时间 + action（`force_unavailable` 不可约 / `force_available` 恢复可约）+ reason 备注
3. **修改 / 删除**：PATCH / DELETE 单条
4. 全部走 admin 既有 CSRF + owner_admin 鉴权模式（main.tsx 已有 `api()` 封装 + `X-CSRF-Token`）
5. 交互形态：建议复用 main.tsx 现有日历网格样式（7 列周视图）或简化日期+时间区间选择器，以改动最小为准

## 非目标（明确排除）
- **公告编辑**（UC-13 后半、UI 线框 A4「公告管理」）：后端无实现、无表、契约有定义 → **另列 TASK（需 DB 新表 = 人审批项）**，本次不做
- 不改后端任何代码（availability-overrides 服务已完整：校验联动/槽位重算/审计）
- 不改预约流程 / SSE / interviewer 侧 UI
- 不做图形化拖拽标红等高级交互（先表单化，MVP 够用）

## 允许修改路径
- `apps/web/main.tsx`（admin 页新增 tab + 表单/列表组件）
- `apps/web/*.css`（时段设置 tab 样式，若需）
- `apps/web/dist-check/*`（如涉及前端门禁脚本）
- `tasks/TASK-ADMIN-AVAIL-UI-001.md`（本任务单）

## 禁止修改路径
- `apps/api/**`（后端零改动）
- `docs/**` 规范工件（本次不涉及规格变更）
- `docker-compose*.yml` / `deploy/**` / `scripts/deploy.sh`（部署栈不动）

## 已批准的 DB / API / 依赖变更
- **DB**：无（无 schema 变更）
- **API**：无契约变更（复用 OpenAPI v0.3 已批准的 availability-overrides 4 个 operationId）
- **依赖**：无新增 npm/pip 依赖

## 规范影响评估（spec impact）
- behavior_change：**false**（实现已批准规格的 UI 入口；后端行为、契约、流程均不变）
- affected_specs：全部 none
- reason：MVP 硬规则⑧ / UI 线框 A4 / UC-13 已批准，缺的只是前端消费已批准 API 的页面

## 功能验收
- `pnpm typecheck` + `pnpm build`（WSL）通过
- admin 登录后「时段设置」tab 可见：新增 force_unavailable 时段 → 预约日历对应格变红（SSE/刷新后）；删除后恢复
- 无 CSRF token 的操作被拒（复用既有防护，不额外测）
- 变更预算：max_files ≤ 4 / prod 预计 ≤ 300 行 / 无测试文件新增（前端现有门禁为准）

## change_budget
- max_files：4
- expected_prod_lines：≤ 300（main.tsx 增量）
- expected_test_lines：0（前端门禁为 typecheck + build）

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要改后端 / 新增依赖 / 改契约 → 停止
- 超出 change_budget → 拆任务
- 公告编辑被混入本任务 → 停止（另行列）

## 交付证据（任务关闭前必须填写）
- commit / PR：<待回填>
- 修改文件清单：<与「允许修改路径」逐一对照>
- 测试命令及结果：<pnpm typecheck / build 结果>
- 验收证据：<admin 时段设置操作截图或接口响应>
- 变更预算实际值：<max_files / 行数>
- 是否偏离 TASK：<否 / 偏离项>
- 规范影响结论：none（行为未变）
- spec_sync：clean
- verified_commit：<待回填>

## 关联
- 后端依据：TASK-DEPLOY-001 之后已存在的 availability-overrides 实现（admin router/service，契约 OpenAPI v0.3）
- 后续：公告编辑 TASK（DB 审批）；验证码数字码 CR（TASK-CR-VERIFY-CODE-001，独立）
