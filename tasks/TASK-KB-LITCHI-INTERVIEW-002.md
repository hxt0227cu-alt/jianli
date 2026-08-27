# TASK-KB-LITCHI-INTERVIEW-002：Litchi 面试知识语料分层重写

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`d75c443cbaf01efb864c5197dc2a64507e2964ef`

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/PRD.md` R2、R7、R22、R24、场景 3、场景 16
- `docs/requirements/use-cases.md` UC-03、UC-16、UC-17
- `TC-AI-001` / 既有 `tests/aiqa/test_rag_eval.py` 检索验收

## 需求来源
- 用户确认 Litchi 为本人独立开发、正式毕设成绩 90.4；Milvus、Neo4j、Ollama 完整环境真实跑通并现场演示；数据平台、可观测性与 Helm 是实验模板。
- 用户要求将审计底稿改写为面试官可查询的知识库语料，并明确区分当前实现、实验证据、失败复盘和下一版演进。

## 目标
将单篇、混杂且含无支撑宣传数字的 Litchi 语料拆为概览、Agent/RAG 实现、证据复盘、演进计划四篇，默认突出工程价值，深挖时能给出可核验边界。

## 非目标（明确排除）
- 不修改 Litchi 项目源码或补做其未实现能力。
- 不改模型、Reranker、检索算法、Prompt、公开 API、数据库、权限、页面二卡片或预约功能。
- 不把规划中的 Redis Stream、RLS、事务 Outbox、专用执行器或成本预算包装成已实现。

## 允许修改路径
- `apps/api/tests/aiqa/test_rag_eval.py`（仅 Litchi 语料与对应文档命中映射，不降低阈值）
- `apps/api/app/aiqa/content.py`（Litchi 静态兜底事实同步）
- `apps/api/app/aiqa/service.py`（仅 Litchi 项目域文档名映射）
- `apps/api/scripts/seed_kb.py`（文档数量说明同步）
- `docs/fact-consistency/fact-bank.md`（FQ-27～30 事实与溯源同步）
- `tasks/TASK-KB-LITCHI-INTERVIEW-002.md`

## 禁止修改路径
- Litchi 仓库 `C:\Users\hxt02\Desktop\hxt-bishe`
- `apps/api/app/aiqa/reranker.py`、运行配置、数据库迁移、OpenAPI、SSE、前端页面与其他项目语料

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：这是 R22/R24 已批准知识内容的事实纠偏与拆分，不改变接口、权限、检索契约或验收阈值。

## 功能验收
- Litchi 项目域只允许召回四篇 Litchi 文档，不串入其他项目。
- 概览回答先呈现项目价值和个人职责，不默认倾倒失败日志。
- 实现追问可回答 Planner/Guard/Executor/Synthesizer、工具白名单、HITL、Milvus/Neo4j/Ollama 与 480/120 分块。
- 复盘追问如实回答历史稳定性、并发失败与评测器缺陷，不把不同环境数据强行归因为扩展性回退。
- 演进追问始终使用“计划/下一版/尚未落地”口径，不冒充当前实现。
- 删除当前证据不足的 YOLO 20%→93.75% 与 Chat P95 5s→124ms 宣传口径。

## 安全与隐私验收
- 不写入本地绝对路径、账号、密钥或可复用攻击步骤。
- 不改变知识库 owner_admin 权限与越界拒答策略。

## 性能验收
- 不降低既有 RAG 命中率阈值；Litchi 文档拆分后原有 literal/semantic/extreme/reject 验收保持通过。

## 变更预算
- max_files：6
- expected_prod_lines：120
- expected_test_lines：220（语料属于测试内 canonical corpus）

## 必须运行的测试命令
- `python -m pytest tests/aiqa/test_rag_eval.py -q`（有真实 PG/Redis 时完整执行；否则记录 skip）
- `python -m pytest tests/aiqa/test_content.py -q`（若文件存在）
- `ruff check app/aiqa/content.py app/aiqa/service.py scripts/seed_kb.py tests/aiqa/test_rag_eval.py`
- `mypy app`
- `git diff --check`

## 回滚方法
- 回滚本任务提交；重新运行 `scripts/seed_kb.py` 恢复上一版知识库。

## 强制停止条件
- 遵循 `AGENTS.md §2`；出现 DB/API/依赖/权限/Prompt/检索算法变化、冻结阈值变化或超过 6 文件即停止。

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
- 规范影响结论：none
- spec_sync：待回填
- verified_commit：待回填

## 关联
- Change Request：无（R22/R24 既有内容维护能力）
- 测试任务：TC-AI-001 / RAG 既有冻结评测
