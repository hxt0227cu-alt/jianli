# TASK-KB-SLEEP-INTERVIEW-004 Sleep 项目面试知识库重构

## 任务类型
- implementation
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`cad03c7f0b89d60a60405b342187c03272fae797`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §9` Fact Source Routing / Review Mode
- `docs/fact-consistency/fact-bank.md` D 组（FQ-31～FQ-33）
- `TC-AIQA-RAG-EVAL`（`apps/api/tests/aiqa/test_rag_eval.py`）

## 需求来源
- 用户确认 Sleep 项目七项脱敏指标可以公开，并要求按 Litchi 复盘方法完成下一项目知识库灌入。

## 目标
以六篇短而可检索的脱敏语料替换旧 `taiyizhi.md`，同步项目域隔离、静态兜底与事实题库，使问答能准确表达本人贡献、硬证据、失败边界与演进判断。

## 非目标（明确排除）
- 不修改 `C:\Users\hxt02\Desktop\sleep202603-an` 原公司项目。
- 不复制或公开原公司源码、截图、原始日志、内部路径、环境信息、客户或同事身份。
- 不改检索算法、Prompt、Agent 工具、公开 API、数据库、权限、依赖或页面布局。
- 不把本地/RC/历史 staging 结果包装成生产结果。

## 允许修改路径
- `tasks/TASK-KB-SLEEP-INTERVIEW-004.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`
- `apps/api/app/aiqa/service.py`
- `apps/api/scripts/seed_kb.py`
- `docs/fact-consistency/fact-bank.md`

## 禁止修改路径
- 上述清单之外全部文件，尤其是 DB migrations、API 契约、认证/加密模块与 Sleep 原仓库。

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
- reason：只校正作品集知识内容与检索域映射，不改变产品接口、权限或运行规则。

## 功能验收
- 六篇 Sleep 语料均独立分块且可由 `sleep202603_an` 项目域检索。
- 旧 `taiyizhi.md` 不再属于 canonical corpus，正式灌库后不再 active。
- FQ-31～FQ-33 与新的事实边界一致。
- 七项公开数字与其口径、限制同时出现在语料中。

## 安全与隐私验收
- 无原公司源码、截图、原始日志、内部路径、客户/同事身份与密钥。
- 团队成果与本人职责明确区分；NDA 证据只说明边界，不暗示可公开复核。

## 性能验收
- 每篇语料正文不超过单 chunk 阈值 480 字符，避免关键事实被跨块切散。
- 既有 RAG 冻结门禁不下降。

## 变更预算（change_budget）
- max_files：6
- expected_prod_lines：90
- expected_test_lines：220

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `cd apps/api && ruff check app/aiqa/content.py app/aiqa/service.py scripts/seed_kb.py tests/aiqa/test_rag_eval.py`
- `cd apps/api && mypy app/aiqa/content.py app/aiqa/service.py`
- `python -m compileall apps/api/app/aiqa apps/api/scripts/seed_kb.py`
- 正式灌库：WSL 中运行 `cd apps/api && .venv/bin/python scripts/seed_kb.py`，并核对 canonical active/indexed 数量。

## 回滚方法
- Git revert 本任务提交；重新运行上一版本 `seed_kb.py` 恢复 canonical corpus。

## 强制停止条件
- 冻结验收测试失败、需要修改任务外文件或超过 6 个文件时停止并报告。

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
- 测试任务：TC-AIQA-RAG-EVAL / FQ-31～FQ-33
