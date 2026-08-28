# TASK-KB-JIANLI-FOUNDATION-005 Jianli 项目基础知识库

## 任务类型
- implementation
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`a08069c9b27e5353e937020f14b28a777c875422`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §9` Fact Source Routing / Review Mode
- `docs/requirements/SRS.md §3.1～§3.2`
- `docs/test/test-plan.md` TC-AI-010 / TC-OPS-010 / TC-AI-013
- `docs/adr/ADR-OBS-001.md`
- `docs/adr/ADR-RERANK-001.md`
- `apps/web/evals/latest.json`

## 需求来源
- 用户要求先为 Jianli 项目灌入基础知识库，覆盖 Agent Lab、评测中心与 CI、OpenTelemetry + Prometheus/Grafana、Reranker 对照实验；技术深入层后续另做。

## 目标
从当前已验证源码、测试和版本化报告中提炼七篇分层 Jianli 基础知识语料，启用 Jianli 项目域 KB 检索，并保留真实证据边界。

## 非目标（明确排除）
- 不做类/函数/SQL 级技术追问语料。
- 不修改页面布局、Agent 行为、Prompt、工具权限、评测阈值或运行基础设施。
- 不新增或修改公开 API、SSE、数据库、依赖、鉴权与加密策略。
- 不把本地组件对照、配置验证或尚未首跑的 GitHub/容器环境包装为生产结果。

## 允许修改路径
- `tasks/TASK-KB-JIANLI-FOUNDATION-005.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/scripts/seed_kb.py`
- `docs/fact-consistency/fact-bank.md`

## 禁止修改路径
- 上述清单之外全部文件。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅增加作品集知识内容和既有项目域检索映射，不改变外部契约、权限或业务行为。

## 功能验收
- 七篇 Jianli 文档分别覆盖项目定位、Agent/RAG、Agent Lab、评测/CI、可观测性、Reranker、可靠业务闭环及证据边界。
- `projects/jianli` 仅检索 Jianli 文档，不串入 Litchi 或 Sleep。
- 既有 Jianli 静态兜底与新 KB 事实一致。
- 正式灌库后 canonical corpus 全部 active + indexed。

## 安全与隐私验收
- 不记录问题/回答/Prompt/知识原文、预约 PII、密钥或高基数标识到可观测描述中。
- `answer.trace` 只描述脱敏阶段事实，不表述为模型思维链。

## 性能验收
- 每篇 Jianli 文档不超过既有 500 字符窗口；最终 20 篇 corpus 不超过 API 单批上传契约；不得修改分块算法或上传契约。
- 既有 RAG 冻结门禁不下降。

## 变更预算（change_budget）
- max_files：6
- expected_prod_lines：100
- expected_test_lines：240

## 必须运行的测试命令
- 真实 PG/Redis：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check app/aiqa/content.py app/aiqa/service.py scripts/seed_kb.py tests/aiqa/test_rag_eval.py`
- `mypy app/aiqa/content.py app/aiqa/service.py`
- `python -m compileall -q app/aiqa scripts/seed_kb.py`
- `python scripts/seed_kb.py` 并核对 canonical active/indexed 数量。
- 真实问答复验 Jianli 基础问题。

## 回滚方法
- Git revert 本任务提交，并使用上一版本 `seed_kb.py` 重新灌入 canonical corpus。

## 强制停止条件
- 冻结测试失败、需要任务外文件、需要改变 API/DB/依赖/权限或超过预算时停止报告。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
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
- Change Request：无
- 测试任务：TC-AI-010 / TC-OPS-010 / TC-AI-013 / TC-AIQA-RAG-EVAL
