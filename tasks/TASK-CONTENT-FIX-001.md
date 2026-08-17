# TASK-CONTENT-FIX-001 修正"表数量"事实错误（11→15）

## 任务类型
- documentation

## 基线版本与基线 commit
- baseline：PRD 2.3.3 / 用例规约 1.7.2 / 领域模型 1.1.5 / SRS 1.3 / UI 线框 1.0 / 架构 0.2 / 安全 0.1 / OpenAPI 0.2 / 测试计划 0.2 / AI 治理 1.0.1（全部 approved）
- 基线 commit：`62620df`

## 精确规范引用
- 无（本次为已落地 schema 的事实性修正；不涉及规范条款变更）

## 需求来源
- 用户确认：2026-08-16 对码发现 `content.py` 与 `main.tsx` 页面二 02 文案均写"0001-0007 迁移共 11 张表"，
  而实际 7 个迁移（`migrations/versions/0001`–`0007`）通过 `op.create_table` 创建 **15 张表**
  （users / auth_sessions / appointments / appointment_slots / availability_overrides / companies /
  company_booking_exceptions / interviewer_profiles / owner_contact_configs / audit_logs /
  notification_events / conversations / conversation_messages / knowledge_documents /
  knowledge_index_versions）。真实性优先原则要求展示/服务语料与实际 schema 一致。

## 目标
- 把"11 张表"修正为"15 张表"，使页面二展示文案与"0001-0007 迁移"实际表数一致。

## 非目标
- 不改其他数字（如 LITERAL 8/8、REJECT 10/10、0.47、RRF top6、React19/Vite8 等已核实正确）。
- 不动 sleep/litchi tab 增删（存在未提交的相关改动，单独评审，见下方"关联"）。
- 不改任何规范文档、迁移、API、依赖。

## 允许修改路径
- `apps/api/app/aiqa/content.py`（jianli 技术栈 chunk 中"11 张表"→"15 张表"）
- `apps/web/main.tsx`（页面二 02 架构与选型 points 中"11 张表"→"15 张表"）

## 禁止修改路径
- 除上两处精确子串外的任何内容；迁移 / 规范 / 其他数字 / sleep/litchi 相关。

## 已批准的 DB / API / 依赖变更
- 无（纯文案事实修正，无 schema/接口/依赖变化）

## 规范影响评估
- behavior_change：false（修正已落地 schema 的错误陈述，使其符合现实；不改变用户可观察的产品行为逻辑）
- affected_specs：
  - srs：none（若 SRS/领域模型建模的表数与 15 不符，属规范漂移，需另起 Change Request 同步；本任务不处理）
  - domain_model：none
  - openapi：none
  - security：none
  - test_plan：none
- reason：Bug 修复式事实校正（served/展示内容对齐真实 schema），非引入新行为。

## 功能验收
- `content.py` 中 jianli 技术栈 chunk 出现"15 张表"且不再出现"11 张表"。
- `main.tsx` 页面二 02 points 出现"15 张表"且不再出现"11 张表"。

## 安全与隐私验收
- 无

## 性能验收
- 无

## 变更预算（change_budget）
- max_files：2
- expected_prod_lines：2（各一处子串替换）
- expected_test_lines：0

## 必须运行的测试命令
- 无（纯静态文案；不触碰测试）

## 回滚方法
- `git checkout -- apps/api/app/aiqa/content.py apps/web/main.tsx`（仅回滚本任务两处子串）

## 强制停止条件
- 若发现除"11→15"外还需改动其他事实或代码 → 停止并报告，不擅自扩大范围。

## 交付证据（任务关闭前必须填写，缺一不得关闭）
- commit / PR：本提交（HEAD，含 tasks/TASK-CONTENT-FIX-001.md）
- 修改文件清单：content.py、main.tsx（各仅"11 张表"→"15 张表"一处）
- 测试命令及结果：无（纯文案）
- lint / typecheck：无相关改动
- DB 迁移验证：无
- 验收证据：对码记录（migrations/versions 0001-0007 共 15 个 op.create_table）
- 变更预算实际值：max_files=2 / 生产行数=2 / 测试行数=0
- 未解决风险：工作树存在未提交的 content.py/models.py/main.tsx/styles.css 改动（含 sleep/litchi 增改），与本任务无关，须用户决定如何处理后再统一提交
- 是否偏离 TASK：否
- 规范影响结论：none
- spec_sync：clean（本任务不改规范）
- verified_commit：本提交（HEAD）

## 关联
- 用户 2026-08-16 23:06 明确决定**保留 sleep/litchi（展示 3 个项目）**，此前"删 sleep/litchi tab"历史计划**作废**。故工作树未提交的 sleep/litchi 改动为**有意保留**，非废弃；本任务不与之混提交。
