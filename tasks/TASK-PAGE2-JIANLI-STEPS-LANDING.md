# TASK-PAGE2-JIANLI-STEPS-LANDING 把 01-04 jianli 草稿落地进前端 + 两处事实校正

> 用户原话（2026-08-18）：「之前说的 01-04 的关于 jianli 的先写到前端吧我怕我忘了。」
> 即把已锁定的页面二 01-04 jianli 案例内容落地进 `apps/web/main.tsx` `projects.jianli.steps`，
> 并校正两处事实错误。纯文案，不改组件/逻辑/API。

## 任务类型
- documentation

## 基线版本与 baseline commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1
- 基线 commit：5724d87

## 目标
把已锁定的页面二 01-04 jianli 案例内容落地进 `apps/web/main.tsx` `projects.jianli.steps`，并校正两处事实：
1. **迁移表数 "11 张表" → "15 张表"**：`migrations/versions` 实际 `op.create_table` 创建 15 张（users/auth_sessions/appointments/appointment_slots/availability_overrides/companies/company_booking_exceptions/interviewer_profiles/owner_contact_configs/audit_logs/notification_events/conversations/conversation_messages/knowledge_documents/knowledge_index_versions）；content.py 旧值 11 为硬错，先前只改了 content.py 没改到前端。
2. **不传播"简历事实一致率实测 26/26 = 100%"**：`scripts/fact_consistency_results.json`（generated 2026-08-17）显示 26 题**全 503 Service Unavailable**，无任何一题真测出答案，无真实数字。改为「评测集已就绪、实测待跑、以 LITERAL 8/8 + REJECT 10/10 为代理指标、SLO ≥ 94% 为目标」。

## 非目标
- 不改组件结构 / 渲染逻辑 / API / 样式
- 不新增编造数字
- 不引入 privacy guard 之外的未验证能力声称（隐私护栏代码已实现，但不声称"已通过测试"——仅描述设计）

## 允许修改路径
- `apps/web/main.tsx`（`projects.jianli.steps` 01-04 的 summary/points 文本）
- `docs/page2-jianli-01-04-draft.md`（同步两处事实校正，消除编造表述）

## 禁止修改路径
- 任何生产逻辑、组件结构、API、样式

## 已批准的 DB / API / 依赖变更
- 无

## 规范影响评估
- behavior_change：false（纯文案）
- affected_specs：全部 none
- reason：仅展示层文本修正，不改变规范/实现。

## 变更预算
- max_files：2
- expected_prod_lines：0
- expected_test_lines：0

## 必须运行的测试命令
- 前端构建门禁仅在 WSL 可跑（沙箱缺 win32 rolldown 原生包）：
  `cd /mnt/c/Users/<user>/Desktop/jianli/apps/web && npm run build`
- 并人工核对页面二 01-04 四页渲染与右侧问答过滤正常。

## 回滚方法
- git 回退文案改动

## 交付证据
- commit / PR：48c3b6c
- 修改文件清单：apps/web/main.tsx（projects.jianli.steps 01-04）+ docs/page2-jianli-01-04-draft.md
- 测试命令及结果：用户 WSL 2026-08-18 `npm run build` 通过（✓ built in 21.70s）；纯文案无逻辑变更
- lint / typecheck：通过（同上 build，tsc -b 无错误）
- DB 迁移验证：无
- 未解决风险：事实一致率 26/26 仍为"实测待跑"，需用户起服务跑 `measure_fact_consistency.py` 后回填真实数字
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean
- verified_commit：48c3b6c
