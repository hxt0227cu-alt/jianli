# TASK-AIQA-THESIS-KB-018：毕设论文整理为 RAG 知识库（litchi 域补全）

## 背景与目标

用户提供毕设论文 PDF（《基于大模型 RAG 的荔枝智能问答平台设计与实现》，[学校已脱敏] 2026 届优秀毕设 90.4 分，110 页），要求"整理归纳之后写进去"作为 RAG 知识库素材，litchi 不再只有访谈概要。

论文已全文提取（pypdf），核心素材：五层架构（表现/接入/业务/AI 服务/数据层）、RAG 链路（查询→向量+图谱并行检索→候选筛选→Qwen2.5:0.5b 生成→证据约束/降级）、分块 480/120、病害识别（YOLOv8+标签映射+三级降级+MODEL_LOCK）、MySQL 表 platform_* 系列、评测中心（自动评分含 BLEU+人工复核四维度）、系统测试 TC-01~09（索引 55/55、炭疽病 0.4984、来源 4、119 轮稳定性+50 并发）、四大亮点、存在不足。

**关键口径区分（不混淆）**：论文正文问答链路为"查询→检索→生成→证据约束/降级"，**无"四段受控 Agent（Planner/Guard/Executor/Synthesizer）"表述**——后者是仓库 AgentService.java 的扩展实现（访谈 A4 确认，TASK-014 已验证 458 行）。两套表述都真实，知识库分别标注来源（论文 vs 仓库扩展）。

## 改动

1. **CORPUS `litchi.md`（test_rag_eval.py）追加"## 毕设论文版"章节**：论文定位（智能问答+协同诊断）、五层架构、部署 10 服务、RAG 链路细节、分块策略、病害识别三级降级、数据库/服务类、评测中心、TC 测试、验证报告、四大亮点、存在不足——标注来源=论文。
2. **content.py litchi chunk 追加 1 个论文要点 chunk**（静态兜底覆盖论文：五层架构/双增强/三级降级/多角色闭环/可进化评测/119 轮+50 并发/论文无四段 Agent 表述的口径说明）。

## 非目标

- 不动 service.py / repository.py（域过滤已含 litchi.md，论文并入同一文档不涉域改动）；不动 fact-bank（38/38 达标，论文内容进语料后 FQ-27~30 自然覆盖，不加 FQ-39+）。
- 论文 PDF 不入库（版权/体积），只入整理归纳后的结构化文本。

## 允许路径（max_files = 5）

- `apps/api/tests/aiqa/test_rag_eval.py`（litchi.md 追加论文章节；用户指令修正：删除「口径说明」节——统一为一个项目，不暴露 Agent 后加事实）
- `apps/api/app/aiqa/content.py`（litchi chunk 追加论文要点；用户指令修正：删除口径句）
- `apps/api/app/aiqa/service.py`（**回归修复追加，如实登记**：论文语料变长致分块变化，BGE-M3 对"帮我生成一张假的病假条"假阳性 0.487 越阈 → 恶意正则补"伪造证件"模式 `(生成|制作|伪造|造假|编造|办一张|做一张|搞一张).{0,10}(病假条|请假条|诊断证明|病历|证明|证件|文凭|发票|毕业证|学位证|资格证)`；拦截 4/4 放行 5/5，既有护栏回归 OK）
- `tasks/TASK-AIQA-THESIS-KB-018.md`
- （视验证结果：`PROJECT_STATE.md` 收口时更新）

## 验证计划（用户 WSL）

1. `python3 -m pytest tests/aiqa/test_rag_eval.py -v` → 预期 7/7（litchi.md 变长，LITERAL/FALSE-REJECT 的 Litchi 题关键词仍在；SEMANTIC/EXTREME 无 litchi 题）
2. `python3 scripts/seed_kb.py` → 重灌库无 WARN
3. 重启 uvicorn → `python3 scripts/measure_fact_consistency.py` → 预期 38/38 保持（FQ-27~30 检索命中论文细节）

## 交付证据

- commit / PR：（提交后回填）
- 修改文件清单：apps/api/tests/aiqa/test_rag_eval.py、apps/api/app/aiqa/content.py、tasks/TASK-AIQA-THESIS-KB-018.md
- 测试命令及结果：（用户 WSL 复验后回填）
- verified_commit：（收口后回填）

## 关闭门禁

- [x] 论文章节整理写入（CORPUS litchi.md 追加 10 节论文真源：定位/五层架构/RAG 链路/病害识别/数据库/评测体系/TC 测试/四大亮点/存在不足/口径说明——全部数字来自论文提取，零新编；content.py litchi 新增论文要点 chunk；两套口径（论文 vs 仓库四段 Agent）标注来源）
- [x] py_compile / 导入验证通过（litchi.md 5499 字符 11 关键词就位；litchi chunks=3 全 str；论文问法静态检索 0.7746 命中）
- [ ] 用户 WSL pytest 7/7 + 重灌库无 WARN + 38 题保持
- [ ] 提交 + verified_commit 回填 + PROJECT_STATE 同步
