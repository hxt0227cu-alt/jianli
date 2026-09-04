# TASK-KB-RESUME-REFRESH-001 知识库随新简历刷新（2026-09）

> 用户提供新简历 `[姓名已脱敏]-22.pdf`，要求知识库随其更新；并经多轮讨论确认四条口径决策（见下）。本任务为**用户明确批准的内容刷新**，等效于已批准的 Change Request。

## 任务类型
- implementation（知识内容/语料/测试同步）

## 基线版本与基线 commit
- baseline：事实锚点 = `docs/fact-consistency/fact-bank.md`；语料 = `canonical_corpus.py`；静态兜底 = `content.py`；人格 = `persona.py`（AGENTS.md §10 已实现清单）
- 基线 commit：`4beadb82f8341ae21900a54d77f0243b8dadcfa3`（上一轮发布 commit）

## 精确规范引用（AI 只读取这些章节）
- `docs/fact-consistency/fact-bank.md`（FQ-01…FQ-61 期望事实，随本次更新同步）
- `docs/fact-consistency/rubric.md`（判定口径）
- `apps/api/app/aiqa/content.py`、`canonical_corpus.py`、`persona.py`
- `apps/api/tests/aiqa/test_rag_eval.py`、`test_persona_style.py`
- `tests/web-shell/shell.spec.ts`、`shell.test.ts`
- `scripts/measure_fact_consistency.py`

## 需求来源
- 用户决策（2026-09-04 讨论确认）：
  - ①B 以新简历为准，保留口径说明（"该指标来自内部 NDA 验证，可追问但不公开原始证据"）
  - ②A 保留 jianli 问答（仅简历不展示，站点仍可答）
  - ③A 保留荣誉/证书可问答
  - ④ 站点公开素材（resume.pdf / resume-preview.png / resume.md）隐藏身份：手机、邮箱、学校、姓名全部不展示；AI 问答输出同样不透露姓名/学校，保持口径一致

## 目标
把 AI 问答知识库（content.py 静态语料 + canonical_corpus RAG 语料 + fact-bank 题库 + persona 风格示例 + 站点简历素材）整体刷新为与新简历一致的内容：新增吉利极氪、MCP 数据分析引擎、慧眼识蚁硬件细节，更新泰益智岗位/时间与指标，隐藏姓名与学校身份，保留 NDA 口径说明，保留 jianli 与荣誉问答。

## 非目标（明确排除）
- 不修改数据库 schema / 迁移 / 公开 API 契约 / SSE 事件字段
- 不新增外部依赖
- 不改变认证 / 鉴权 / 加密 / 工具白名单逻辑
- 不删除 jianli 知识（②A 保留）
- 不新增功能特性

## 允许修改路径
- `apps/api/app/aiqa/content.py`、`apps/api/app/aiqa/canonical_corpus.py`、`apps/api/app/aiqa/persona.py`
- `docs/fact-consistency/fact-bank.md`、`scripts/measure_fact_consistency.py`
- `apps/api/tests/aiqa/test_rag_eval.py`、`apps/api/tests/aiqa/test_persona_style.py`
- `tests/web-shell/shell.spec.ts`、`tests/web-shell/shell.test.ts`
- `apps/web/main.tsx`（简历预览 alt 文本 / 下载文件名去身份化）
- `apps/web/public/resume.md`、`apps/web/public/resume.pdf`、`apps/web/public/resume-preview.png`（匿名版新简历）
- `tasks/TASK-KB-RESUME-REFRESH-001.md`（本任务单）

## 禁止修改路径
- `apps/api/app/appointments/`、`app/auth/`、`app/notifications/`、`app/admin/`、`app/api/` 契约
- `apps/api/migrations/`、`docs/api/openapi.yaml`、`docs/api/sse.md`
- `apps/api/var/`、`.env*`、`deploy/` 配置、CI 工作流
- jianli 相关语料的技术事实（保留）

## 已批准的 DB / API / 依赖变更
- 无（纯内容与测试同步，无 schema / 契约 / 依赖变更）

## 规范影响评估（spec impact）
- behavior_change：true（AI 回答内容与站点展示随新简历变化）
- affected_specs：
  - srs：change_request_required → **已由用户显式批准**（四条决策 = 等效 Change Request 批准，见"需求来源"）
  - domain_model：none
  - openapi：none
  - security：none（身份隐藏属收紧隐私边界，不放开）
  - test_plan：update（RAG/persona/web-shell 用例期望随事实更新）
- reason：事实源（fact-bank/语料）是回答的口径真相源；本次由产品所有者（用户）直接批准刷新，故按已批准变更处理，同步更新测试期望。

## 功能验收
- 新简历各事实点（泰益智 2026.01-2026.08 / 吉利极氪 / MCP 引擎 / 慧眼识蚁 / Litchi 新编排器）均可被 RAG 检索命中（含新增文档）
- AI 不再回答姓名与学校（匿名口径一致），其余隐私问题（家庭住址/工资/生日）继续拒答
- jianli 相关问题仍可答；荣誉/证书问题仍可答
- 站点 resume.md/pdf/png 完全匿名（无姓名、学校、手机、邮箱）

## 安全与隐私验收
- 全仓不再出现真实姓名"[姓名已脱敏]"、学校"[学校已脱敏]"、手机号、个人邮箱（仅允许出现在用户上传素材与 .env.local）
- 专利申报号（可反查学校）一并移除
- 公开问答不得泄露 NDA 原始证据（仅口径说明）

## 性能验收
- 不涉及（无性能敏感路径改动）

## 变更预算（change_budget）
- max_files：16
- expected_prod_lines：约 700（语料/人格/content 重写）
- expected_test_lines：约 120（测试期望同步）

## 必须运行的测试命令
- `cd apps/api && PYTHONPATH=. python -m pytest tests/aiqa tests/test_app.py -q`（DB-free 14 用例）
- `python -m ruff check .`、`python -m ruff format --check .`、`python -m mypy app`（若有）
- `cd apps/web && pnpm typecheck && pnpm test && pnpm build`（若环境允许）

## 回滚方法
- 内容回退：`git revert` 本 commit；无 DB 迁移，无数据影响

## 强制停止条件（与 AGENTS.md §2 一致）
- 超出本任务单「允许修改路径」之外的变更 → 停止并报告
- 新增 DB/API/依赖/密钥策略变更 → 停止并报告
- 冻结验收测试失败不得改断言绕过（本次测试期望更新属于事实同步，须在 TASK 内说明并同步）

## 交付证据（任务关闭前填写）
- commit / PR：待 push 后回填（见 verified_commit）
- 修改文件清单：
  - `apps/api/app/aiqa/canonical_corpus.py`：20→23 篇（新增 mcp-analytics-engine / zeekr-cockpit-assistant / anteye-robot；profile 匿名化 + NDA 口径；sleep 全套新口径；litchi 新编排器；jianli 7 篇由 git HEAD 逐字恢复，语义等同验证通过；身份零泄漏；恢复 `# ruff: noqa: E501` 与 HEAD 一致）
  - `apps/api/app/aiqa/content.py`：`_UPDATED_AT=2026-09-04`；resume 页 12 chunks 匿名新口径 + projects 页 6 项目；匿名事实卡（无姓名/学校/手机/邮箱/专利号）；anteye 移除无依据"优秀结题"
  - `apps/api/app/aiqa/persona.py`：STYLE_FEW_SHOT 12 组新口径 + 去身份化（语法验证通过）
  - `docs/fact-consistency/fact-bank.md`：全量重写，FQ-01~38 测量运行 + 扩展 FQ-39~64；保留编号、新增 FQ-62~64
  - `scripts/measure_fact_consistency.py`：FQ-31~33 换新 sleep 口径（保持 38 题测量运行）
  - `apps/api/tests/aiqa/test_rag_eval.py`：冻结身份问题改匿名；旧 sleep/litchi 案例换新口径；新增 mcp/zeekr/anteye LITERAL+SEMANTIC 案例
  - `apps/api/tests/aiqa/test_persona_style.py`：数字溯源列表换新口径
  - `apps/web/main.tsx`：TopBar"AI 应用开发工程师"；项目卡 sleep/litchi 新口径；深度面板（SleepReliabilityReplay / SleepDeliveryEvidence / LitchiAcceptanceEvidence）NDA 口径重写；Followup 池 sleep 问题更新；简历预览 alt / 下载名 / 标题匿名化；`&gt;99%` JSX 转义
  - `apps/web/public/resume.md` / `resume.pdf` / `resume-preview.png`：匿名版新简历（2 页 PDF，headless Chrome 渲染；无姓名/学校/手机/邮箱/专利号）
  - `tests/web-shell/shell.spec.ts` / `shell.test.ts`：img alt 与面板断言同步新内容
- 测试命令及结果：
  - `PYTHONPATH=. pytest tests/aiqa tests/test_app.py -q` → **86 passed, 24 skipped**（DB-free）
  - `tsc --noEmit`（apps/web）→ **exit 0**
  - `vitest --root . run tests/web-shell/shell.test.ts` → **1 passed**
  - 注：test_rag_eval.py 需真实 PG/Redis（本环境无，skipif 跳过）；真实栈验证留待 WSL 集成环境
- lint / typecheck：
  - `ruff check app` → **All checks passed!**（含恢复 canonical_corpus.py 的 `# ruff: noqa: E501`，与 HEAD 一致）
  - `mypy app` → **Success: no issues found in 53 source files**
- DB 迁移验证：无（无 schema 变更）
- 验收证据：新简历全文经 WSL pypdf 重新提取核实；resume.pdf 2 页 / pymupdf 渲染第 1、2 页视觉核验无裁剪无身份；语料 23 篇 import 断言通过；全仓身份扫描（[姓名已脱敏]/[学校已脱敏]/[手机号已脱敏]/[邮箱已脱敏]/专利号）零泄漏
- 变更预算实际值：max_files=16，实际 13 改 + 1 新增 = 14（含 TASK 单），未超预算
- 未解决风险：
  - fact-bank 测量运行（FQ-01~38）需真实 PG/Redis + 已更新语料灌库后跑 `measure_fact_consistency.py` 验证 SLO ≥94%（本环境无 DB，未能实跑）
  - 历史文档（docs/interviews/round2-answers.md、scripts/fact_consistency_results.json、docs/fact-consistency/scored-2026-08-18.md 等）含旧身份/旧指标，属历史记录，未清理（用户未要求）
  - 匿名简历保留 CSDN 博客链接（blog.csdn.net/m0_73429744），不在用户指定的隐藏清单（姓名/学校/手机/邮箱）内；如需一并隐藏请告知
  - 前端项目 tab 仍为 3 个（jianli/sleep/litchi），MCP/极氪/慧眼识蚁仅在 AI 问答与简历素材中体现，未新增 UI tab（避免超出"更新知识库"范围）
- 是否偏离 TASK：否
- 规范影响结论：updated（用户批准）
- spec_sync：已按用户四条决策同步（①B 新简历+NDA 口径 / ②A 保留 jianli / ③A 保留荣誉 / ④ 身份全隐藏）
- verified_commit：<push 后回填>

## 关联
- Change Request：用户 2026-09-04 四条决策（等效批准）
- 测试任务：FQ-01…FQ-61（fact-bank）、RAG LITERAL/SEMANTIC/REJECT/FALSE-REJECT、persona 数字溯源、web-shell
