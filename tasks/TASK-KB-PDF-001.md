# TASK-KB-PDF-001 知识库 PDF 支持 + 前端管理页（合并任务）

> **状态（2026-08-13，✅ 已关闭 Closed，用户验证通过并授权关闭）**：PDF 上传（pypdf）+ 前端管理页 + 页面一 PDF 展示全部实现并验证，2026-08-13 用户授权关闭。
> **依赖**：M6 已关闭（upload/知识库检索就绪）；TASK-FE-AIQA-001 已关闭（前端问答页就绪）

## 1. 任务类型
- implementation（后端 aiqa + 前端 web，合并同域主线）

## 2. 精确规范引用
- OpenAPI v0.2：`uploadKnowledgeDocuments`（multipart files，202）、`listKnowledgeDocuments`、`deleteKnowledgeDocument`（204）
- 领域模型 v1.1.5 §6.14：`parse_mode` 枚举 text/ocr/native；pdf 类型；删除即禁检索
- 既有实现：`apps/api/app/aiqa/service.py` upload（`_SUPPORTED_TYPES={"md","txt"}`，pdf 现 failed"not supported"）；`apps/web/main.tsx`（Page type/HistoryRail/TopBar/api()/csrfCookie）

## 3. 目标
**后端**：`uploadKnowledgeDocuments` 支持 **pdf**（`pypdf` 提取文本 → `type=pdf, parse_mode=native` → checksum 去重 → embedding → indexed；解析失败/空文本 → failed 带原因）；md/txt 照旧（parse_mode=text）；docx 保持 failed。
**前端**：
- 管理后台页（Page='admin'）：owner_admin 登录 → PDF/md/txt 多文件上传 → 文档列表（type/size/status/failure_reason + 删除）；复用 `api()`/`csrfCookie()`，multipart 用 FormData
- 页面一 PDF 简历展示：`apps/web/public/resume.pdf`（用户放置素材），ResumeView 以 `<embed>` 展示
- HistoryRail/TopBar 加"知识库"入口

## 4. 非目标
- 扫描件 OCR（`parse_mode=ocr` 枚举保留不实现）；docx 解析
- 历史会话 UI；管理页权限细化（owner_admin 即可）
- PDF 下载端点（页面一 PDF 走 vite public 静态文件，不经后端）

## 5. 已批准的 DB / API / 依赖变更（用户 2026-08-13 批准）
- **依赖**：`pypdf`（纯 Python PDF 文本提取，加入 `pyproject.toml` dependencies）
- DB：无变更；API：无契约变更（复用既有 3 个 knowledge operation；页面一 PDF 为 vite public 静态资源，非后端 API）

## 6. 允许修改路径（change_budget：max_files=9）
- `apps/api/pyproject.toml`（+pypdf）
- `apps/api/app/aiqa/service.py`（upload 支持 pdf）
- `apps/api/tests/aiqa/test_knowledge.py`（+PDF 上传/检索用例，用内嵌最小合法 PDF 生成器）
- `apps/web/main.tsx`（+AdminView、Page='admin'、入口、ResumeView PDF embed）
- `apps/web/styles.css`（管理页样式）
- `apps/web/public/resume.pdf`（占位说明文件或由用户放置；不提交大文件，登记素材路径）
- `tests/web-shell/shell.test.ts`（仅新增锚点断言）
- `PROJECT_STATE.md` / `tasks/TASK-KB-PDF-001.md`

## 7. 禁止修改路径
- 后端契约/迁移/鉴权主体；既有预约/问答流程；`docs/` 已批准规范

## 8. 验收标准
- 后端：ruff ✅ + mypy ✅ + DB-free ✅；真实集成（WSL）新增 PDF 用例 passed（上传→indexed→检索命中）
- 前端：typecheck ✅ + vitest ✅ + build ✅；手动（WSL）：admin 页登录上传 PDF/md → 列表显示 → 删除生效；resume.pdf 放 public 后页面一显示
- `python-multipart`/`pypdf` 均为已批准依赖

## 9. 强制停止条件
- 未列明变更（新依赖/改契约/改鉴权）→ 停止报告

## 10. 交付证据（2026-08-13 已回填；✅ 任务已关闭）
- 实现 commit：`cb4d16e`（7 files / +232：pyproject+service+test_knowledge PDF 用例 + main.tsx AdminView/styles/入口 + shell.test 锚点）+ `5525cb6`（修复：不支持类型用例 notes.pdf→notes.docx，PDF 已支持的语义演进）
- 后端门禁：ruff ✅ + mypy 43 files ✅ + DB-free 14 passed ✅
- **用户 WSL 验证（2026-08-13）**：`pytest tests/aiqa/test_knowledge.py` **6 passed in 10.48s** ✅（含 PDF indexed/去重/检索命中 + 损坏 PDF failed）；前端 `pnpm run typecheck` ✅ + `pnpm test` 1 passed ✅ + `pnpm run build` ✅（JS 234.99kB / gzip 72.65kB）；`verified_commit=5525cb6`
- 手动验证（管理页上传 PDF 简历 → indexed → 问答命中引用）：用户后续自行操作（素材 `apps/web/public/resume.pdf`）
- 环境说明：前端门禁在用户 WSL 执行（沙箱 Windows 缺 win32 平台包，pnpm 平台隔离——node_modules 被用户 WSL 重装为 linux 平台）

## 11. 关联
- 前置：M6（upload API 就绪）、TASK-FE-AIQA-001（前端问答就绪）
- 后续：OCR（扫描件）、docx、历史会话 UI、上线素材（真实简历 PDF）
