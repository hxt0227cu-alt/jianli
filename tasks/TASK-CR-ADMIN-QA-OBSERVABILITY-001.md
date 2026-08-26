# TASK-CR-ADMIN-QA-OBSERVABILITY-001 管理端问答客观可观测字段规范批准

> 状态：Approved / Closed（2026-08-26）。用户明确批准 3 个字段、0009 可逆迁移和管理端展示，并明确删除主观 `quality_score`；本任务只同步规范，不写实现。

## 基线与引用

- baseline commit：`2235442`
- PRD 2.3.4 §4.7 / §8.6；SRS 1.4 §3.9 / §7；domain-model 1.1.5 §6.13；OpenAPI 0.4
- 用户批准文本：2026-08-26 对 `TASK-ADMIN-QA-OBSERVABILITY-001` 第 1 项授权

## 目标

- domain-model 1.1.6：Message 新增 nullable `grounded`、`citations_count`、`latency_ms`，只记录客观事实。
- OpenAPI 0.5：登记既有 admin 对话列表、消息详情、AIQA 统计 3 个 operation；响应包含上述观测字段。
- 历史消息三个字段为 null；统计只以 `grounded IS NOT NULL` 的 assistant 消息作为 grounded_rate 分母。
- 明确禁止把规则硬编码的 `quality_score` 当作回答质量评估。

## 非目标

- 不修改代码、迁移、测试或 UI。
- 不新增 LLM-as-judge、外部依赖、工具 trace、Prompt 或鉴权行为。
- 不修改对话内容、留存期或 owner_admin 只读权限。

## 允许修改路径

- `docs/design/domain-model.md`
- `docs/requirements/SRS.md`（仅 domain based_on 影响同步）
- `docs/api/openapi.yaml`
- `docs/baseline.yml`
- `tasks/TASK-CR-ADMIN-QA-OBSERVABILITY-001.md`
- `PROJECT_STATE.md`

## 已批准的 DB / API / 依赖变更

- DB：下游 0009 在 `conversation_messages` 新增三个 nullable 字段；非负 CHECK；无索引。
- API：登记 `adminListConversations`、`adminListConversationMessages`、`getAIQAStats` 及其响应 Schema；只读 owner_admin。
- 依赖：无。

## 规范影响评估

- domain-model：1.1.5 → 1.1.6（approved）
- SRS：行为不变，仅 based_on 1.1.5 → 1.1.6；版本保持 1.4 approved
- OpenAPI：0.4 → 0.5（approved）
- 其他工件：none；spec_sync=clean

## change_budget

- max_files：6
- expected_spec_lines：≤180

## 验收

- YAML 可解析；operationId 全局唯一。
- 三字段均 nullable；`citations_count >= 0`、`latency_ms >= 0`。
- 无 `quality_score` Schema/领域字段。
- 实现必须另由 `TASK-ADMIN-QA-OBSERVABILITY-001` 承载。

## 交付证据

- commit / PR：`7b44781`（规范批准与契约快照）
- 修改文件：domain-model / SRS based_on / OpenAPI / baseline / 本任务 / PROJECT_STATE
- 验证结果：OpenAPI 静态结构、37 个 operationId 唯一、三 operation 与三字段存在、无 `quality_score` Schema；`git diff --check` PASS
- 规范影响：domain-model 1.1.6 / OpenAPI 0.5 approved；SRS 1.4 behavior unchanged
- spec_sync：clean
- verified_commit：`7b44781`
