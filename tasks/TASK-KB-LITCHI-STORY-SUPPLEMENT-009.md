# TASK-KB-LITCHI-STORY-SUPPLEMENT-009 Litchi 开发故事高价值语料补强

## 任务类型
- implementation
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`9308ac770509b1b2ca2a1ade64d6f868564f2d6f`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §7` 冻结验收测试
- `AGENTS.md §9` Fact Source Routing / Review Mode
- `docs/fact-consistency/fact-bank.md` Litchi 事实组
- `TC-AIQA-RAG-EVAL`（`apps/api/tests/aiqa/test_rag_eval.py`）

## 需求来源
- 用户提供 Litchi 开发故事并授权由 AI 选择适合 HR/技术追问的内容补入现有 RAG 语料。

## 目标
核验并补充三条高价值故事：文档解析入口故障定位、评测 evidenceIds 标注修正的口径、图像模型与透明降级的实验边界；保持现有 4 篇 Litchi canonical 文档及全库 20 篇总数不变。

## 非目标（明确排除）
- 不逐月照搬开发时间线，不写人物姓名或无助于面试判断的过程细节。
- 不把未提交工作区结果冒充干净提交证据，不把小验证集结果外推到真实果园。
- 不修改 Litchi 源码、Jianli 业务代码、API、数据库、迁移、依赖、权限、Prompt、检索算法或阈值。

## 允许修改路径
- `tasks/TASK-KB-LITCHI-STORY-SUPPLEMENT-009.md`
- `apps/api/tests/aiqa/test_rag_eval.py`
- `apps/api/app/aiqa/content.py`
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
- reason：仅补强作品集事实语料和等价检索验收，不改变运行逻辑或外部契约。

## 功能验收
- canonical corpus 仍为 20 篇，Litchi 仍为原 4 个文件名。
- 语料可回答：为什么解析坏文本不能靠调阈值解决、为什么 3/30→24/30 不是模型八倍提升、图像 93.75% 的真实实验边界与透明降级。
- 保留现有 Agent、RAG、并发、安全和证据等级口径，不删除或放宽冻结断言。
- 新事实必须能区分提交代码、未提交工作区报告和用户确认的开发经历。

## 安全与隐私验收
- 不写入绝对路径、个人姓名、密钥、账号、日志原文或内部标识。

## 性能验收
- 不改变检索阈值、top-k、分块参数或任何既有测试门槛。
- 真实 BGE-M3 门禁通过，新增追问引用目标 Litchi 文档。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：60
- expected_test_lines：120

## 必须运行的测试命令
- `PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- 新增 Litchi 追问打印命中排名并达到 3/3 引用目标文档。
- `ruff check app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `mypy app/aiqa/content.py`
- `python -m compileall -q app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `python scripts/seed_kb.py`，核对 canonical 20/20 active + indexed。
- 真实模型抽检至少两条新增追问及证据边界。

## 回滚方法
- Git revert 本任务提交，并用上一版本 `scripts/seed_kb.py` 重灌 canonical corpus。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 任一冻结断言下降、需要修改任务外文件、需要 API/DB/依赖/权限/阈值变化或超过预算时停止报告。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`e106fa1`（实现提交；任务证据由后续闭环提交补齐）
- 修改文件清单：`apps/api/tests/aiqa/test_rag_eval.py`、`apps/api/app/aiqa/content.py`、`docs/fact-consistency/fact-bank.md`、本任务单
- 测试命令及结果：
  - `PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py::test_rag_extreme_semantic_hit_cases -q -s` → 1 passed；新增 Litchi 3/3 均为目标文档 rank=1，整组 8/9，未命中项为任务前既有 Jianli 用例
  - `PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q` → 7 passed（真实 PG/Redis/BGE-M3，142.31s）
  - `python scripts/seed_kb.py` → canonical 20/20 active + indexed，Litchi 仍为 4 篇
- lint / typecheck：`ruff` pass；`mypy app/aiqa/content.py` 0 errors；`compileall` pass；`git diff --check` pass
- DB 迁移验证：无
- 验收证据：真实模型 `deepseek-v4-flash` 两条单一追问均 `grounded=true`，首引均为 `litchi-evidence-retrospective.md`；正确区分标签修复与模型提升，并正确说明 300/80 小样本、93.75%/91.25%、`best.pt`、`engine/demoMode` 边界
- 变更预算实际值：4 文件；实现语料 17 行变更、评测 25 行变更，其余为事实题库与任务治理；未超过 `max_files=4`
- 未解决风险：复合提问“准确率边界 + 降级防冒充”曾出现一次未走检索、`grounded=false` 且混入异项目事实；拆成单一问题后正确。该问题属于既有 Agent 路由/无依据生成策略，不在本任务获批范围。数据库另保留 232 条软删除历史文档，不参与活跃检索。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：not_required（仅 canonical 内容与等价评测补强）
- verified_commit：`e106fa1`

## 关联
- Change Request：无
- 上游任务：`TASK-KB-TECHNICAL-DEPTH-007`
- 测试任务：TC-AIQA-RAG-EVAL
