# TASK-UI-GLASS-001 桌面端毛玻璃视觉升级

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：14917e0c061a1b2e55dccb7471f071f10b8d7362

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` §1.1、§1.2、§1.4、§3 U1/U2/U3
- `docs/requirements/use-cases.md` UC-01、UC-02、UC-07
- 现有 `tests/web-shell/shell.test.ts` 冻结回归

## 需求来源
- 用户 2026-08-29 明确要求：为现有站点实现毛玻璃风格 UI。

## 目标
在不改变现有布局结构和业务行为的前提下，为公开页、预约页、认证弹窗与管理端统一增加高可读、可降级的毛玻璃视觉系统。

## 非目标（明确排除）
- 不改变页面信息架构、业务流程、文案、状态语义或权限。
- 不修改 API、SSE、数据库、迁移、RAG、通知与部署架构。
- 不新增 npm/pip 依赖、图片素材、字体或外部服务。
- 不迁移至其他建站或托管平台。

## 允许修改路径
- `tasks/TASK-UI-GLASS-001.md`
- `apps/web/styles.css`
- `apps/web/appointment.css`
- `tests/web-shell/shell.test.ts`（仅可新增视觉存在性断言，不得修改或放宽既有断言）

## 禁止修改路径
- `apps/api/**`
- `docs/api/**`
- `apps/web/main.tsx`
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
- reason：UI 线框明确不规定具体 hex、字体和间距；本任务只调整视觉皮肤，不改变结构、交互、状态与契约。

## 功能验收
- ≥1280×720 桌面视口中，侧栏、顶栏、内容卡片、聊天栏、预约和管理端形成一致的半透明分层。
- PDF 阅读区、表格、表单与预约状态色保持清晰可读，不因透明度降低信息辨识度。
- 不支持 `backdrop-filter` 时有不透明背景降级；减少动态效果偏好下不出现持续装饰动画。
- 现有页面与业务回归测试、typecheck、production build 全部通过。

## 安全与隐私验收
- 不改变认证、权限、加密、日志或隐私展示规则。
- 不加载远程字体、图片、脚本或样式资源。

## 性能验收
- 不新增网络请求或 JavaScript 运行时依赖。
- 仅使用有限数量固定背景光斑；不对长列表元素增加无限动画。

## 变更预算（change_budget）
- max_files：4
- expected_prod_lines：450
- expected_test_lines：20

## 必须运行的测试命令
- `npm test`
- `npm run typecheck`
- `npm run build`
- 浏览器 1440×1000 公开页视觉检查；预约/管理端可达状态检查。

## 回滚方法
- 回退本任务提交；本任务无数据迁移、缓存或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 新增依赖、API/DB/权限变更或需修改 `main.tsx` 才能完成时停止报告。
- 超过 4 个文件或冻结测试失败时停止，不修改既有断言规避失败。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：`695d1e6ecd3c2a4f16103b051ccf5c4a68f3119c`
- 修改文件清单：`apps/web/styles.css`、`apps/web/appointment.css`、`tasks/TASK-UI-GLASS-001.md`
- 测试命令及结果：`npm test` → 1 test / 1 file passed；`npm run build` → 1793 modules transformed，production build 成功
- lint / typecheck：`npm run typecheck` → 0 error；`git diff --check` → 0 error
- DB 迁移验证：无
- 验收证据：Codex 内置浏览器 1440×1000 实测：三栏均为 `blur(24px) saturate(1.38)`，PDF 保持不透明阅读面，项目/预约/认证表面可读；900×800 实测 `desktop-app=none`、`desktop-gate=flex`；控制台 0 warning / 0 error；页面无 Google Fonts 外链。
- 变更预算实际值：3 / 4 files；生产样式净新增 270 行（271 增 / 1 删）≤450；测试 0 行≤20
- 未解决风险：登录态管理端真实数据页未在本次浏览器会话完成视觉复验；本地 API `127.0.0.1:8000` 当时不可达，已验证其样式选择器、未登录认证页及 production build。
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：`695d1e6ecd3c2a4f16103b051ccf5c4a68f3119c`

## 关联
- Change Request：无（不改变用户可观察业务行为）
- 测试任务：现有 web-shell 冻结回归
