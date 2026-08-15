# TASK-KB-THRESHOLD-001 相关性阈值（P1：检索无门槛 → 拒答率闭环）

> **状态**：Open（2026-08-15 建；用户授权"现在做 P1 相关性阈值"）
> **依赖**：EVAL-001/002 已验证（拒答型 6→10 条 XFAIL 是可测量缺陷基线）；BGE-M3 接入已验证

## 1. 背景（缺陷 → 修复 → 评测验证 闭环）
评测集捕获的 P1 缺陷：`search_chunks` 无相关性阈值，向量 top-k **硬召回**——
知识库有文档时任何问题（爬虫/天气/住址）都 `grounded=True`（拒答率 0%）。
本任务：加相似度下限 → 低于阈值视为无证据 → 走静态兜底/拒答 → 拒答型 XFAIL 转绿。

## 2. 设计（关键判断）
- **阈值作用在向量相似度**（`1 - (embedding <=> :query)`，语义可靠度量）；
  BM25 单字命中**不算**语义证据（CJK 单字总重叠，否则拒答必挂）。
- `search_chunks(embedding, top_k, min_score=0.0)`：SQL `AND (1 - (c.embedding <=> :query)) >= :min_score`。
- `_knowledge_candidates`：向量检索用 min_score；**vector_hits 为空 → 直接 return []**
  （BM25 单独命中不视为语义证据；min_score=0 时向量总有 top-10，行为不变——兼容现状）。
- **阈值只对真实 embedding 有意义**：哈希相似度无语义含义，阈值会误杀命中型用例。
  因此阈值是配置项 `kb_min_score`（env `JIANLI_KB_MIN_SCORE`，默认 0 = 不生效），
  评测 fixture 按「有无真实 embedding」条件设值（有 → 0.4，无 → 0）。
- 拒答测试改**条件 xfail**：真实 embedding 下必须全绿（offtopic=True），
  哈希下维持 xfail（基线）。

## 3. 变更清单（已批准：用户授权 P1）
- [ ] `app/config.py`：`kb_min_score: float = 0.0` + env 映射
- [ ] `app/aiqa/repository.py`：`search_chunks` 加 `min_score` 参数（SQL 过滤）
- [ ] `app/aiqa/service.py`：`_knowledge_candidates` 传 min_score + vector_hits 空 return []
- [ ] `tests/aiqa/test_rag_eval.py`：fixture 条件设 `kb_min_score`；拒答测试条件 xfail
- [ ] 迁移：无（纯行为变更，无 schema）
- [ ] 依赖：无

## 4. 验收
- [ ] ruff ✅ / mypy ✅ / DB-free ✅（沙箱）
- [ ] WSL（BGE-M3 + 阈值）：拒答型 **XFAIL → PASS（10/10）**、命中型不降（LITERAL 8/8）
- [ ] WSL（哈希，阈值 0）：现状不变（命中 8/8，拒答 xfail）
- [ ] 交付证据回填

## 5. 面试价值
"评测发现检索无相关性阈值（拒答率 0%）→ 加相似度下限（仅向量语义判定）→
拒答率 0%→100%，命中率保持——**缺陷可测量、修复可验证的完整闭环**，
证明我懂 RAG 的召回/拒答边界设计。"
