# TASK-KB-SEED-VERIFY-003：知识库重灌结果强校验

## 任务类型
- implementation
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`76c0602`

## 精确规范引用
- `docs/requirements/PRD.md` R22、R24
- `docs/requirements/use-cases.md` UC-16、UC-17
- `TASK-KB-LITCHI-INTERVIEW-002`

## 需求来源
- 2026-08-27 实际重灌中，14 篇新文档因 embedding provider 402 全部 failed；脚本却把 26 条已软删除历史记录计为 indexed 并返回成功。
- 用户已于 2026-08-28 完成充值，要求继续重灌。

## 目标
让 `seed_kb.py` 只按当前 active 文档验收本次 canonical corpus，任何缺失、额外或 failed 文档都返回非零并打印失败原因；随后完成真实重灌。

## 非目标
- 不改知识内容、Embedding provider、检索算法、公开 API、数据库结构、权限或依赖。

## 允许修改路径
- `apps/api/scripts/seed_kb.py`
- `apps/api/tests/scripts/test_seed_kb.py`
- `tasks/TASK-KB-SEED-VERIFY-003.md`

## 禁止修改路径
- 其他应用代码、迁移、OpenAPI、前端与知识语料。

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false
- affected_specs：SRS none / domain_model none / openapi none / security none / test_plan none
- reason：仅修复运维脚本的结果判定，不改变产品契约。

## 功能验收
- 仅 `retrieval_disabled_at IS NULL` 的 active 文档参与统计。
- active 名称集合必须精确等于 CORPUS，且每篇 status 均为 indexed，才返回 0。
- 缺失、额外、indexing、failed 均返回 1；failed 输出文档名和脱敏 failure_reason。
- 充值后真实重灌为 active 14/14 indexed，四篇 Litchi 均 active。

## 安全与隐私验收
- 不输出 API Key、数据库口令或文档正文。

## 性能验收
- 单次只增加一条 active 状态查询；无在线请求路径影响。

## 变更预算
- max_files：3
- expected_prod_lines：40
- expected_test_lines：90

## 必须运行的测试命令
- `pytest tests/scripts/test_seed_kb.py -q`
- `ruff check scripts/seed_kb.py tests/scripts/test_seed_kb.py`
- `mypy app`
- 真实 `python scripts/seed_kb.py` + DB active 状态核验

## 回滚方法
- 回滚实现提交；知识文档可再次由 canonical corpus 重灌。

## 强制停止条件
- 遵循 `AGENTS.md §2`；如需 DB/API/依赖/权限/知识内容变化则停止。

## 交付证据
- commit / PR：`50ae9c6`（实现提交）
- 修改文件清单：`apps/api/scripts/seed_kb.py`、`apps/api/tests/scripts/test_seed_kb.py`、本任务单；均在允许路径内。
- 测试命令及结果：`pytest tests/scripts/test_seed_kb.py -q` → `3 passed`；覆盖精确成功、provider 402/failed、缺失/额外/重复 active 文档。
- lint / typecheck：scoped Ruff → `All checks passed!`；`mypy app` → `Success: no issues found in 52 source files`；`git diff --check` → pass。
- DB 迁移验证：无
- 验收证据：用户充值后真实运行 `seed_kb.py` → `HTTP 202`、`KB active 14 / indexed 14 / non-indexed 0 / historical 40`、`verified canonical corpus 14/14`、`exit=0`。随后数据库直查确认 active=14、indexed=14、Litchi=4；`litchi-overview.md`、`litchi-agent-rag.md`、`litchi-evidence-retrospective.md`、`litchi-evolution.md` 均 indexed 且各 1 chunk，旧 `litchi.md` 无 active 记录。
- 变更预算实际值：3/3 文件；生产脚本 39+/11-，测试 44 行，任务文档 87 行；未超预算。
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`50ae9c6`

## 关联
- Change Request：无
- 上游任务：`TASK-KB-LITCHI-INTERVIEW-002`
