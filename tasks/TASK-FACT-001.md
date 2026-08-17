# TASK-FACT-001 简历事实一致率评测脚手架（题库 + rubric + 测量脚本）

> 任务类型：documentation + test（评测脚手架，不改变系统行为）
> 本任务为页面二 04「简历事实一致率 ≥ 94%」SLO 提供**可复跑的度量方法**，是 Task ①。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5（取自 `docs/baseline.yml`）
- 基线 commit：development_gate 全 approved，HEAD 以 `git log` 为准（本任务不依赖特定 commit）

## 精确规范引用
- `apps/api/app/aiqa/content.py` `build_pages()` 中 `resume` 页 chunks（doc="简历"）+ `projects` 页 `projects_jianli` chunks（doc="jianli"）——**唯一事实源（ground truth）**。
- 页面稿 `docs/page2-jianli-01-04-draft.md` §04「诚实边界」：94% 事实一致率为 SLO 目标，专项评测集构建中。
- 用户决策（2026-08-17）：事实源用 `content.py` 的 jianli chunks（含 resume chunks 全检索语料）；题库规模直接 26 题（对齐 R1–R26 覆盖意图）。

## 需求来源
- 北极星指标「简历事实一致率 ≥ 94%」（SLO 目标，待本任务脚手架实测）。

## 目标
交付一套**只读、可复跑**的事实一致率评测脚手架：26 题题库（含期望事实 + 判定要点）、评定 rubric、测量脚本（产出 Q+A 转录）。

## 非目标（明确排除）
- 不修改 `content.py`、不修改任何服务/检索/阈值代码。
- 不自动判定一致率（人工对照打分，避免模型自评偏差）。
- 不考教育背景等仅 `sections` 展示、不进检索语料的字段；不考 sleep/litchi 细节（本次聚焦 jianli 一致性）。
- 不实现"转人工/留言"入口（产品决策不实现）。

## 允许修改路径
- `docs/fact-consistency/fact-bank.md`（新建，26 题题库）
- `docs/fact-consistency/rubric.md`（新建，评定口径 + 公式）
- `scripts/measure_fact_consistency.py`（新建，只读测量脚本）

## 禁止修改路径
- `apps/api/app/aiqa/*`（任何代码）
- `content.py` chunk 文本（事实源本身不得在本任务改动；若发现期望值错，走内容变更流程而非静默改题凑分）
- 迁移 / API / 依赖

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：**false**（只读脚本 + 文档，不改变用户可观察行为）
- affected_specs：srs none / domain_model none / openapi none / security none / test_plan update（新增评测集，属补充非冲突）
- reason：纯评测脚手架，不触碰生产行为；与现有 SRS/领域模型/OpenAPI 无冲突。
- 分类：文档 + 测试脚手架，非代码重构、非行为变更。

## 功能验收
- `python3 scripts/measure_fact_consistency.py` 能向 `/answers:stream` 发 26 题并落盘 `scripts/fact_consistency_results.json`，每题含 `answer_text` + `offtopic`/`grounded` 标记。
- 题库 26 题期望事实均可溯源至 `content.py` chunk 文本。

## 安全与隐私验收
- 脚本只发请求 + 落盘本地 JSON，不写密钥、不改运行态、不接触外部网络（仅本机 uvicorn）。

## 性能验收
- 26 题串行请求，单题超时 60s（env `JIANLI_AIQA_TIMEOUT` 可调），整体应在数分钟内完成。

## 变更预算（change_budget）
- max_files：3（两个 md + 一个 py）
- expected_prod_lines：0（无生产代码）
- expected_test_lines：~150（测量脚本）

## 必须运行的测试命令
- `python3 scripts/measure_fact_consistency.py`（冒烟：确认能跑通、落盘 JSON）
- 人工：`fact_consistency_results.json` 对照 `fact-bank.md` 逐题打分，按 `rubric.md` 算一致率。

## 回滚方法
- 纯新增文件，删除三个文件即回滚，无迁移/配置副作用。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 若发现需改 `content.py` chunk / 检索阈值 / API → 立即停止并报告，不得在本任务内改。
- 若发现期望值写错 → 走内容变更流程，不得静默改题凑分。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：本提交（HEAD，含 tasks/TASK-FACT-001.md）
- 修改文件清单：`docs/fact-consistency/fact-bank.md`、`docs/fact-consistency/rubric.md`、`scripts/measure_fact_consistency.py`
- 测试命令及结果：`python3 scripts/measure_fact_consistency.py` → 26 题转录落盘；人工一致率评分 <待用户跑真实 LLM 后回填>
- lint / typecheck：脚本为独立工具，不进 app 包；ruff 不覆盖 scripts/（如需 `python3 -m py_compile scripts/measure_fact_consistency.py` 通过）
- DB 迁移验证：无
- 验收证据：<待用户跑真实 LLM 后附 JSON 摘录>
- 变更预算实际值：max_files=3 / 生产行数=0 / 脚本约 150 行
- 未解决风险：真实 LLM 未跑前一致率为空（SLO 仍为待测目标值）；脚本依赖 uvicorn 已起 + `JIANLI_LLM_*`/`JIANLI_LLM_EMBEDDING_*` 已配。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean（无上游规范变更）
- verified_commit：本提交（HEAD）
- **关闭门禁**：① 脚本冒烟通过；② 规范影响 none；③ spec_sync=clean；④ verified_commit 已记录。人工一致率评分非关闭硬性门槛（属后续使用），但须在交付证据注明「待用户跑真实 LLM 后回填」。

## 关联
- 上游：页面稿 `docs/page2-jianli-01-04-draft.md` §04 诚实边界（94% SLO）
- 同伴：`scripts/measure_cost.py`（成本测量，同类只读工具）
