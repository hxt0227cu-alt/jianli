# TASK-AIQA-GROUNDING-001 简历域事实 grounding 修复（冲 94% 一致率）

> 任务类型：implementation（问答 grounding 修复）
> 本任务解决 TASK-FACT-001 实测暴露的简历域失分：FQ-05/06/09（开放题被 LLM 自由发挥盖过 R2/R4）与 FQ-10（数字分身事实不在检索语料）。
> **两轮修复**：Round-1（`top_k` 3→5 + 数字分身 chunk + persona grounding 指令）仅修好 FQ-10，FQ-05/06/09 仍 ❌（根因是 LLM 忠实度，非召回）；Round-2（选项 B：常驻「硬性事实卡」进 system prompt + 逐字必用硬约束）针对 FQ-05/06/09。修复后目标实测一致率 ≥ 94%（严格 ✅≥25/26）。

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5（取自 `docs/baseline.yml`）
- 基线 commit：development_gate 全 approved；本任务基于当前未提交工作树（HEAD 以 `git log` 为准）

## 精确规范引用
- `apps/api/app/aiqa/retrieval.py` `retrieve()`（默认 `top_k=3`→5）
- `apps/api/app/aiqa/content.py` `build_pages()` `resume_chunks`（5 块，缺数字分身事实）+ 新增 `build_resume_facts_card()`
- `apps/api/app/aiqa/persona.py` `_SYSTEM_PROMPT` + `build_system_prompt(facts_card=None)`
- `apps/api/app/aiqa/service.py` 回答路径（messages2）：`page_key=="resume"` 时注入 `build_resume_facts_card()`
- `scripts/fact_consistency_results.json`（TASK-FACT-001 实测：严格 22/26=84.6%；Round-1 重测 23/26=88.5%，FQ-10✅、FQ-05/06/09 仍 ❌）
- `docs/fact-consistency/fact-bank.md` FQ-05/06/09/10

## 需求来源
- 北极星「简历事实一致率 ≥ 94%」；实测失分题 FQ-05/06/09/10（均简历域）。

## 目标
三处小改，使简历域 4 题命中事实源，实测一致率升至 ≥94%。

## 非目标（明确排除）
- 不改拒答阈值 / 0.47 双层门槛逻辑。
- 不改 jianli 项目域（FQ-11~26 已 16/16 全对，不触碰）。
- 不改 API / SSE 契约 / 迁移 / 依赖。
- 不扩大题库（保持 26 题）。

## 允许修改路径
- `apps/api/app/aiqa/retrieval.py`（`top_k` 3→5）
- `apps/api/app/aiqa/content.py`（`resume_chunks` 新增数字分身块；新增 `build_resume_facts_card()`）
- `apps/api/app/aiqa/persona.py`（`_SYSTEM_PROMPT` 加 grounding 指令；`build_system_prompt` 支持 `facts_card` 入参）
- `apps/api/app/aiqa/service.py`（**仅**回答路径 messages2：`page_key=="resume"` 时向 `build_system_prompt` 注入 `build_resume_facts_card()`；双调用点其余逻辑不变）
- `docs/fact-consistency/fact-bank.md`（FQ-10 溯源注记更新，反映事实已入 chunk）

## 禁止修改路径
- `service.py` 中除「简历域回答路径注入事实卡」之外的编排逻辑（如拒答判定、`_search_candidates`、SSE 帧）、`gateway.py`、`sse.py`
- jianli 项目域 chunks（projects_jianli J0–J7）
- 拒答/阈值/embedding/检索算法本身（仅调 top_k 上限）

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact）
- behavior_change：**true**（简历域软问题回答将更贴合事实源，可观测行为变化）
- affected_specs：srs none / domain_model none / openapi none / security none / test_plan update（新增评测证据）
- reason：改进检索召回上限 + grounding 指令，使回答**重新符合**既有「真实性优先、绝不编造」规范（SRS/领域模型已有该约束），属「Bug 修复使代码重新符合现有 SRS」类，不需改规范。
- 分类：Bug 修复使代码重新符合现有 SRS（非改变外部行为的新功能）。

## 功能验收
- `python3 scripts/measure_fact_consistency.py --only 5,6,9,10` 重测：FQ-05 命中"先设计后编码"、FQ-06 命中"可观测性/可演进性/契约测试"、FQ-09 命中"内容问答与检索"、FQ-10 不再 OFFTOPIC 且答出"数字分身"。
- 全量 26 题重测：严格 ✅ ≥ 25（≥94%）。
- 回归：FQ-01~04/07/08 仍 ✅（top_k=5 多带入 R2/R4 不应导致错误事实）。

## 安全与隐私验收
- 无密钥 / 权限 / 审计变更。

## 性能验收
- `top_k` 5 对 5~8 块小语料无性能影响；LLM 上下文略增，单题 token 增量可忽略。

## 变更预算（change_budget）
- max_files：5（retrieval.py / content.py / persona.py / service.py / fact-bank.md）
- expected_prod_lines：~40

## 必须运行的测试命令
- `python3 -m py_compile apps/api/app/aiqa/retrieval.py apps/api/app/aiqa/content.py apps/api/app/aiqa/persona.py`
- `python3 scripts/measure_fact_consistency.py`（WSL，uvicorn 已 restart + LLM 已配）

## 回滚方法
- 三处均为局部常量/列表/字符串改动，git revert 或手动回退 `top_k=3` / 删 chunk / 删 prompt 句即还原。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 若需改拒答阈值 / API / 迁移 / 依赖 → 立即停止并报告。
- 若全量重测出现 jianli 域（FQ-11~26）回归 → 停止，排查 top_k 影响，不得硬改题库凑分。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：本提交（HEAD，含 tasks/TASK-AIQA-GROUNDING-001.md）
- 修改文件清单：retrieval.py / content.py / persona.py / service.py / fact-bank.md
- 测试命令及结果：
  - Round-1 重测（WSL）：`measure_fact_consistency.py` 全量 → 严格 **23/26=88.5%**（FQ-10✅ 修好；FQ-05/06/09 仍 ❌，根因=LLM 忠实度非召回）
  - **Round-2 重测（事实卡，WSL，generated_at=2026-08-17T11:52:39Z）：`measure_fact_consistency.py` 全量 → 严格 ✅ 26/26 = 100%**（FQ-05「我偏好先设计后编码」/ FQ-06「可观测性、可演进性与契约测试」/ FQ-09「内容问答与检索相关功能」全部逐字命中；jianli 域 16/16 无回归）。≥94% SLO 已达成。
- lint / typecheck：py_compile 通过（3 模块）；事实卡组装单测通过（card 逐字 + pin 指令命中 + 无卡时行为不变）
- DB 迁移验证：无
- 验收证据：`scripts/fact_consistency_results.json`（26 题全文 + grounded/offtopic/model/usage），重点 FQ-05/06/09/10 均 ✅
- 变更预算实际值：max_files=5 / 生产行数≈40
- 未解决风险：事实卡强制逐字可能略降开放题自然度（可接受，真实性优先）；LLM 非确定性下偶发漂移概率低（事实卡进 system prompt 已大幅抑制），以脚本可复跑为准。
- 是否偏离 TASK：否（Round-2 事实卡属同一 grounding 目标 amend，已更新允许/禁止清单与预算）
- 规范影响结论：none（bug-fix 对齐既有规范）
- spec_sync：clean
- verified_commit：本提交（HEAD）
- **关闭门禁**：① 全量重测严格 ✅ 26/26 ≥25 ✅；② 规范影响 none ✅；③ spec_sync=clean ✅；④ verified_commit 待提交。

## 关联
- 上游：TASK-FACT-001（评测脚手架 + 实测 84.6%）
- 同伴：`scripts/measure_fact_consistency.py`
