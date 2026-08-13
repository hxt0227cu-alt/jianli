# TASK-M6-DB AI 问答域迁移（人工审批建表）

> **任务类型**：migration（**DB 迁移铁律：建表须用户人工审批**；本任务单即审批材料，schema 见 §7）
> **状态（2026-08-13）**：✅ 用户已批准 schema（含 RecommendedQuestionCache 不纳入）；✅ 迁移 `0004_aiqa_schema.py` + 迁移测试已编写；⏳ 待 WSL 真实 PG 验证；**不执行生产迁移**（执行另行批准）
> **前置**：领域模型 v1.1.5 已 approved（§6.13/6.14 已建模 4 张表）→ 本迁移只是把已批准建模落地为 DDL

## 1. 基线版本与基线 commit
- baseline：领域模型 1.1.5 / SRS 1.3 / OpenAPI 0.2 / 架构 0.2 / 安全 0.1（均 approved）；development_gate 全放行
- 基线 commit：`ba468c9`（M6 首轮治理回填，HEAD）

## 2. 精确规范引用（只读这些章节）
- 领域模型 v1.1.5 **§6.13 Conversation/Message（含留存）**、**§6.14 KnowledgeDocument/KnowledgeIndexVersion**、**§9 数据留存与清理**（Conversation 180 天 `purge_after`；KnowledgeDocument 删除即禁检索 `retrieval_disabled_at` + 索引热切换）
- OpenAPI v0.2 字段对齐（会话三件套 / 知识库三件套 operation 的字段与枚举）：`Conversation{id,created_at,updated_at}`、`Message{id,role enum(user,assistant),content,is_offtopic,created_at}`
- 既有迁移风格：`migrations/versions/0003_outbox_audit_schema.py`（枚举 `postgresql.ENUM` + `checkfirst`；`uq_`/`ix_`/`fk_` 命名；downgrade 逆序 + 枚举 drop）

## 3. 目标
把领域模型 §6.13/6.14 已建模的 4 张表（`conversations` / `conversation_messages` / `knowledge_documents` / `knowledge_index_versions`）+ 5 个枚举 + 索引/约束落地为**可逆迁移 0004**，使 M6 二轮（会话持久化）与三轮（知识库摄取）具备建表前提。**不执行生产迁移**（执行须用户单独批准）。

## 4. 非目标（明确排除）
- **RecommendedQuestionCache（领域模型 §6.16）不纳入本次**：属 P1-2 推荐问题缓存优化，非二/三轮阻塞项；如后续需要另开小迁移（避免本次审批范围膨胀）
- 不实现任何业务代码/端点（二/三轮在 TASK-M6-AI-QA 后续轮次实现）
- 不改动既有 0001–0003 任何表/枚举/索引；不动加密/鉴权/预约/通知 schema
- 不引入向量扩展（pgvector 等）——检索实现待三轮单独评估（属依赖变更，另行审批）

## 5. 允许修改路径（change_budget：max_files=4）
- `apps/api/migrations/versions/0004_aiqa_schema.py`（新建，唯一生产产物）
- `apps/api/tests/migrations/` 既有迁移测试套件适配（若套件按表集合断言，则追加 0004 子集断言；**不改动既有冻结断言**）
- `tasks/TASK-M6-DB.md`（本任务单，交付证据回填）
- `PROJECT_STATE.md`（仅当前任务段）
> 注：0004 落地后，M6 二轮/三轮实现（`app/aiqa/` 扩展 + 端点）**另开实现轮次**，不在本任务。

## 6. 禁止修改路径
- `apps/api/migrations/versions/0001_*` / `0002_*` / `0003_*`（既有 schema 冻结）
- `apps/api/app/**`（本任务不写业务代码）
- 已批准枚举值清单之外的任何枚举/字段语义

## 7. Schema 设计（**审批核心**，全部出自领域模型 §6.13/6.14）

### 7.1 新枚举（5 个，命名对齐 `notification_event_type` 风格）
| 枚举名 | 成员 |
|---|---|
| `message_role` | user, assistant |
| `knowledge_document_type` | md, pdf, docx, txt |
| `knowledge_document_status` | indexing, indexed, failed |
| `knowledge_document_parse_mode` | text, ocr, native |
| `knowledge_index_status` | building, ready, rolled_back |

### 7.2 `conversations`（领域模型 §6.13；留存 §9：180 天）
| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK→users.id，NOT NULL |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| deleted_at | timestamptz | NULL |
| purge_after | timestamptz | NULL（180 天硬删） |
- 索引：`ix_conversations_user`（user_id, updated_at DESC）——支持"列出当前用户会话"；`ix_conversations_purge`（purge_after）**部分索引 WHERE purge_after IS NOT NULL**——支持清理任务。

### 7.3 `conversation_messages`（§6.13）
| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| conv_id | uuid | FK→conversations.id，NOT NULL（ON DELETE CASCADE：会话硬删连带消息） |
| role | message_role | NOT NULL |
| content | text | NOT NULL |
| is_offtopic | bool | NOT NULL（默认 false） |
| created_at | timestamptz | NOT NULL |
- 索引：`ix_conversation_messages_conv`（conv_id, created_at）——按会话取消息历史。

### 7.4 `knowledge_documents`（§6.14）
| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| type | knowledge_document_type | NOT NULL |
| size | int | NOT NULL |
| content_checksum | text | NOT NULL（SHA-256 解析文本，去重） |
| storage_key | text | NOT NULL（对象存储路径） |
| status | knowledge_document_status | NOT NULL |
| parse_mode | knowledge_document_parse_mode | NULL |
| failure_reason | text | NULL |
| retrieval_disabled_at | timestamptz | NULL（删除即禁检索） |
| active_index_version_id | uuid | FK→knowledge_index_versions.id，**NULL**（当前服务索引；循环 FK，见 7.6 后置） |
| version | int | NOT NULL（默认 1） |
| created_at | timestamptz | NOT NULL |
- 唯一约束：`uq_knowledge_documents_storage_key`（storage_key 全表唯一——对象键天然唯一）
- **部分唯一索引 `uq_knowledge_documents_active_checksum`**（content_checksum）**WHERE retrieval_disabled_at IS NULL**——"相同文件去重"：仅活跃文档互斥；删除（禁检索）后可重新上传同名同内容文件
- 索引：`ix_knowledge_documents_created_at`（created_at DESC）——管理列表

### 7.5 `knowledge_index_versions`（§6.14）
| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| doc_id | uuid | FK→knowledge_documents.id，NOT NULL（ON DELETE CASCADE） |
| version | int | NOT NULL |
| status | knowledge_index_status | NOT NULL |
| indexed_at | timestamptz | NOT NULL |
- 唯一约束：`uq_knowledge_index_versions_doc_version`（doc_id, version）——版本递增不重复
- 索引：`ix_knowledge_index_versions_doc`（doc_id, status）——按文档取索引/切换

### 7.6 循环 FK 处理（关键决策）
`knowledge_documents.active_index_version_id → knowledge_index_versions.id` 与 `knowledge_index_versions.doc_id → knowledge_documents.id` 互为外键。
**做法**：先建 `knowledge_documents`（`active_index_version_id` 仅 uuid NULL、暂不声明 FK）→ 建 `knowledge_index_versions`（含 doc_id FK）→ `op.create_foreign_key("fk_knowledge_documents_active_index_version_id", ...)` 后置补上。downgrade 逆序：先删该 FK 再删两表。

### 7.7 可逆性
`upgrade`：5 枚举 → 4 表 → 后置 FK → 索引/约束；`downgrade` 完全逆序（删 FK/索引/约束 → 表 → 枚举）。空库 `up → down base → up` 必须通过（迁移测试套件执行）。

## 8. 已批准的 DB / API / 依赖变更（本任务自身即 DB 变更，逐项列明）
- DB：**仅新增** 4 表 + 5 枚举 + 上列索引/约束；不改既有任何对象；不引入 pgvector
- API：无（纯 schema）
- 依赖：无

## 9. 验收标准
- `alembic upgrade head` 从 0001 起全链通过；`downgrade base` 逆序全部撤销；空库 `up→down base→up` 通过
- 迁移测试套件（真实 PostgreSQL）覆盖：4 表列/约束/FK/部分唯一索引存在性 + 去重拒绝路径（活跃 checksum 重复 → 报错；删除后重传 → 允许）+ 会话级联删除
- ruff/mypy 不涉及（纯迁移文件按套件既有口径）

## 10. 强制停止条件
- 出现未列明变更（改既有表/枚举、加 pgvector、动业务代码）→ 立即停止报告
- 超出 change_budget → 拆任务

## 11. 回滚方法
- 迁移未执行：`alembic downgrade base`（可逆）；已执行：逆序 `downgrade -1`

## 12. 交付证据（2026-08-13 已回填；任务待用户授权关闭）
- **用户批准**：2026-08-13（schema 4 表 + 5 枚举 + 索引/约束；RecommendedQuestionCache 不纳入）
- **实现 commit**：`d2f4e42`（迁移 + 测试）+ `57a7481`（修复：FK 显式命名 + 形状断言 bool/int 归一化；WSL 首跑 3/2，修复后全绿）
- 本地门禁：ruff All checks passed ✅ + mypy 0 error（40 source files）✅ + `alembic heads` = `0004_aiqa_schema (head)` ✅ + py_compile ✅
- **真实 PostgreSQL 迁移测试（用户 WSL，2026-08-13）**：`PYTHONPATH=. pytest tests/migrations/test_aiqa_schema.py -v` **5 passed in 1.32s** ✅（up→down→up 可逆 + 4 表/5 枚举/索引/FK 形状 + 去重后重传 + 枚举拒绝 + 级联删除）；`verified_commit=57a7481`
- 生产迁移执行：**未执行，另行批准**（本地 dev 库 `jianli_dev` 升级 head 亦须用户授权）

## 13. 关联
- **前置任务**：领域模型 v1.1.5 已 approved（§6.13/6.14 建模即批准依据）
- **后续**：本迁移批准 → 写 0004 + 迁移测试 → 用户批准执行 → M6 二轮（会话持久化三件套 + streamAnswer 落库）/ 三轮（知识库摄取三件套 + 检索接入）在 TASK-M6-AI-QA 后续轮次实现
- **待用户确认**：① 7.2–7.5 schema 设计；② §4 RecommendedQuestionCache 不纳入本次；③ 生产迁移执行将在迁移测试通过后单独申请批准
