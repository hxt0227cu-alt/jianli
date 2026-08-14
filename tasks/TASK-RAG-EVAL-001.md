# TASK-RAG-EVAL-001 RAG 评测集（检索/拒答质量量化）

> **状态**：Open（2026-08-14 建；用户确认"开工"，P0 面试工程——把检索质量变成数字）
> **依赖**：TASK-KB-RAG-001（分块+混合检索）已验证；测试复用 test_knowledge 的 real_stack 模式（真实 PG）

## 1. 背景（用户核心关切）
用户项目用于**面试 AI 全栈（Agent/RAG 方向）**，担心被当成"调 API"。
回答"准不准"必须可量化 → 建评测集 + 断言门槛 + 一条命令出数字。

## 2. 目标
1. **评测语料**（测试内嵌 3 篇中文 md：简历/两项目——模拟真实简历知识库，可重复、不依赖用户真素材）
2. **评测用例**（≈14 条，分两类）：
   - 命中型（8 条）：问教育/技能/项目架构/RAG 做法 → 断言 `grounded=true` 且 citations 命中期望文档
   - 拒答型（6 条）：越界（爬虫/天气/炒股）+ 简历未写细节（住址/生日）→ 断言 `offtopic=true`（不编造）
3. **数字输出**：pytest 汇总打印 `召回率@k = x/y`、`拒答正确率 = x/y`；断言保守门槛（哈希 embedding 下基线，先跑出真实数字再定）
4. **CI 命令**：一条 pytest 跑完（真实 PG），可进 WSL 验证

## 3. 范围（严格限定）
- ✅ 新增 `tests/aiqa/test_rag_eval.py`（内嵌语料 + 14 用例 + 汇总打印）
- ✅ 新建任务单本文件
- ❌ **不动** `app/aiqa/service.py` / repository / 迁移（相关性阈值 = P1 单独任务，等真实 embedding 配好再动，避免哈希阈值误伤）
- ❌ 不加任何运行时依赖（复用 LocalEmbeddingGateway / pypdf 等既有）

## 4. 技术要点
- 复用 `tests/aiqa/test_knowledge.py` 的 `real_stack`/`_upload`/`_stream_answer` 模式（自包含 copy，不跨文件 import 测试助手）
- 上传走真实管线（admin 上传 → chunk → embedding → indexed），匿名 streamAnswer 测检索（知识库检索对公开问答生效）
- 语料用 `.encode()`（**bytes 字面量不能含中文**——M6 三轮教训）
- 文档内容 ≥500 字触发分块，关键词分散

## 5. 验收
- [ ] ruff ✅ + mypy ✅（沙箱）
- [ ] WSL 真实 PG：`PYTHONPATH=. pytest tests/aiqa/test_rag_eval.py -v` 全绿 + 打印出命中/拒答数字
- [ ] 任务单交付证据回填

## 6. 面试价值（写进简历/话术）
"RAG 评测回归：14 条评测集（命中/越界/无依据），召回率 xx% / 拒答率 xx%，一条命令可跑；换 embedding 后数字对比（哈希 xx% → 真实 xx%）证明检索质量可量化、可优化。"
