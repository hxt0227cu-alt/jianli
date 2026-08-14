# TASK-KB-RAG-001 RAG 检索质量工程：分块 + 混合检索（BM25+向量 RRF）

> **状态**：Open（2026-08-14 建，用户选定"B 混合检索+分块"，方向聚焦 AI Agent/RAG，CRUD 类暂停）
> **依赖**：M6 已关闭（知识库摄取/检索就绪）；TASK-KB-PDF-001 已关闭（PDF 摄取就绪）

## 1. 任务类型
- implementation + **新迁移 0006（chunk 表，用户选 B 预批准，schema 见 §5）**

## 2. 精确规范引用
- OpenAPI v0.2：`streamAnswer` citations 帧（`{doc, fragment}`）——**契约不变**，fragment 语义从"整篇"升级为"chunk 序号"
- 领域模型 v1.1.5 §6.14（knowledge_documents/索引版本）；0005 embedding 列
- 既有实现：`aiqa/repository.py`（KnowledgeRepository.search 整篇向量）、`aiqa/service.py`（upload/`_knowledge_candidates`）、`aiqa/retrieval.py`（CJK 词元）

## 3. 目标
1. **分块（chunking）**：上传文档按 chunk 切分（默认 500 字符/50 重叠，段落边界优先），每 chunk 一个 embedding 存入新表 `knowledge_chunks`；`knowledge_documents.embedding` 列**弃用不再写入**（保留列，NULL）
2. **混合检索**：query embedding → chunk 向量检索 top-K + query 词元 → 纯 Python **BM25** top-K → **RRF 融合**（`Σ 1/(k+rank)`，k=60）→ top chunks；按 doc 聚合去重；`streamAnswer` 知识库检索改走 chunk 级混合检索（citations 显示 `doc · chunk序号`）
3. 删除文档即禁检索（doc 层软删，search 过滤）；上传去重/状态机不变

## 4. 非目标
- 向量索引（hnsw/ivfflat，文档量小全表扫描够）；重排序模型（rerank）；OCR
- RAG 评测集（A 方向，后续）；Agent 只读工具（C，后续）
- CRUD 类前端（评分/设置/通知偏好）——用户明确暂停

## 5. 已批准的 DB / API / 依赖变更（用户 2026-08-14 选 B 批准）
- **DB（迁移 0006_knowledge_chunks，用户审批）**：
  ```sql
  CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    doc_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    seq INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (doc_id, seq)
  );
  ```
  downgrade: DROP TABLE knowledge_chunks
- API：无契约变更（citations 帧格式不变，fragment 语义升级为 chunk 序号）
- 依赖：无新增（BM25 纯 Python）

## 6. 允许修改路径（change_budget：max_files=10）
- `apps/api/migrations/versions/0006_knowledge_chunks.py`（新建）
- `apps/api/app/aiqa/chunking.py`（新建，切分）
- `apps/api/app/aiqa/bm25.py`（新建，纯 Python BM25）
- `apps/api/app/aiqa/repository.py`（KnowledgeRepository：+replace_chunks/+search_chunks/+delete chunks 适配；search 改 chunk 级）
- `apps/api/app/aiqa/service.py`（upload chunk 化；`_knowledge_candidates` 改混合检索）
- `apps/api/app/aiqa/runtime.py`（装配 bm25 或 service 内建）
- `apps/api/tests/migrations/test_aiqa_schema.py`（+0006 shape 断言）
- `apps/api/tests/aiqa/test_knowledge.py`（+chunk 命中/混合检索用例；既有断言保持）
- `PROJECT_STATE.md` / `tasks/TASK-KB-RAG-001.md`

## 7. 禁止修改路径
- OpenAPI/sse.md 契约（citations 字段不变）；鉴权/加密；既有前端（纯后端任务）

## 8. 验收标准
- 后端：ruff ✅ + mypy ✅ + DB-free ✅；迁移测试（up/down 可逆 + chunk 表 shape）✅
- 真实集成（WSL）：上传长文档 → chunk 数>1 → 问包含单个 chunk 特有内容的问题 → citations 命中正确 doc·chunk；删除 → 不再命中；去重/PDF 用例不回归
- `_knowledge_candidates`：知识库优先、静态兜底不变

## 9. 强制停止条件
- 未列明变更（改契约/新增依赖/新表未批）→ 停止报告

## 10. 交付证据（2026-08-14 已回填；任务待用户授权关闭）
- 实现 commit：`25a3fc3`（8 files / +388：0006 迁移 + chunking/bm25/repository/service + 迁移 shape 断言 + 集成用例）
- 门禁：ruff ✅ + mypy 45 files ✅ + DB-free 14 passed ✅
- **用户 WSL 验证（2026-08-14）**：`pytest tests/migrations/test_aiqa_schema.py tests/aiqa/test_knowledge.py -v` **12 passed in 13.67s** ✅（迁移 5：含 0006 knowledge_chunks shape + up/down 可逆；知识库 7：含 test_chunked_document_recall 长文档中段埋词 chunk 级命中）；`verified_commit=25a3fc3`

## 11. 关联
- 前置：M6 / TASK-KB-PDF-001；后续：A 评测体系（chunk 级检索可评测）、C Agent 只读工具
