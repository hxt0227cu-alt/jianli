# TASK-AIQA-UNKNOWN-TOOL-RAG-FALLBACK-001 白名单外工具拒绝后的 RAG 回退

## 任务类型
- bugfix
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`6ef5492`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §3` 白名单外工具禁止与无依据拒答
- `AGENTS.md §7` 冻结验收测试
- `docs/baseline.yml` `agent_tools` / `mvp_hard_rules`
- `TC-AI-007` Agent 工具白名单与无依据回答

## 需求来源
- 真实模型复合问题验收中，模型返回白名单外工具后虽被拒绝，却误入预约工具结果生成分支，产生 `grounded=false` 且混入异项目事实的回答；用户要求解决。

## 目标
- 白名单外工具继续被拒绝、记录安全轨迹且绝不执行。
- 拒绝后以用户原始问题进入现有 RAG 路径：有证据则 grounded 回答，无证据则现有 off-topic 拒答。
- 合法预约工具的鉴权、失败结果及多步行为保持不变。

## 非目标
- 不新增或删除 Agent 工具。
- 不修改 Prompt、公开 API/SSE 契约、数据库、迁移、依赖、RBAC、检索算法、阈值或知识库内容。

## 允许修改路径
- `tasks/TASK-AIQA-UNKNOWN-TOOL-RAG-FALLBACK-001.md`
- `apps/api/app/aiqa/service.py`
- `apps/api/tests/aiqa/test_agent_tools.py`

## 禁止修改路径
- 上述清单之外全部文件。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估（spec impact）
- behavior_change：false（缺陷修复，恢复既有白名单拒绝 + grounded/no-evidence 不变量）
- affected_specs：none
- reason：修复白名单外工具被拒绝后错误进入工具生成分支的问题，不改变合法工具或接口行为。

## 功能、安全与性能验收
- 缺陷复现测试必须证明白名单外工具未执行、轨迹为 blocked、随后使用原问题检索并 `grounded=true`。
- 无证据问题仍 `grounded=false`、`offtopic=true`，不得生成无引用事实。
- 合法工具和 `MAX_STEPS` 现有测试不回归。
- 不增加额外模型调用；白名单外工具路径由继续循环改为立即进入检索。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：20
- expected_test_lines：60

## 必须运行的测试命令
- `PYTHONPATH=. pytest tests/aiqa/test_agent_tools.py tests/aiqa/test_agent_crud.py tests/aiqa/test_agent_lab.py -q`
- `PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check app/aiqa/service.py tests/aiqa/test_agent_tools.py`
- `mypy app/aiqa/service.py`
- `python -m compileall -q app/aiqa/service.py tests/aiqa/test_agent_tools.py`
- 真实模型复测原复合问题，必须 `grounded=true` 且引用 Litchi 文档。

## 回滚方法
- Git revert 本任务提交。

## 强制停止条件
- 冻结断言失败、需要任务外文件或 API/DB/依赖/权限/Prompt/阈值变化、超过预算时立即停止报告。

## 交付证据（任务关闭前必须填写）
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- spec_sync：待回填
- verified_commit：待回填

