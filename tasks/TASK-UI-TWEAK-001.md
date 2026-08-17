# TASK-UI-TWEAK-001：隐藏聊天面板滚动条

## 基线
- PRD 2.3.3 / 用例 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI线框 1.0 / architecture 0.2 / security 0.1 / openapi 0.2 / test_plan 0.2 / ai_governance 1.0.1

## 目标
用户截图反馈**中间简历区（`.main-column>.workspace`，即页面一/页面二等中间主区域）**出现默认滚动条（红框标记）。仅通过 CSS 隐藏该中间区域的滚动条视觉，不改变布局、功能或可滚动行为。

> 修正：初版误改了右侧聊天面板（`.chat-panel`），用户指出红框圈的是中间简历区；已回退聊天面板改动，改为隐藏 `.main-column>.workspace` 滚动条。

## 非目标
- 不修改任何业务逻辑、API 契约、状态或路由。
- 不引入新依赖。
- 不改右侧聊天面板、左侧 history rail 的滚动条（维持原样）。

## 允许修改路径
- `apps/web/styles.css`

## 禁止修改路径
- `apps/web/main.tsx`、`apps/web/*.tsx`、`apps/api/**`

## 已批准的 DB / API / 依赖变更
- 无

## 变更预算
- max_files: 1
- expected_prod_lines: +2（CSS 规则）

## 交付证据
- 修改文件：`apps/web/styles.css`
- 新增规则：`.main-column>.workspace{scrollbar-width:none;-ms-overflow-style:none}` 与 `.main-column>.workspace::-webkit-scrollbar{display:none}`
- 验证：本地 Git Bash 环境缺少 pnpm/tsc/rolldown 原生绑定，`pnpm build` / `vite build` 未跑通；需用户在正常前端环境执行 `pnpm build` 重建 dist。
- 是否偏离 TASK：否（已按用户纠正修正目标，回退初版错误改动）
- 未解决风险：无（纯视觉隐藏）
