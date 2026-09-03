# TASK-EXTERNAL-RAG-GATE-005 真实语义 Provider 显式发布门禁

> 状态：In Progress（2026-08-31）。复核纠正：冻结 TC 不得从发布门禁 deselect；仅允许将 pre-commit `--quick` 明确降级为非发布开发预检。

## 任务类型
- test / CI infrastructure（测试分层修复，不改断言）

## 基线与引用
- baseline：PRD 2.3.6 / SRS 1.9 / test-plan 1.2
- 基线 commit：`465b6ccdbf8b1be6f237f962d40279fab54f991a`
- `docs/test/test-plan.md` §1、§2.2、§4；TC-AI-001、TC-AI-002
- 冻结用例：`test_rag_semantic_hit_cases`、`test_rag_extreme_semantic_hit_cases`、`test_pure_vector_ranking`、`test_rag_reject_cases`

## 目标
- 完整门禁和任何 `--tc` 发布门禁强制保留真实 Embedding 配置并执行四项冻结评测；缺凭据、网络或额度失败均 fail closed。
- 只有单独 `--quick` 的 pre-commit 开发预检允许显式报告四项未执行，且成功结果不得称为发布通过；`--external-rag` 可强制加入原断言。
- CI `rag-integration` 强制检查 GitHub Secrets 并运行四项冻结节点，不得用本地哈希或 deselect 误绿。

## 非目标
- 不修改冻结问题、阈值、断言、语料、检索算法或 Provider 配置。
- 不自动联网、不把 real-provider 测试改成 mock、不新增依赖。

## 允许修改路径
- `scripts/verify.sh`
- `.github/workflows/agent-quality-gate.yml`
- `docs/HARNESS.md`
- `docs/devlog/pitfalls/pitfalls.jsonl`
- `docs/devlog/pitfalls/pitfalls.md`
- `tasks/TASK-EXTERNAL-RAG-GATE-005.md`

## 已批准的 DB / API / 依赖变更
- DB：无 schema 变化，仅复用 AIQA 测试库。API：无。依赖：无。

## 规范影响评估
- behavior_change：false
- affected_specs：none
- reason：只把外部 Provider 验收从默认离线门禁中显式分层，冻结标准不变。

## 变更预算
- max_files：6
- expected_prod_lines：0
- expected_test_lines：≤65
- expected_doc_lines：≤12

## 验收
- 单独 `verify --quick` 明确为非发布离线预检并列出四项未执行。
- `verify --tc --quick`、`verify --tc` 及完整 `verify` 均在真实凭据可用时执行四项冻结测试；网络/额度异常原样失败，不重试轰炸。
- CI 缺少 secret 时明确失败；配置后运行原冻结节点且零 skip。

## 回滚
- 回退显式参数与文档；冻结测试不变。

## 交付证据
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：复用 TASK-RELEASE-GATES-002 证据
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：真实 Provider 运行需要网络与有效余额
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：clean
- verified_commit：待回填
