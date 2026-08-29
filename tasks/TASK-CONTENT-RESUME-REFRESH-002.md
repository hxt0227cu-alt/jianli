# TASK-CONTENT-RESUME-REFRESH-002 新简历 PDF 与文字源更新

## 任务类型
- content
- test

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`140b249`

## 精确规范引用
- `AGENTS.md §9` Fact Source Routing
- `TC-WEB-RESUME`（`tests/web-shell/shell.test.ts`）
- `tasks/TASK-CONTENT-RESUME-001.md`

## 需求来源
- 用户提供 `C:\Users\hxt02\Desktop\resume.pdf`，要求更新网站新简历。

## 目标
- 用用户提供的一页新 PDF 替换网站 `/resume.pdf`。
- 将 `resume.md` 更新为新简历的可检索文字镜像。
- 对源 PDF 和站内副本进行哈希、页数、文本与视觉渲染验证。

## 非目标
- 不修改 canonical 20 篇 RAG 语料、事实题库或既有源码审计边界。
- 不把简历中的压缩表达扩张为“生产已上线”“评测全部满分”等实现事实。
- 不实施毛玻璃 UI；UI 视觉升级另立任务。
- 不修改 API、DB、依赖、权限、Prompt、检索算法或阈值。

## 允许修改路径
- `tasks/TASK-CONTENT-RESUME-REFRESH-002.md`
- `apps/web/public/resume.pdf`
- `apps/web/public/resume.md`

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估
- behavior_change：false（内容素材替换，不改变交互或契约）
- affected_specs：none
- spec_sync：not_required

## 验收
- 网站 PDF 与用户源 PDF SHA-256 完全一致，均为 1 页。
- PDF 重新渲染无裁切、重叠、黑块或缺字。
- `resume.md` 覆盖个人简介、实习、三个项目、荣誉证书与技能，且不保留旧日期/旧描述。
- `npm test`、`npm run typecheck`、`npm run build` 全绿。

## 变更预算
- max_files：3
- expected_content_lines：80

## 回滚
- Git revert 本任务提交。

## 交付证据
- commit / PR：待回填
- 修改文件：待回填
- 测试结果：待回填
- PDF 验证：待回填
- DB 迁移：无
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- verified_commit：待回填

