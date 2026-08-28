# TASK-KB-TECHNICAL-DEPTH-007 Litchi / Sleep 技术追问语料升级

## 任务类型
- implementation
- test
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`5164fa8fd35b0d7f75b6d2b4a10b332c767bbb8e`

## 精确规范引用（AI 只读取这些章节）
- `AGENTS.md §7` 冻结验收测试
- `AGENTS.md §9` Fact Source Routing / Review Mode
- `docs/fact-consistency/fact-bank.md` Litchi / Sleep 事实组
- `TC-AIQA-RAG-EVAL`（`apps/api/tests/aiqa/test_rag_eval.py`）

## 需求来源
- 用户显式批准依据 2026-08-28 两份只读技术取证材料升级 Litchi 与 Sleep 技术追问层，并保持 20 篇 canonical corpus 上限。

## 目标
在不新增 canonical 文档的前提下，升级现有 4 篇 Litchi 与 6 篇 Sleep 语料，修正基础口径冲突，覆盖关键实现链路、异常路径、证据等级和下一版演进，并通过真实 BGE-M3 冻结检索与正式重灌库。

## 非目标（明确排除）
- 不修改 Jianli 七篇、个人三篇语料及页面展示。
- 不修改 API、SSE、数据库、依赖、权限、Prompt、检索算法、分块算法或评测阈值。
- 不公开 NDA 源码、日志、截图、内部标识、绝对路径或可反推公司资产的信息。
- 不将未来方案、实验模板、本地模拟、本人确认或未提交 RC 包装为已提交生产实现。

## 允许修改路径
- `tasks/TASK-KB-TECHNICAL-DEPTH-007.md`
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
- reason：仅校正与深化作品集语料及其等价检索验收，不改变产品契约、权限或业务行为。

## 功能验收
- canonical corpus 仍恰为 20 篇，Litchi 4 篇、Sleep 6 篇文件名保持不变。
- Litchi 覆盖受控 Agent、RAG 摄入/检索、HITL/业务边界、并发与评测、部署与演进。
- Sleep 覆盖异步接纳、固定 DAG/协调器、工具/HITL/安全、租户 RAG、遥测重放、评测红队、设备和 staging 边界。
- 修正 Sleep 84 条用例的 11 个源码 case group 口径、Litchi 部分协作闭环/非事务 Outbox/SSE 轮询等冲突。
- 新增技术追问检索用例，但不删除或放宽既有命中、拒答、误拒和隐私断言。
- 正式灌库后 20 篇 canonical 文档全部 active + indexed。

## 安全与隐私验收
- 公开语料不得包含绝对路径、内部仓库标识、真实设备标识、公司客户数据、密钥、日志原文或 NDA 源码细节。
- 本人确认、未提交 RC、实验模板和未来方案必须显式标注证据边界。

## 性能验收
- 不改变现有检索阈值、top-k、分块参数或测试门槛。
- 真实 BGE-M3 下冻结 RAG 门禁全部通过；新增技术追问必须稳定命中目标项目文档。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：120
- expected_test_lines：320

## 必须运行的测试命令
- 真实 PG/Redis/BGE-M3：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -q`
- `ruff check app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `mypy app/aiqa/content.py`
- `python -m compileall -q app/aiqa/content.py tests/aiqa/test_rag_eval.py`
- `python scripts/seed_kb.py` 并核对 canonical active/indexed 数量。
- 真实模型复验 Litchi / Sleep 技术追问与证据边界问法。

## 回滚方法
- Git revert 本任务提交，并使用上一版本 `scripts/seed_kb.py` 重新灌入 canonical corpus。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 任一冻结断言下降、需要修改任务外文件、需要 API/DB/依赖/权限/阈值变化或超过预算时立即停止报告。

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
- 上游任务：`TASK-KB-CORPUS-CLEANUP-006` / `TASK-KB-JIANLI-FOUNDATION-005`
- 测试任务：TC-AIQA-RAG-EVAL
