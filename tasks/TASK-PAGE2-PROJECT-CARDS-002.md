# TASK-PAGE2-PROJECT-CARDS-002 页面二项目价值卡片收敛

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：68c13c0

## 精确规范引用（AI 只读取这些章节）
- `docs/requirements/PRD.md` §2 R1/R3/R6/R25、§3 场景 3
- `docs/requirements/use-cases.md` §UC-02
- `docs/design/ui-wireframe.md` §U2
- `docs/test/test-plan.md` TC-UI-002、TC-UI-003

## 需求来源
- 用户于 2026-08-27 明确批准：每个项目一屏仅保留项目名与定位标签、一句核心价值、一句场景/难题、三张硬证据卡和一行诚实证据边界；技术细节由右侧项目隔离问答承接。

## 目标
将页面二的四阶段长文播放改为三个项目 Tab 下的单屏价值卡片，首屏快速表达项目差异化与可验证证据。

## 非目标（明确排除）
- 不新增或修改知识库内容、推荐问题、RAG/Agent 行为。
- 不修改预约、鉴权、管理端、邮件或飞书能力。
- 不修改 API、SSE、数据库、迁移或依赖。

## 允许修改路径
- `apps/web/main.tsx`
- `apps/web/styles.css`
- `tasks/TASK-PAGE2-PROJECT-CARDS-002.md`

## 禁止修改路径
- `apps/api/**`
- `docs/requirements/**`
- `docs/api/**`
- `docs/test/test-plan.md`
- 其他业务模块与冻结验收测试

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估（spec impact，每个代码 TASK 必填）
- behavior_change：false
- affected_specs：
  - srs：none
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：现行 U2 已批准“项目卡片 + 右侧项目问答”；本任务仅将冗长的阶段播放实现收敛为已批准的卡片式信息层级，不改变能力、接口或安全边界。

## 功能验收
- 页面二仍展示 jianli、Sleep、Litchi 三个项目 Tab，切换后单屏内容同步变化。
- 每个项目仅显示定位标签、核心价值、场景难题、三张证据卡及证据边界。
- 移除阶段序号、播放/上一步/下一步控制和长要点列表。
- 右侧项目隔离问答、预约入口与正文可选择复制保持不变。
- 证据口径明确区分本地、确定性模拟和未验证边界。

## 安全与隐私验收
- 不新增个人敏感信息、密钥、外部链接或权限路径。
- 不夸大模拟、接纳层性能或未验证模型效果。

## 性能验收
- 不新增运行时请求或依赖；前端生产构建通过。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：180
- expected_test_lines：0

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`

## 回滚方法
- 回退本任务对 `apps/web/main.tsx` 与 `apps/web/styles.css` 的修改。

## 强制停止条件
- 新增 API、数据库、依赖、知识库事实或修改冻结验收测试时立即停止。
- 超过 3 个文件或冻结验收失败时立即停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`e1f0636`（页面二项目价值卡实现）
- 修改文件清单：`apps/web/main.tsx`、`apps/web/styles.css`、本任务单
- 测试命令及结果：WSL `npm test` → 1 file / 1 test passed；WSL `npm run build` → 1792 modules transformed，生产构建通过
- lint / typecheck：WSL `npm run typecheck` → exit 0
- DB 迁移验证：无
- 验收证据：本地 `http://localhost:5173/` 浏览器验收；jianli / Sleep / Litchi 三个 Tab 标题与证据边界均可见，控制台 error 为 0
- 变更预算实际值：3/3 文件；生产代码 `+119/-149` 行，未修改测试；预算内
- 未解决风险：TC-UI-003 历史文字仍只点名 jianli/sleep，但本任务按禁止路径未修改冻结验收；现有实现继续展示三个项目
- 是否偏离 TASK：否；工作区另有 `apps/api/app/aiqa/service.py`、`apps/api/app/aiqa/sse.py` 与 `tasks/TASK-AIQA-AGENT-LAB-001.md` 修改，不属于本任务且未触碰
- 规范影响结论：none
- spec_sync：clean（实现仍符合已批准 PRD R1/R3/R6/R25、UC-02 与 UI U2）
- verified_commit：`e1f0636`

## 关联
- Change Request：无需；实现收敛至已批准 U2 项目卡片交互
- 测试任务：TC-UI-002、TC-UI-003
