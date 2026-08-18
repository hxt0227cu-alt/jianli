# TASK-PAGE2-WORDING-011 页面二 01-04 文案诚实修正（标边界，不编造）

> 承接对 DeepSeek + Kimi 评审的回应：页面人格是"真实性优先、绝不编造"，故所有文案必须
> 如实标出"已实现"与"已知缺口/规划中"。本任务仅在 `projects.jianli.steps` 与草稿做
> **文案层**修正（无行为变更），把评审戳中的边界讲清楚。

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：5c0e4cc

## 精确规范引用
- `apps/web/main.tsx` `projects.jianli.steps`
- `docs/page2-jianli-01-04-draft.md`

## 需求来源
- 外部评审（DeepSeek①②③ / Kimi①②⑥⑦⑨）+ 自查歧义

## 目标
文案修正（全部不编造，缺口如实标）：
1. **"拒答率 0%→100%" → "越界题拦截率 0%→100%（REJECT 10/10）"**，并与"误拒率待测（TASK-AIQA-FALSE-REJECT-009）"成对出现，避免读成"系统拒答一切"。
2. **评测代表性边界**：26/26 事实一致率注明"评测集与知识源同源，验证事实在场时不编造；跨分布泛化需更大对抗集（规划中）"——不写未测的"85% 泛化集"。
3. **多轮**：写"有界回填（≤6 条）+ 每轮硬性事实卡重锚"，补"未做上一轮推理隔离，长对话累计偏差防护依赖事实卡每轮重锚，非完全免疫"（锚点隔离见 TASK-AIQA-ANCHOR-ISO-008）。
4. **前端**：写"fetch 流式逐帧解析 + 打字机渲染"，把"中断控制/超时/断线重连/移动端"列为已知缺口或"已实现（TASK-FE-STREAM-CTRL-010）"——不把未实现写成已实现。
5. **新增诚实叙事**：选型理由（DeepSeek-V4-Flash + StubGateway 默认兜底）、"如果重来"反思（先建对抗评测集再写答案；事实卡比调参更治本）、差异化竞争力框架（评测先暴露缺陷 + 事实卡重锚）。

## 非目标
- 不改任何代码行为 / API / 样式
- 不引入编造数字（所有数字沿用已核实真实值）

## 允许修改路径
- `apps/web/main.tsx`（`projects.jianli.steps` 01-04 的 summary/points 文本）
- `docs/page2-jianli-01-04-draft.md`（同步修正）

## 禁止修改路径
- 任何生产逻辑、组件结构、API

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：false（纯文案）
- affected_specs：全部 none
- reason：仅展示层文本修正，不改变规范/实现。

## 功能验收
- 所有陈述与代码实际一致；缺口明确标注，无"已实现"式误述
- "拒答率"歧义消除

## 安全与隐私验收
- 不涉及

## 性能验收
- 不涉及

## 变更预算
- max_files：2
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 无（文案）；前端改动随 TASK-FE-STREAM-CTRL-010 一并构建验证

## 回滚方法
- git 回退文案改动

## 强制停止条件
- 无

## 交付证据
- commit / PR：5724d87
- 修改文件清单：apps/web/main.tsx（projects.jianli.steps 01-04）+ docs/page2-jianli-01-04-draft.md
- 测试命令及结果：无（纯文案）
- lint / typecheck：无
- DB 迁移验证：无
- 验收证据："拒答率"歧义已消除（→"越界题拦截率"）；补误拒率/多轮/选型/如果重来边界，全部不编造
- 变更预算实际值：max_files 实际 2 / 生产 0 行 / 测试 0 行
- 未解决风险：无
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：5724d87
- 关闭门禁：①②③④ 全满足
