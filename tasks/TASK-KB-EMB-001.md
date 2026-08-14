# TASK-KB-EMB-001 真实 embedding 接入（硅基流动 BGE-M3）

> **状态**：Open（2026-08-14 建；用户选定"硅基流动（BGE-M3）"为 P0 真实 embedding）
> **依赖**：TASK-RAG-EVAL-001 已验证（HIT=8/8，REJECT=0/6 XFAIL）；迁移 0006 就绪

## 1. 背景（面试工程 P0 第二步）
当前 embedding 是本地哈希降级（无语义）——"向量检索"名不副实，面试必被戳。
用户选定 **硅基流动 BAAI/bge-m3**（1024 维、中文效果佳、OpenAI 兼容、价格低）换真实语义向量。

## 2. 已批准变更（用户 2026-08-14 选定 BGE-M3 即预批准）
- **DB（迁移 0007 `0007_embedding_1024`）**：`knowledge_chunks.embedding` 从 `vector(768)` → `vector(1024)`。
  pgvector 跨维度不能 cast → **DROP COLUMN + ADD COLUMN**，**已有 chunk 向量丢失、知识库需重灌**
  （当前仅 dev/seed 数据，符合预期）。downgrade 回 768（同样 DROP+ADD）。0005 的
  `knowledge_documents.embedding` 已弃用（0006 起不写入），**不动**。
- **config**：`llm_embedding_dim` 默认 768 → **1024**（本地哈希降级也按 1024 生成，与列一致）
- **无新增运行时依赖**（httpx 仍 dev extra；硅基流动走既有 OpenAIEmbeddingGateway）

## 3. 实现清单
- [x] `migrations/versions/0007_embedding_1024.py`（DROP+ADD vector(1024)；downgrade 回 768）
- [x] `app/config.py`：默认维 768→1024 + 注释指向 0007
- [x] `tests/migrations/test_aiqa_schema.py`：新增 `_vector_dimension` helper
  （`format_type()` 解析 `vector(N)`）+ 断言 chunk.embedding 维度 = 1024
- [ ] 用户 WSL：测试库 upgrade head（fixture 自动）+ `jianli_dev` upgrade head + 重灌知识库
- [ ] 用户 WSL：配 `JIANLI_LLM_EMBEDDING_BASE_URL/API_KEY/MODEL` 后重跑 `test_rag_eval.py`
  → 对比哈希 vs 真实 embedding 命中率（面试亮点数据）

## 4. 配置（用户运行时环境变量，key 不落文件）
```
export JIANLI_LLM_EMBEDDING_BASE_URL="https://api.siliconflow.cn/v1"
export JIANLI_LLM_EMBEDDING_API_KEY="sk-xxx"          # 用户 SiliconFlow key
export JIANLI_LLM_EMBEDDING_MODEL="BAAI/bge-m3"
# 不设 JIANLI_LLM_EMBEDDING_DIM（默认 1024 已对齐列）
```

## 5. 验收
- [ ] 沙箱门禁：ruff ✅ / mypy ✅ / alembic head=0007 ✅ / DB-free ✅
- [ ] WSL：迁移测试 5 passed（含维度断言）+ 评测重跑有数字
- [ ] 知识库重灌后 `streamAnswer` 引用正常（真实向量检索）

## 6. 面试价值
"embedding 从本地哈希升级为 BGE-M3 语义向量（硅基流动，1024 维），
评测集对比：哈希命中率 x% → 语义命中率 y%，检索质量可量化提升。"
