# TASK-WEB-NAV-LABEL-CONSISTENCY-001 顶部与侧栏导航命名统一

## 任务类型
- implementation

## 基线版本与基线 commit
- baseline：PRD 2.3.6 / 用例规约 1.7.4 / 领域模型 1.1.8
- 基线 commit：`2c5557ef4a4f7545ce9bf347d69595655ca2912b`

## 精确规范引用（AI 只读取这些章节）
- `docs/design/ui-wireframe.md` §2、§3
- `docs/requirements/SRS.md` §3.1
- 现有 `tests/web-shell/shell.test.ts` Web 展示回归

## 需求来源
- 用户 2026-08-30 基于顶部导航与左侧导航截图提出：两处名称必须一致，以左侧导航为准。

## 目标
将顶部公共导航统一为“简历问答 / 项目说明 / 预约面试 / 我的预约”，与左侧导航的页面名称、顺序和选中语义一致。

## 非目标（明确排除）
- 不改变导航顺序、页面跳转、active 判断、角色权限或 owner 专属入口。
- 不改变布局、字号、页面标题、URL、API、数据库、依赖或安全策略。

## 允许修改路径
- `tasks/TASK-WEB-NAV-LABEL-CONSISTENCY-001.md`
- `apps/web/main.tsx`
- `tests/web-shell/shell.test.ts`（仅新增/强化导航文案一致性断言）

## 禁止修改路径
- `apps/web/styles.css`
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
- reason：修正同一页面在两处导航中的显示名称不一致，使实现重新符合已批准 UI 的统一全局导航语义；不改变可执行行为。

## 功能验收
- 顶部公共导航按顺序显示“简历问答 / 项目说明 / 预约面试 / 我的预约”。
- 左侧导航文案保持不变，两处名称逐项一致。
- 点击、active 状态与页面切换行为保持不变。

## 安全与隐私验收
- 不触碰鉴权、权限或用户数据。

## 性能验收
- 仅替换静态文案，不新增请求、资源或运行时逻辑。

## 变更预算（change_budget）
- max_files：3
- expected_prod_lines：4
- expected_test_lines：8

## 必须运行的测试命令
- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `git diff --check`
- 浏览器实屏检查顶部与侧栏名称、顺序和 active 状态。

## 回滚方法
- 回退本任务提交；无数据迁移或外部状态。

## 强制停止条件（与 `AGENTS.md §2` 一致）
- 需要改变导航逻辑、角色权限、依赖、API、数据库或安全策略时停止报告。
- 超过 3 个文件、超出预算或冻结验收测试失败时停止。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：待回填
- 修改文件清单：待回填
- 测试命令及结果：待回填
- lint / typecheck：待回填
- DB 迁移验证：无
- 验收证据：待回填
- 变更预算实际值：待回填
- 未解决风险：待回填
- 是否偏离 TASK：待回填
- 规范影响结论：none
- spec_sync：待回填
- verified_commit：待回填

## 关联
- Change Request：无（既有导航一致性缺陷修复）
- 测试任务：现有 web-shell 回归
