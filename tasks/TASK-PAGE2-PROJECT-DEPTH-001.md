# TASK-PAGE2-PROJECT-DEPTH-001 三项目展示深度对齐

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`f689ecd91a2701efc80b40f3b5e033a84903f25a`

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` §3 U2
- `docs/requirements/use-cases.md` UC-02
- `docs/fact-consistency/fact-bank.md` FQ-27～FQ-33、FQ-39～FQ-50、FQ-59～FQ-61
- `apps/api/app/aiqa/content.py` Sleep / Litchi canonical facts
- 现有 `tests/web-shell/shell.test.ts` 冻结回归

## 需求来源
- 用户 2026-08-29 基于项目页截图澄清：Jianli 有核心价值、Agent Lab、评测中心三个大板块，而 Sleep/Litchi 只有核心价值板块，导致后两项呈现为未完成。

## 目标
在不夸大事实的前提下，为 Sleep 与 Litchi 分别补齐第二、第三个大型展示板块，使三个项目均形成“价值定位 → 工程过程 → 验证与边界”的完整叙事。

## 非目标（明确排除）
- 不为 Sleep/Litchi 伪造可交互 Agent Lab、远端 CI、生产部署或未验证指标。
- 不修改问答、RAG、知识库、Prompt、推荐问题或评测阈值。
- 不修改 API、数据库、迁移、权限、依赖与部署。
- 不公开 NDA 源码、日志、内部标识、绝对路径或个人敏感信息。

## 允许修改路径
- `tasks/TASK-PAGE2-PROJECT-DEPTH-001.md`
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tests/web-shell/shell.test.ts`（仅新增板块存在性与事实边界断言，不得修改或放宽既有断言）

## 禁止修改路径
- `apps/api/**`
- `docs/**`
- 数据库迁移、依赖锁文件、权限与密钥配置

## 已批准的 DB / API / 依赖变更
- 无。

## 规范影响评估（spec impact，每个代码 TASK 必填）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：仅在 U2 已批准的项目展示页内补齐现有项目证据与呈现层级，不改变交互契约、业务行为或事实真相源。

## 功能验收
- Jianli 保持“核心价值 + Agent Lab + 版本化评测”三个大板块。
- Sleep 展示“核心价值 + 可靠性事件复盘 + 交付证据账本”三个大板块。
- Litchi 展示“核心价值 + Agent/RAG 实现链路 + 毕设验收与边界”三个大板块。
- Sleep/Litchi 新增板块使用既有暖色主题，内容密度、字号与占位高度不弱于 Jianli 对应板块。
- 新增事实均可从 canonical content / fact bank 追溯，明确区分已实现、实验模板、失败与未落地项。

## 安全与隐私验收
- 不展示 NDA 源码、日志、内部标识、绝对路径或个人敏感信息。
- 不把模拟 ACK、未提交报告、实验模板或失败部署描述成生产运行证据。

## 性能验收
- 不新增网络请求、图片、字体、JavaScript 依赖或持续动画。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：320
- expected_test_lines：35

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`
- `git diff --check`
- 浏览器 1440×1000 逐项检查 Jianli / Sleep / Litchi 的三个大板块与控制台。

## 回滚方法
- 回退本任务提交；无数据迁移或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要新增依赖、API/DB/权限变化或修改 canonical 事实源时停止报告。
- 事实无法从既有语料核验、超过 4 个文件、超出预算或冻结测试失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`9cd77bf4cc7bda4db8a8050f40cd49f92e74ccf7`
- 修改文件清单：`apps/web/main.tsx`、`apps/web/styles.css`、`tests/web-shell/shell.test.ts`、`tasks/TASK-PAGE2-PROJECT-DEPTH-001.md`
- 测试命令及结果：`npm test` → 1 test / 1 file passed；`npm run build` → 1793 modules transformed，production build 成功
- lint / typecheck：`npm run typecheck` → 0 error；`git diff --check` → 0 error
- DB 迁移验证：无
- 验收证据：Codex 内置浏览器 1440×1000 实测：Sleep 为 `project-card khaki`（783px）+ 可靠性复盘（482px）+ 交付账本（450px）三个板块；Litchi 为 `project-card sun`（802px）+ 双链路工程图（611px）+ 毕设验收板（643px）三个板块；主内容宽 705px，无横向溢出，暖色主题与文字层次清晰，warning/error 控制台记录为 0。
- 变更预算实际值：4 / 4 files；生产代码/样式 138 增 / 1 删≤320；测试 17 行≤35
- 未解决风险：新增板块事实为公开聚合叙事，详细源码与 NDA 证据仍由右侧项目隔离问答承接。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`9cd77bf4cc7bda4db8a8050f40cd49f92e74ccf7`

## 关联
- Change Request：无（U2 展示内容补齐，不改变业务行为或契约）
- 测试任务：现有 web-shell 冻结回归
