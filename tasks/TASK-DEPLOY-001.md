# TASK-DEPLOY-001 部署素材（简历）+ LLM 配置支持（DeepSeek V4 Flash）

> **状态**：Open（2026-08-13 建；用户提供简历 `14.docx`，选定 DeepSeek V4 Flash）
> **依赖**：M6 / TASK-FE-AIQA-001 / TASK-KB-PDF-001 均已关闭

## 1. 任务类型
- implementation + 素材落地（配置支持，非 API 契约变更）

## 2. 目标
1. **简历素材（完整 PDF，优先）**：用用户提供的 `14.pdf` 原版（284KB，含照片/卡片/完整排版）作为产品素材
   - `apps/web/public/resume.pdf`（页面一展示；用户原版——**完整真实排版，非向量化损失**）
   - 知识库上传也用同一份 PDF（pypdf 提取 → `type=pdf, parse_mode=native` → embedding；优于 md 抽取，避免文本结构损失）
2. **LLM 配置支持（DeepSeek V4 Flash）**：`base_url=https://api.deepseek.com`、`model=deepseek-v4-flash`
   - **DeepSeek 无 /embeddings 端点** → embedding 配置从 chat 拆分为独立字段
     `llm_embedding_base_url/api_key/model`（env `JIANLI_LLM_EMBEDDING_*`），不配则本地哈希降级（知识库照常工作）
   - API key 仅存运行时环境变量，不写入任何文件

> 修订记录（2026-08-13 晚）：用户首版提供 `14.docx`，我用 python-docx + 正则提取文本并用 reportlab 生成简历 PDF（简化排版）。用户随后提供**真版 PDF `14.pdf`**，**要求用完整 PDF 而非向量化提取成 md**——删除简化版 `resume.md`，页面一改用真版 PDF；知识库建议直接上传 PDF（pypdf 提取更准）。

## 3. 允许修改路径（change_budget：max_files=6）
- `apps/web/public/resume.md`（新建，素材）
- `apps/web/public/resume.pdf`（新建，素材）
- `apps/api/app/config.py`（+3 embedding 配置字段 + env 映射）
- `apps/api/app/aiqa/runtime.py`（embedding gateway 改用独立配置）
- `PROJECT_STATE.md` / `tasks/TASK-DEPLOY-001.md`

## 4. 禁止修改路径
- API 契约 / 迁移 / 鉴权；既有业务逻辑（仅配置能力扩展）

## 5. 验收标准
- ruff ✅ + mypy ✅ + DB-free 15 passed ✅（含 test_config）
- 用户 WSL：设 DeepSeek env 后 streamAnswer 走真实模型；知识库上传（未配 embedding）走本地哈希降级正常

## 6. 交付证据（关闭前填写）
- *实现后回填*

## 7. 关联
- 后续：真实简历 PDF 由管理页上传知识库 → 问答命中；上线准备（域名/备案/SMTP）
