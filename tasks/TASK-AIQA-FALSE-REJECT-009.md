# TASK-AIQA-FALSE-REJECT-009 误拒率评测集（混淆矩阵精确率侧）

> 承接外部评审（Kimi①"误拒率/false positive 模糊评测"、DeepSeek②）的真缺口：
> 现有 `test_rag_eval.py` 仅有 REJECT 10/10（越界题**召回侧**，验证"该拒的拒了"），
> **缺失精确率侧**——"该答的没被误拒"。阈值 0.47 偏激进时，范围内正常问法可能被误拒。
> 本任务补齐 FALSE_REJECT_CASES，使评测成为完整混淆矩阵（拦截率 + 误拒率成对）。

## 任务类型
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：5c0e4cc

## 精确规范引用
- SRS §（知识库问答）：范围内命中率≥90%、越界拒答率≥95%
- `apps/api/tests/aiqa/test_rag_eval.py` `REJECT_CASES` / `test_rag_reject_cases`

## 需求来源
- 外部评审 Kimi①（误拒率/false positive 评测）；页面"越界拦截 100%"需"误拒率 0/N"配对

## 目标
在 `test_rag_eval.py` 新增 `FALSE_REJECT_CASES`（范围内、应正常作答的问法）与
`test_rag_false_reject_cases`，断言每个用例 `offtopic=False` 且 `grounded=True`，
度量误拒率 = 0/N（精确率侧）。

## 非目标
- 不改阈值/路由/检索逻辑
- 不新增冻结 TC（属实现测试，可随实现补充）

## 允许修改路径
- `apps/api/tests/aiqa/test_rag_eval.py`（仅新增用例+测试函数，不改动既有用例）

## 禁止修改路径
- 生产代码、阈值、API 契约
- 既有 `LITERAL/SEMANTIC/EXTREME/REJECT` 用例

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：false（纯测试补充）
- affected_specs：全部 none
- reason：仅新增评测用例，不改变任何规范/实现。

## 功能验收
- `test_rag_false_reject_cases` 在真实 PG+Redis+真 embedding 环境下全部 PASS（误拒率 0/N）
- 与 `test_rag_reject_cases`（REJECT 10/10）共同构成完整混淆矩阵

## 安全与隐私验收
- 评测用例不含真实隐私数据（沿用 CORPUS 合成文档）

## 性能验收
- 不引入性能回归

## 变更预算
- max_files：1
- expected_prod_lines：0
- expected_test_lines：~30

## 必须运行的测试命令
- 需真实 PG+Redis+embedding（与 `test_rag_reject_cases` 同环境）：
  `JIANLI_AIQA_TEST_DATABASE_URL=... JIANLI_AIQA_TEST_REDIS_URL=... JIANLI_LLM_EMBEDDING_BASE_URL=... $PY -m pytest apps/api/tests/aiqa/test_rag_eval.py::test_rag_false_reject_cases -v`

## 回滚方法
- 删除新增用例与测试函数

## 强制停止条件
- 无（纯测试，无硬停触发）

## 交付证据
- commit / PR：5724d87
- 修改文件清单：apps/api/tests/aiqa/test_rag_eval.py
- 测试命令及结果：无 PG 时无法跑（6 用例 skipped）；须 WSL（PG+Redis+真 embedding）复跑 `test_rag_false_reject_cases`
- lint / typecheck：ruff ✅（改动文件）
- DB 迁移验证：无
- 验收证据：FALSE_REJECT_CASES 8 题 + test 函数已加，收集通过（无 PG 时跳过）
- 变更预算实际值：max_files 实际 1 / 生产 0 行 / 测试 ~30 行
- 未解决风险：须 WSL 跑通；若真阈值下某用例被误拒，先定位是阈值问题而非用例错误
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：5724d87
- 关闭门禁：①④ 已满足；②（WSL 复跑）③（spec_sync clean）待用户验证后满足
