# TASK-AIQA-RECOMMENDATION-RECALL-001 推荐面试问题误拒修复

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：9b333b0da18402734d1fa9f3c9cbf3df82003a54

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.2
- `docs/requirements/use-cases.md` UC-03 / UC-04 / UC-05
- `docs/test/test-plan.md` TC-AI-001 / TC-AI-002 / TC-AI-004 / TC-AI-006

## 需求来源
- 用户本地验收发现页面推荐问题“你适合什么样的团队和岗位？”和“你最有成就感的一段工程经历是哪一段？”被错误判为越界。

## 目标
让页面自身推荐的两道范围内面试问题稳定检索到公开证据并正常回答，同时以真实 RAG 门禁防止回归。

## 非目标（明确排除）
- 不修改 API、SSE 契约、数据库、依赖、权限、Prompt 或 Agent 工具。
- 不降低 `JIANLI_KB_MIN_SCORE=0.47`，不修改混合检索、RRF 或 Reranker 算法。
- 不增加 canonical corpus 文档数量，不放宽真正越界问题的拒答规则。

## 允许修改路径
- `tasks/TASK-AIQA-RECOMMENDATION-RECALL-001.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`

## 禁止修改路径
- `apps/api/app/aiqa/service.py`
- API / migration / dependency / auth / agent-tool 相关文件
- 既有 `REJECT_CASES` 及其断言和阈值

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：Bug 修复使页面推荐问题重新符合已批准的范围内问答与推荐问题用例；不改变既有规范。

## 功能验收
- 两道推荐问题均返回 `grounded=true`、`offtopic=false`，并产生引用。
- `FALSE_REJECT_CASES` 从 8 题扩为 10 题且 10/10 通过。
- 既有 `REJECT_CASES` 仍 10/10 拒答，隐私断言不降低。
- canonical corpus 仍保持 20 篇。

## 安全与隐私验收
- 新增内容仅来自已批准公开面试材料，不含 NDA 内容、联系方式、绝对路径、日志或内部标识。
- 无依据与越界拒答门槛保持不变。

## 性能验收
- 不新增模型调用、检索阶段或外部依赖；检索性能路径不变。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：8
- expected_test_lines：8

## 必须运行的测试命令
- `ruff check app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `pytest tests/aiqa/test_rag_eval.py -v`（真实 PostgreSQL / Redis / BGE-M3）
- 正式重灌 20 篇 canonical corpus 后，在页面实问两题并核对 grounded / citations / offtopic。

## 回滚方法
- 回退本任务对 `content.py` 与 `test_rag_eval.py` 的增量；重新执行 `scripts/seed_kb.py` 恢复旧语料快照。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要降低检索阈值、修改检索算法、API、数据库、依赖、鉴权或 Prompt 时立即停止。
- 冻结的越界拒答、隐私或命中率门禁失败时立即停止，不修改断言绕过。
- 超过 3 个修改文件时拆分任务。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待完成
- 修改文件清单：待完成
- 测试命令及结果：待完成
- lint / typecheck：待完成
- DB 迁移验证：无
- 验收证据：待完成
- 变更预算实际值：待完成
- 未解决风险：待完成
- 是否偏离 TASK：待完成
- 规范影响结论：none
- spec_sync：待完成
- verified_commit：待完成

## 关联
- Change Request：无（符合既有规范的 Bug 修复）
- 测试任务：TC-AI-001 / TC-AI-002 / TC-AI-004 / TC-AI-006
