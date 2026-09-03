# TASK-AIQA-KB-EXPAND-014 Round 2 访谈产出落地知识库

> Round 2 访谈（docs/interviews/round2-questions.md + round2-answers.md）A–F 全部完成（2026-08-18），
> 产出大量仓库缺失的真实事实（Litchi 架构细节 / 泰益智 84 例与 51 重复等深挖 / 技能证据 / 行为故事 / 动机 A 版）。
> 本任务把访谈产出落地为：评测语料（CORPUS）→ 静态页（content.py）→ 题库（fact-bank FQ-27+）→ live KB 灌库。

## 任务类型
- content / 语料扩展（无 API / 逻辑 / 隐私护栏 / 迁移变更）

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：c1a1766（TASK-013 收口后 HEAD）

## 精确规范引用
- `docs/fact-consistency/rubric.md` §5（事实源唯一、改期望值须走变更）
- `docs/fact-consistency/fact-bank.md` 备注（"如需扩展，新增 FQ-27+ 并在脚本 QUESTION_BANK 同步"）
- `apps/api/tests/aiqa/test_rag_eval.py`（CORPUS 结构）
- `apps/api/app/aiqa/content.py`（`projects_chunks` litchi 占位块）
- 访谈产出：`docs/interviews/round2-answers.md`（A–F 全部，含诚实边界标注）

## 需求来源
- 用户 2026-08-18：「我们继续补知识库的内容吧」→ 确认 Round 2 访谈 → A–F 全部答完 → 落地。
- 访谈产出事实（示例）：Litchi 一人独立 8 模块 12,622 Java 行 / qwen2.5:0.5b 本地 Ollama / Milvus 哈希向量（无 GPU 约束）/ 四段 Agent / 60 条评测；泰益智 84 例 7 类细分 / 67/84 provider 漂移 / 51 条重复根因（ClickHouse Array(UUID)）/ 18720=3×6240 / 20 个 ADR / 21 NestJS 模块 / ESP32 13,223 行 C++；行为故事（Figma vs 小程序端、1 对 1 带人、文档化交接）；动机 A 版（2023 起 AI 编程、深圳南山、5 年架构师、可交接自荐）。

## 目标
把访谈产出写入知识库三层（CORPUS / content.py / live KB），并扩 fact-bank FQ-27+，使数字分身能回答 Litchi 架构细节、sleep 踩坑、行为与动机类问题（此前 KB 全无）。

## 非目标
- 不改 `service.py` / `retrieval.py` / `persona.py` / 迁移 / API / 加密 / 鉴权 / 隐私护栏
- 不改已有冻结测试断言（LITERAL 8/8、REJECT 10/10、FALSE-REJECT 8/8 等阈值不变）
- 不改泰益智仓库（sleep202603-an 只读查证，不入库、不改动）
- 不做 FQ-27+ 之外的新题库扩展
- 不编造访谈中标注为【诚实边界/推断】的内容（如实保留）

## 允许修改路径
- `apps/api/tests/aiqa/test_rag_eval.py`（CORPUS：litchi.md 扩写真实架构细节、taiyizhi.md 补 84 例细分/漂移/51 重复细节、**新增 interview-story.md 文档**收纳行为与动机；保留现有 doc key 与冻结用例）
- `apps/api/app/aiqa/content.py`（`projects_chunks` litchi 占位块升级为真实事实 chunk；如需同步 resume facts card 不涉及——facts card 已在 TASK-013 定型，除非必要不动）
- `docs/fact-consistency/fact-bank.md`（新增 FQ-27+：litchi 架构 / sleep 细节 / 行为 / 动机，溯源指向新 chunk 与 story 文档）
- `scripts/measure_fact_consistency.py`（QUESTION_BANK 同步新增 FQ-27+ 条目）
- `apps/api/scripts/seed_kb.py`（**重建**：修复 env 加载——`set -a; source .env.local; set +a` 或脚本内解析 `.env.local`，进程内 ASGI 上传 CORPUS 到 live 库；上轮因未加载 .env.local 误连空库，本次修正）
- `docs/interviews/round2-answers.md`（状态标注，访谈已完成）

## 禁止修改路径
- `apps/api/app/aiqa/service.py`、`retrieval.py`、`persona.py`、`gateway.py`、`embeddings.py`、`sse.py`
- `apps/api/app/**` 其他域、`migrations/`、`docs/api/**`
- 泰益智仓库 `C:\Users\<user>\Desktop\sleep202603-an`（只读）
- 用户并行工作区文件：`apps/api/tests/test_worker.py`、`apps/api/var/`、`tasks/TASK-M3-WORKER-SMTP-TEST.md`

## 已批准的 DB / API / 依赖变更
- 无（live KB 灌库为数据操作，非 schema/API 变更）

## 规范影响评估
- behavior_change：false（不改变任何可观察行为；仅扩展现有知识库内容与题库，使数字分身能回答更多真实问题）
- affected_specs：none（fact-bank 为题库扩展，FQ-27+ 按备注预留口子新增）
- reason：纯内容补齐；RAG 评测断言/阈值不变（新增 story 文档为独立 doc，不改变既有用例的期望 doc 与拒绝集）

## 功能验收
- 评测不回归：WSL `python3 -m pytest tests/aiqa/test_rag_eval.py -v` 全绿（LITERAL 8/8、REJECT 10/10、FALSE-REJECT 8/8、privacy、semantic、extreme）
- 新题库全绿：WSL `python3 scripts/measure_fact_consistency.py` → 原 FQ-01..26 保持 26/26 + FQ-27+ 新增题全 ✅
- KB 检索路径首次有真内容：live 库灌库后 `_knowledge_candidates` 命中（可由 measure 间接验证：FQ-27+ 若走 KB 命中则证明灌库生效）

## 安全与隐私验收
- 不改隐私护栏；访谈产出含住址/工资等隐私测试用例仅作评测（REJECT/隐私用例不变），不入库为可答事实
- interview-story.md 为公开行为故事与动机，无 PII 外泄

## 性能验收
- 静态语料新增 ~2-3 chunk（litchi 升级 + story），运行时无开销变化；CORPUS 新增 1 文档对检索空间影响由评测回归验证

## 变更预算
- max_files：6（test_rag_eval.py + content.py + fact-bank.md + measure_fact_consistency.py + seed_kb.py + round2-answers.md 状态）
- expected_prod_lines：content.py +~6 / -1；test_rag_eval.py CORPUS +~60 行（litchi 扩写 + taiyizhi 补充 + story 文档）
- expected_doc_lines：fact-bank.md +~40（FQ-27+ 约 10-14 题）；measure QUESTION_BANK +~12

## 必须运行的测试命令
- WSL：`python3 -m pytest tests/aiqa/test_rag_eval.py -v`（评测回归）
- WSL：`cd /mnt/c/Users/<user>/Desktop/jianli && python3 scripts/measure_fact_consistency.py`（FQ-01..26 保持 + FQ-27+ 全绿）
- WSL：`set -a; source .env.local; set +a; cd apps/api && python3 scripts/seed_kb.py`（live KB 灌库，先清理 10 篇 failed）

## 回滚方法
- 还原 test_rag_eval.py CORPUS / content.py / fact-bank.md / measure QUESTION_BANK / 删除 seed_kb.py 即可（无迁移/数据 schema 影响；live KB 已灌文档可删）

## 强制停止条件
- RAG 评测回归失败（LITERAL/REJECT/FALSE-REJECT 任一降级）→ 停止并收敛 CORPUS 改动
- 访谈产出中【诚实边界/推断】内容被误写成既定事实 → 停止并修正

## 交付证据
- commit / PR：（待执行后回填）
- 修改文件清单：（待执行后回填）
- 测试命令及结果：（待执行后回填）

## 治理备注
- 工作树有用户并行改动（apps/api/tests/test_worker.py M3 E2E + apps/api/var/ + TASK-M3-WORKER-SMTP-TEST.md）——提交必须显式 add 本任务文件，禁止 `git add -A`。
- live KB 灌库需用户 WSL 执行（seed_kb.py 已修正 env 加载）。
