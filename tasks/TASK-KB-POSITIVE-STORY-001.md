# TASK-KB-POSITIVE-STORY-001 成就故事正向语料收口

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：04c85fcf5c1fb4c74bb91690fcb1705c1ac0fc82

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/SRS.md` §3.2
- `docs/requirements/use-cases.md` UC-03 / UC-04 / UC-05
- `docs/test/test-plan.md` TC-AI-001 / TC-AI-002 / TC-AI-004
- `apps/api/tests/aiqa/test_rag_eval.py` `CORPUS` / `FALSE_REJECT_CASES`

## 需求来源
- `TASK-AIQA-POSITIVE-FRAMING-001` 页面真模型验收发现：`behavior-stories.md` 的成就段落直接包含“限制、失败、67/84”，导致正向问题即使有 Prompt 约束仍复述不利信息。

## 目标
将成就故事的主检索证据收口为成果、个人贡献和工程价值，使“最有成就感”问题只引用 84/84、18,720 零丢失、5.6 万行精确去重与可复跑可交接价值。

## 非目标（明确排除）
- 不删除 `sleep-evidence-retrospective.md` 等专门技术复盘文档中的真实失败与边界。
- 不增加或删除 canonical corpus 文档，不改变 20 篇上限。
- 不修改 API、数据库、依赖、检索算法、阈值、权限、Prompt 或 Agent 工具。

## 允许修改路径
- `tasks/TASK-KB-POSITIVE-STORY-001.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`

## 禁止修改路径
- `apps/api/app/aiqa/persona.py`
- `apps/api/app/aiqa/service.py`
- API / migration / dependency / auth / agent-tool 相关文件
- 既有 RAG 评测阈值与断言

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
- reason：同一已公开事实的面试叙事聚焦修复；事实、证据边界、拒答和外部契约均不变。

## 功能验收
- `behavior-stories.md` 成就段不含“没有稳定真机”“67/84”“限制、失败”等主动不利表述。
- `FALSE_REJECT_CASES` 成就题继续 `grounded=true / offtopic=false`。
- 页面真实回答保留 84/84、18,720、5.6 万行与可复跑可交接价值，不主动输出失败率、未验证或安全不足。
- 真正越界题和隐私题门禁不降低。

## 安全与隐私验收
- 不新增私人信息或 NDA 内容。
- 不把未验证事实包装成已验证；技术边界仍保留在专项复盘语料中。

## 性能验收
- 文档数保持 20，不新增检索阶段或模型调用。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：8
- expected_test_lines：8

## 必须运行的测试命令
- `PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `mypy app/aiqa/content.py`
- `scripts/seed_kb.py` 后验证 20/20 active + indexed。
- 页面真实复问成就题并检查回答。

## 回滚方法
- 回退两处成就故事文本并重新执行 `scripts/seed_kb.py`。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要删除专门边界文档、降低测试断言、修改检索/API/数据库/依赖/权限时立即停止。
- 冻结 RAG 门禁失败或超过 3 个文件时停止。

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
- 前置任务：`TASK-AIQA-POSITIVE-FRAMING-001`
- 测试任务：TC-AI-001 / TC-AI-002 / TC-AI-004
