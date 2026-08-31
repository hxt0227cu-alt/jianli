# TASK-CR-AIQA-LITCHI-SCOPE-012 Litchi 问答项目键契约校正

> 状态：Approved / Implemented（2026-08-31）。用户已要求页面二包含 Litchi 且右侧问答按当前项目过滤；审查发现运行时与前端已支持，但 OpenAPI 枚举漂移。

## 任务类型
- change-request / documentation（仅校正既有行为的契约）

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / SRS 1.9 / OpenAPI-SSE 0.9 / test-plan 1.3
- 基线 commit：`6a1df19362f9dc3cc40646be66df7fe0842bfa01`

## 精确规范引用
- `docs/api/openapi.yaml` `AnswerRequest.project_key`
- `docs/test/test-plan.md` TC-UI-003、TC-AI-001
- 运行事实：`apps/api/app/aiqa/models.py` `ProjectKey`、`apps/web/main.tsx` `PROJECT_API_KEYS`

## 目标
- 在 `AnswerRequest.project_key` 登记运行时已经接受的 `litchi`，消除生成客户端和契约校验漂移。
- OpenAPI 文件 0.7.0→0.8.0，OpenAPI-SSE 基线 0.9→1.0；test-plan 1.3→1.4 仅完成 impact review。

## 非目标
- 不新增项目、不改变检索、路由、Prompt、前端内容、API 路径、字段、状态码或 SSE 帧。
- 不修改生产代码、测试断言、DB、依赖、权限或评测阈值。

## 允许修改路径
- `docs/api/openapi.yaml`
- `docs/baseline.yml`
- `docs/test/test-plan.md`
- `tasks/TASK-CR-AIQA-LITCHI-SCOPE-012.md`

## 已批准的 DB / API / 依赖变更
- DB：无。依赖：无。
- API：`AnswerRequest.project_key` enum 补登记既有值 `litchi`；无新字段或运行行为。
- 治理：OpenAPI-SSE 0.9→1.0；test-plan 1.3→1.4，冻结 TC 数量、断言与阈值不变。

## 规范影响评估
- behavior_change：false
- affected_specs：openapi=update / test_plan=impact-reviewed / srs=none / domain=none / security=none
- reason：低优先级契约追认已经批准并实现的三项目问答范围。

## 验收
- OpenAPI 3.1 YAML 可解析，`project_key` 精确包含 `jianli`、`sleep202603_an`、`litchi`。
- test-plan 仍为 78 个冻结 TC，所有阈值不变，based_on 指向 OpenAPI-SSE 1.0。
- 本提交不包含任何 `apps/**`、测试或迁移文件。

## 变更预算
- max_files：4
- expected_prod_lines：0
- expected_test_lines：0
- expected_doc_lines：≤85

## 必须运行的测试命令
- YAML 解析与枚举精确断言
- `git diff --check`
- `git diff --cached --name-only` 范围核对

## 回滚方法
- `git revert <本任务提交>`；无运行时或数据回滚。

## 强制停止条件
- 需要新增字段/路径/SSE 事件、修改运行行为、测试阈值、DB、依赖或超过 4 文件。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：文档任务不适用
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：updated
- spec_sync：clean
- verified_commit：待回填
