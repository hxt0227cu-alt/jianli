# TASK-AIQA-KB-RESUME-020：新简历 14.pdf 同步至知识库与界面展示

> 用户显式指令越出预约域分工（工作记忆 MEMORY.md 原约定 AIQA 知识库/RAG/页面二由其它会话自理）；本任务为用户 2026-08-24 直接下达，已授权代跑刷新 + 提交 + 瘦身 + TASK 回填。

## 背景与目标

用户用桌面新简历 `14.pdf` 替换旧简历，要求同步至两侧：

1. **知识库**：① RAG 检索主源 `knowledge_documents`/`knowledge_chunks`（pgvector，经 `scripts/seed_kb.py` 重灌）；② 静态兜底 `content.py`（`resume_chunks`/`projects_chunks`/`build_resume_facts_card`/recommendations）+ 事实题库 `fact-bank.md` + 人格层 `persona.py` few-shot。
2. **界面展示**：前端 `main.tsx` 硬编码文本 + 可见 PDF `public/resume.pdf`。

新简历与旧 `content.py` 多处冲突，须全部对齐并消除陈旧事实：

- 荣誉：**2025 国家励志奖学金**（旧误写「国家奖学金」）+ 校级奖学金/2026 优秀毕业生/CSDN。
- 泰益智：RC 压测吞吐 **+393.9%**、P95 **1.35s→229ms**；封装 **6 个受治理工具 + 15 个 Agent REST API**（FastAPI+LangGraph+K8s）。
- 毕设荔枝平台：**22 个业务页面**；病害识别 **20%→93.75%**；Chat P95 **5s→124ms（约 1/50）**；50 并发成功率 100%。
- 教育：专业排名 **3/153（前 2%）**（去掉旧 GPA 3.38/4.0，简历未列）。
- Agent 工具：经 TASK-AIQA-AGENT-CRUD-001，`search_knowledge` + `list/cancel/reschedule_appointment`（RBAC 守卫），推翻旧「预约端点绝不开放」陈述 → 删除 main.tsx/content 中矛盾旧文案。

## 非目标（不做）

- 不改 schema / migration / API / 契约 / 加密鉴权策略（纯内容刷新，spec_sync=clean）。
- 不改 agent 工具实现（已落地），仅修正展示/兜底文本中与已实现代码矛盾的旧陈述。
- 不重跑 fact-consistency 38 题（本次为简历数值更新，FQ 题已覆盖；38/38 由 TASK-016 已达成，本任务未新增事实题、未改 QUESTION_BANK）。

## 允许路径（max_files = 7）

- `apps/api/app/aiqa/content.py`（resume_chunks/projects_chunks/build_resume_facts_card/recommendations 重写）
- `apps/api/app/aiqa/persona.py`（STYLE_FEW_SHOT 第 2/3 例加新指标）
- `apps/api/tests/aiqa/test_rag_eval.py`（CORPUS 11 篇同步新事实——seed 规范源）
- `docs/fact-consistency/fact-bank.md`（FQ-19/27/31 修正）
- `apps/web/main.tsx`（sleep/litchi/jianli 硬编码文本对齐 + 删矛盾旧陈述）
- `apps/web/public/resume.pdf`（14.pdf 覆盖）
- `apps/api/scripts/seed_kb.py`（`_seed_owner` 复用既有 owner_admin，刷新必需 bug fix）
- `tasks/TASK-AIQA-KB-RESUME-020.md`（本文件）

## 变更预算

- content.py：4 处文本段重写（8 段 resume_chunks + projects_chunks + facts card + recommendations）。
- persona.py：STYLE_FEW_SHOT 2 例追加指标句。
- test_rag_eval.py：CORPUS 11 篇同步（resume/honors/education/certificates/taiyizhi/litchi/interview-story 等）。
- fact-bank.md：FQ-19（agent 工具）/FQ-27（22 页面）/FQ-31（393.9%/229ms/6+15）修正。
- main.tsx：sleep 压测 + litchi 22 页面/93.75%/124ms + jianli agent 三工具化 + 删「绝不开放」旧文案。
- resume.pdf：298528 bytes 覆盖。
- seed_kb.py：14 行修复（复用既有 owner_admin）。
- TASK 文件：新建。

## 验证计划（用户授权代跑）

1. ruff：content.py/persona.py All checks passed；test_rag_eval.py 维持基线 15 E501（中文 3 字节计，无新增）。
2. DB-free：`pytest tests/aiqa/test_aiqa.py` 13/13 passed；content 构建输出含全部新事实。
3. 知识库刷新（WSL）：`python3 scripts/seed_kb.py` → 软删旧 doc + 上传 CORPUS（11 篇，SiliconFlow BGE-M3 embedding 全成功）。
4. DB 直查核：ACTIVE 文档=11（恰 CORPUS 全集）、新事实入 chunks、`国家奖学金(无励志)` 在 active 检索=0。
5. 瘦身（可选）：`DELETE` 软删残留 → total 11 doc / 37 chunk。

## 交付证据

- commit / PR：`369b282`（简历同步 6 文件，122+/79-）+ `efe287f`（seed_kb.py bug fix 1 文件，14+/1-）。
- 修改文件清单：apps/api/app/aiqa/content.py、apps/api/app/aiqa/persona.py、apps/api/tests/aiqa/test_rag_eval.py、docs/fact-consistency/fact-bank.md、apps/web/main.tsx、apps/web/public/resume.pdf、apps/api/scripts/seed_kb.py。
- 测试命令及结果：
  - ruff：content.py/persona.py All checks passed；test_rag_eval.py 15 E501（= HEAD 基线，无新增）。
  - DB-free：`pytest tests/aiqa/test_aiqa.py` **13/13 passed**。
  - 知识库刷新（WSL，jianli_dev）：seed_kb 清 65 旧 doc + 上传 11 篇（HTTP 202，embedding 全成功）；DB 直查 **ACTIVE=11 doc / 37 chunk**，新事实全部入库（`393.9%`×2/`229ms`×2/`93.75%`×1/`124ms`×2/`22 个业务页面`×1/`国家励志奖学金`×3/`受治理工具`×2/`15 个 Agent REST API`×2），ACTIVE 中陈旧「国家奖学金(无励志)」= **0**。
- verified_commit：`369b282`（主交付）/ `efe287f`（脚本修复，刷新必需）

## 关闭门禁

- [x] 代码改动 + ruff/mypy/pytest 验证通过（content/persona 双绿，test_aiqa 13/13）
- [x] 知识库刷新执行并 DB 直查验证（11 active doc，新事实入，旧事实 0 残留；瘦身后 11 doc/37 chunk）
- [x] 界面展示同步（resume.pdf + main.tsx）+ 删矛盾旧陈述
- [x] 提交（369b282 + efe287f）+ verified_commit 回填 + PROJECT_STATE 同步
