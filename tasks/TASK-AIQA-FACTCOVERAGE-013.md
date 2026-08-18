# TASK-AIQA-FACTCOVERAGE-013 简历域事实覆盖补齐（路径 A）

> 承接事实一致率首测（2026-08-18）FQ-03/04/08/09 非 ✅：其期望事实（预约与协作类系统 /
> 插槽快照·实时刷新·幂等写入 / 内容问答与检索 / 人格层问答）仅存 `content.py` 的
> `resume_sections`（页面展示、不进检索语料），检索/兜底均无法命中 → 拒答或部分答。
> 用户选「路径 A：提升数字分身真实覆盖」——把 4 处事实下沉为可检索 chunk。

## 任务类型
- content 文档补齐（纯内容，无 API/逻辑/隐私护栏变更）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：3bdf067（本轮前 HEAD）

## 精确规范引用
- `docs/fact-consistency/rubric.md` §2（✅/⚠️/❌/🚫 定义）、§3（一致率公式、SLO ≥94%）、§5（事实源唯一）
- `docs/fact-consistency/fact-bank.md` FQ-03/04/08/09（期望事实与溯源）
- `apps/api/app/aiqa/content.py` `build_pages()`（`resume_chunks` 为可检索事实源；`resume_sections` 仅展示）

## 需求来源
- 事实一致率首测 26 题评分（strict 84.6%，未达 SLO ≥94%）：✅22、⚠️2(FQ-04/08)、❌0、🚫0、合法拒答2(FQ-03/09)
- 根因诊断：`fact-bank.md` 期望事实漂移（sections→chunk 未同步）；线上检索 KB(pgvector) 优先、content.py 静态兜底，这 4 题在旧 KB 中本就检索不到 → 静态兜底是有效路径
- 用户 2026-08-18 决策：路径 A（推荐，提升数字分身真实覆盖）

## 目标
把 4 处仅存于 `resume_sections` 的事实下沉为 content.py 可检索 `resume_chunks`，使静态兜底命中，FQ-03/04/08/09 可答且一致，事实一致率重测 ≥94%。

## 非目标
- 不改 KB(pgvector) / CORPUS（已诊断：这 4 题在旧 KB 中检索不到，静态兜底即足够，无需重上传）
- 不改检索/路由/阈值/隐私护栏/API
- 不新增数据表或依赖

## 允许修改路径
- `apps/api/app/aiqa/content.py`（`resume_chunks` 新增 R6 工作经历块 + R3 技术栈块补「人格层问答」+ `build_resume_facts_card` 补工作经历行与「人格层问答」）
- `docs/fact-consistency/fact-bank.md`（FQ-03/04/09 溯源改指 R6、FQ-08 溯源改指 R3；标注 KB 优先/content.py 兜底）
- `apps/web/main.tsx`（04「事实一致率」由"实测待跑"回填实测数字）

## 禁止修改路径
- `apps/api/app/aiqa/service.py`、`retrieval.py`、`persona.py`、`tests/`、`migrations/`、任何 API/SSE/DB/加密/鉴权逻辑
- `scripts/fact_consistency_results.json` 之外任何脚本行为（该 json 为测量转录，如实提交）

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：false（不改可观察行为，仅扩展现有页面知识库内容，使已声明的 SLO 可达成）
- affected_specs：none
- reason：纯内容补齐，与 PRD「回答必须可溯源」一致；`build_resume_facts_card` 的 "MUST stay in sync with resume_chunks" 注释同步更新

## 功能验收
- 静态 `retrieve(q, "resume", None)` 对 FQ-03/04/08/09 命中正确 chunk（已验：FQ-03→R6 0.99、FQ-04→R6 1.27、FQ-08→R3 1.06、FQ-09→R6 0.71）
- 用户 WSL 复测 `python3 scripts/measure_fact_consistency.py`：26/26 OK，无 OFFTOPIC/ERR
- 严格一致率 26/26 = 100%（≥94% ✅），🚫误拒 0，零编造

## 安全与隐私验收
- 不改隐私护栏；新增内容为公开简历事实（工作经历/技术栈），无 PII 外泄

## 性能验收
- 仅静态语料文本新增 ~2 个 chunk（约 150 字），无运行时开销变化

## 变更预算
- max_files：3（`content.py` + `fact-bank.md` + `main.tsx`；`scored-2026-08-18.md`/`fact_consistency_results.json` 为交付证据文档，随提交）
- expected_prod_lines：content.py +~12 / -3
- expected_doc_lines：fact-bank.md +~10 / -6；scored 文档重写（两轮评分）

## 必须运行的测试命令
- WSL：`python3 scripts/measure_fact_consistency.py`（26 题事实一致率重测）
- WSL（回归，可选）：`python3 -m pytest tests/aiqa/test_rag_eval.py -v`（RAG 评测不受影响，CORPUS 未改）
- WSL（前端，纯文案回填）：`cd apps/web && npm run build`

## 回滚方法
- 还原 `content.py`（删除 R6/R3 新增内容、还原 facts card）与 `fact-bank.md`、`main.tsx` 即可，无迁移/数据影响

## 强制停止条件
- 若重测后 FQ-03/04/08/09 仍非 ✅，或 RAG 评测回归失败 → 停止并复盘检索路径

## 交付证据
- commit / PR：（待用户确认后提交，回填 commit hash）
- 修改文件清单：apps/api/app/aiqa/content.py、docs/fact-consistency/fact-bank.md、apps/web/main.tsx
- 测试命令及结果：**PASS — 用户 WSL 复验 2026-08-18 02:27，measure_fact_consistency.py 26/26 OK**（FQ-03/04/08/09 由 OFFTOPIC/⚠️ 转 ✅；严格一致率 26/26=100%，SLO ≥94% 达成，🚫误拒 0）

## 治理备注
- 曾拟改 `test_rag_eval.py` CORPUS 与新增 `scripts/seed_kb.py`（重上传 KB），经诊断确认非必需（这 4 题在旧 KB 中本就检索不到，静态兜底即足够），已撤销/删除，保持单一最小工件。
- 不回删历史 results.json/评分，如实保留两轮证据。
