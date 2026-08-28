# TASK-KB-CORPUS-CLEANUP-006 旧个人语料收敛

## 任务类型
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`a08069c9b27e5353e937020f14b28a777c875422`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §7` 冻结验收测试
- `AGENTS.md §9` Fact Source Routing
- `docs/fact-consistency/fact-bank.md` A/B/E 组
- `TC-AIQA-RAG-EVAL`（`apps/api/tests/aiqa/test_rag_eval.py`）

## 需求来源
- 用户显式批准将九篇旧个人语料合并清理为三篇，并同步冻结评测的等价文档映射，不降低命中率、拒答率或隐私断言。

## 目标
将 `resume/honors/education/skills/internship/certificates/rag-notes/agent-notes/interview-story` 九篇重复或占位语料，收敛为 `profile.md`、`credentials.md`、`behavior-stories.md`，为七篇 Jianli 项目语料释放批量上传空间。

## 非目标（明确排除）
- 不修改任何评测阈值、命中率门槛、拒答断言、隐私断言或测试依赖级别。
- 不修改 API、SSE、数据库、依赖、权限、检索算法或页面。
- 不新增未经用户确认的个人经历和量化数据。

## 允许修改路径
- `tasks/TASK-KB-CORPUS-CLEANUP-006.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `docs/fact-consistency/fact-bank.md`
- `apps/api/scripts/seed_kb.py`

## 禁止修改路径
- 上述清单之外全部文件；Jianli 七篇语料与项目域映射由 `TASK-KB-JIANLI-FOUNDATION-005` 负责。

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
- reason：语料去重和等价测试文档映射，不改变产品行为或验收强度。

## 功能验收
- 九篇旧文档不再属于 canonical corpus，三篇新文档覆盖其经确认事实。
- 所有原命中、语义、极端改写、误拒和隐私题保持原断言强度。
- 最终 canonical corpus 恰为 20 篇，符合单次上传 `maxItems=20`。

## 安全与隐私验收
- 不新增住址、生日、薪资等隐私；原隐私拒答用例保持不变。

## 性能验收
- 真实 PG/Redis 全量 RAG 冻结测试不得低于变更前门禁。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：2
- expected_test_lines：180

## 必须运行的测试命令
- 真实 PG/Redis：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check tests/aiqa/test_rag_eval.py scripts/seed_kb.py`
- `python -m compileall -q scripts/seed_kb.py tests/aiqa/test_rag_eval.py`

## 回滚方法
- Git revert 本任务提交，并重新运行上一版本 `seed_kb.py`。

## 强制停止条件
- 任一冻结断言下降、需要修改任务外文件或超过预算时停止报告。

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
- 下游任务：`TASK-KB-JIANLI-FOUNDATION-005`
- 测试任务：TC-AIQA-RAG-EVAL
