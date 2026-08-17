# TASK-CONTENT-RESUME-001 提交简历源文件 resume.md

> 将 AI 问答 RAG 使用的简历源文件 `apps/web/public/resume.md`（[姓名已脱敏]真实简历，45 行）正式入库，作为简历域知识库的源文本。属内容交付，不改变任何问答逻辑。

## 任务类型
- content  # 内容 / 知识库源文本交付

## 关联任务
- 简历域事实 grounding 修复见 `tasks/TASK-AIQA-GROUNDING-001.md`（已关闭，verified_commit=eba0103）；本任务提交其引用的源文本 `resume.md`，使其随仓库版本固定，便于复跑事实一致率评测。

## 目标
将 `apps/web/public/resume.md` 入库。该文件为简历问答 RAG 的检索语料源头，含教育背景、项目经历（含 Litchi Copilot 荔枝智能农技协同平台）、技能等真实信息。

## 非目标（明确排除）
- 不改动问答逻辑、persona、retrieval、grounding 事实卡
- 不改动其他内容文件（content.py 等）
- 不新增依赖

## 允许修改路径
- `apps/web/public/resume.md`
- 本任务单 `tasks/TASK-CONTENT-RESUME-001.md`

## change_budget
- max_files: 2
- 生产代码行数：0（纯内容/文档）

## 验收标准
- `apps/web/public/resume.md` 已入库且内容完整（45 行，含教育/项目/技能）
- 不引入未跟踪的真实交付文件

## 状态
- status: in_progress
- 创建 commit: （待提交）
- verified_commit: （待回填）
