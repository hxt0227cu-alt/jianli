# TASK-TEST-AGENT-LAB-NO-EVIDENCE-001 更新 Agent Lab 零依据冻结输入

## 任务类型
- test-maintenance

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`6ef5492`

## 精确规范引用
- `AGENTS.md §7` 冻结验收测试
- `TC-AI-010` Agent Lab 隐私安全轨迹与无依据拒答
- `apps/api/tests/aiqa/test_rag_eval.py` 已冻结越界问题集

## 需求来源
- 用户明确授权。原“N​ASA 火星项目”问题因项目语料扩充后含大量“项目/参与/成果”通用词，不再是稳定的静态零命中输入；断言本身仍有效。

## 目标
- 将零依据输入替换为现有拒答评测已验证的稳定越界问题。
- 保持 retrieval blocked、无原问题泄漏和轨迹单调性断言不变。

## 非目标
- 不修改业务代码、断言强度、检索算法、阈值、API、DB、依赖或权限。

## 允许修改路径
- `tasks/TASK-TEST-AGENT-LAB-NO-EVIDENCE-001.md`
- `apps/api/tests/aiqa/test_agent_lab.py`

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：仅替换失去零命中特性的测试输入，不改变验收语义。

## 变更预算
- max_files：2
- expected_test_lines：4

## 验收与命令
- `PYTHONPATH=. pytest tests/aiqa/test_agent_lab.py -q`
- `ruff check tests/aiqa/test_agent_lab.py`
- `python -m compileall -q tests/aiqa/test_agent_lab.py`
- 不得修改业务代码或降低任何断言。

## 回滚
- Git revert 本任务提交。

## 交付证据
- commit / PR：本任务闭环提交
- 修改文件：本任务单、`apps/api/tests/aiqa/test_agent_lab.py`
- 测试结果：`PYTHONPATH=. pytest tests/aiqa/test_agent_lab.py -q` → 3 passed
- lint / compile：Ruff pass；compileall pass
- DB 迁移：无
- 变更预算实际值：2 文件；冻结测试净替换 2 行，未降低断言
- 未解决风险：无
- 是否偏离 TASK：否
- spec_sync：not_required
- verified_commit：本任务闭环提交
